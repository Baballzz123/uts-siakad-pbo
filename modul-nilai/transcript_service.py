import csv
import io
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from models import Mahasiswa
from gpa_calculator import NilaiRepo, GPACalculator, CatatanNilai


class TranscriptService:
    """Service untuk menyusun data transkrip akademik serta ekspor ke CSV dan PDF."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = NilaiRepo(db)

    def susun_transkrip(self, nim: str) -> Dict[str, Any]:
        mhs = self.db.query(Mahasiswa).filter(Mahasiswa.nim == nim).first()
        if not mhs:
            raise ValueError(f"Mahasiswa dengan NIM {nim} tidak ditemukan.")

        semua_nilai = self.repo.ambil_nilai_mahasiswa(nim)

        # Ambil nilai terbaik per kode_mk untuk transkrip akhir
        terbaik_per_mk: Dict[str, CatatanNilai] = {}
        for item in semua_nilai:
            existing = terbaik_per_mk.get(item.kode_mk)
            if existing is None or item.bobot > existing.bobot:
                terbaik_per_mk[item.kode_mk] = item

        daftar_mk = sorted(terbaik_per_mk.values(), key=lambda x: (x.semester, x.kode_mk))

        total_sks_tempuh = sum(item.sks for item in daftar_mk)
        total_sks_lulus = sum(item.sks for item in daftar_mk if item.lulus)
        total_mutu = sum((Decimal(item.sks) * item.bobot for item in daftar_mk), Decimal("0.00"))
        ipk = GPACalculator.hitung_ipk(semua_nilai)

        return {
            "nim": mhs.nim,
            "nama": mhs.nama,
            "prodi": mhs.prodi,
            "angkatan": mhs.angkatan,
            "tanggal_cetak": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "total_sks_tempuh": total_sks_tempuh,
            "total_sks_lulus": total_sks_lulus,
            "total_mutu": str(total_mutu.quantize(Decimal("0.01"))),
            "ipk": str(ipk),
            "mata_kuliah": [
                {
                    "kode_mk": item.kode_mk,
                    "nama_mk": item.nama_mk,
                    "semester": item.semester,
                    "sks": item.sks,
                    "huruf": item.huruf,
                    "bobot": str(item.bobot),
                    "mutu": str((Decimal(item.sks) * item.bobot).quantize(Decimal("0.01"))),
                    "status": "LULUS" if item.lulus else "TIDAK LULUS",
                }
                for item in daftar_mk
            ],
        }

    def export_csv(self, nim: str) -> str:
        data = self.susun_transkrip(nim)
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["TRANSKRIP AKADEMIK MAHASISWA"])
        writer.writerow(["NIM", data["nim"]])
        writer.writerow(["Nama", data["nama"]])
        writer.writerow(["Program Studi", data["prodi"]])
        writer.writerow(["Angkatan", data["angkatan"]])
        writer.writerow(["Tanggal Cetak", data["tanggal_cetak"]])
        writer.writerow([])
        writer.writerow(["Kode MK", "Nama Mata Kuliah", "Semester", "SKS", "Nilai Huruf", "Bobot", "Mutu", "Status"])

        for mk in data["mata_kuliah"]:
            writer.writerow([
                mk["kode_mk"],
                mk["nama_mk"],
                mk["semester"],
                mk["sks"],
                mk["huruf"],
                mk["bobot"],
                mk["mutu"],
                mk["status"],
            ])

        writer.writerow([])
        writer.writerow(["Total SKS Tempuh", data["total_sks_tempuh"]])
        writer.writerow(["Total SKS Lulus", data["total_sks_lulus"]])
        writer.writerow(["Total Mutu", data["total_mutu"]])
        writer.writerow(["IPK", data["ipk"]])

        return output.getvalue()

    def export_pdf(self, nim: str) -> bytes:
        """Menghasilkan file PDF 1.4 valid secara mandiri."""
        data = self.susun_transkrip(nim)

        lines: List[str] = [
            "TRANSKRIP AKADEMIK SEMENTARA",
            "==========================================================================",
            f"NIM           : {data['nim']}",
            f"Nama          : {data['nama']}",
            f"Program Studi : {data['prodi']} (Angkatan {data['angkatan']})",
            f"Tanggal Cetak : {data['tanggal_cetak']}",
            "--------------------------------------------------------------------------",
            "KODE   | MATA KULIAH                      | SKS | NILAI | BOBOT | STATUS",
            "--------------------------------------------------------------------------",
        ]

        for mk in data["mata_kuliah"]:
            nama_pendek = mk["nama_mk"][:32].ljust(32)
            kode_pad = mk["kode_mk"].ljust(6)
            sks_pad = str(mk["sks"]).rjust(3)
            huruf_pad = mk["huruf"].ljust(5)
            bobot_pad = mk["bobot"].rjust(5)
            lines.append(
                f"{kode_pad} | {nama_pendek} | {sks_pad} | {huruf_pad} | {bobot_pad} | {mk['status']}"
            )

        lines.extend([
            "--------------------------------------------------------------------------",
            f"Total SKS Tempuh : {data['total_sks_tempuh']} SKS",
            f"Total SKS Lulus  : {data['total_sks_lulus']} SKS",
            f"Total Mutu       : {data['total_mutu']}",
            f"IPK Akhir        : {data['ipk']}",
            "==========================================================================",
        ])

        def _escape_pdf_text(text: str) -> str:
            return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

        content_ops = ["BT", "/F1 9 Tf", "40 780 Td", "13 TL"]
        for idx, line in enumerate(lines):
            escaped = _escape_pdf_text(line)
            if idx == 0:
                content_ops.append(f"({escaped}) Tj")
            else:
                content_ops.append(f"T* ({escaped}) Tj")
        content_ops.append("ET")
        stream_bytes = "\n".join(content_ops).encode("latin-1", errors="replace")

        objects = [
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
            f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii") + stream_bytes + b"\nendstream\nendobj\n",
            b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj\n",
        ]

        pdf = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for obj in objects:
            offsets.append(len(pdf))
            pdf.extend(obj)

        xref_start = len(pdf)
        pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        pdf.extend(b"0000000000 65535 f \n")
        for off in offsets[1:]:
            pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))

        pdf.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("ascii")
        )
        return bytes(pdf)