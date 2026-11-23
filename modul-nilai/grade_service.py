from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session
from models import Kelas, KRS, KRSDetail, SkalaNilai, GradeHistory
from presensi_port import PresensiPort


class GradeError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class GradeService:
    """Service input dan perubahan nilai dengan validasi pengampu, presensi, dan audit trail."""

    def __init__(self, db: Session, presensi_port: PresensiPort):
        self.db = db
        self.presensi_port = presensi_port

    def is_pengampu(self, kelas_id: int, dosen_id: str) -> bool:
        kelas = self.db.query(Kelas).filter(Kelas.id == kelas_id).first()
        if not kelas:
            raise GradeError(404, f"Kelas dengan id={kelas_id} tidak ditemukan.")
        return kelas.dosen_id == dosen_id

    def konversi_angka_ke_skala(self, nilai_angka: Decimal) -> SkalaNilai:
        if nilai_angka < Decimal("0") or nilai_angka > Decimal("100"):
            raise GradeError(422, "Nilai angka harus berada pada rentang 0 sampai 100.")

        skala_list = (
            self.db.query(SkalaNilai)
            .order_by(SkalaNilai.nilai_min.desc())
            .all()
        )
        for skala in skala_list:
            if Decimal(str(skala.nilai_min)) <= nilai_angka <= Decimal(str(skala.nilai_max)):
                return skala
        raise GradeError(422, f"Skala nilai untuk angka {nilai_angka} tidak ditemukan.")

    def input_nilai(
        self,
        kelas_id: int,
        nim: str,
        dosen_id: str,
        nilai_huruf: Optional[str] = None,
        nilai_angka: Optional[Decimal] = None,
        alasan: Optional[str] = None,
    ) -> dict:
        if not self.is_pengampu(kelas_id, dosen_id):
            raise GradeError(403, f"Dosen '{dosen_id}' bukan pengampu kelas id={kelas_id}.")

        detail = (
            self.db.query(KRSDetail)
            .join(KRS, KRSDetail.krs_id == KRS.id)
            .filter(KRSDetail.kelas_id == kelas_id, KRS.nim == nim)
            .first()
        )
        if not detail:
            raise GradeError(404, f"Mahasiswa {nim} tidak terdaftar pada kelas id={kelas_id}.")

        if not self.presensi_port.memenuhi_syarat_ujian(kelas_id, nim):
            persen = self.presensi_port.get_persentase_kehadiran(kelas_id, nim)
            raise GradeError(
                422,
                f"Kehadiran mahasiswa {nim} hanya {persen}% (minimal 75.00% untuk input nilai).",
            )

        skala_dipilih: Optional[SkalaNilai] = None
        angka_simpan: Optional[Decimal] = None

        if nilai_angka is not None:
            angka_simpan = Decimal(str(nilai_angka))
            skala_dipilih = self.konversi_angka_ke_skala(angka_simpan)
            if nilai_huruf and nilai_huruf.upper() != skala_dipilih.huruf:
                raise GradeError(
                    422,
                    f"Nilai angka {angka_simpan} seharusnya huruf '{skala_dipilih.huruf}', bukan '{nilai_huruf}'.",
                )
        elif nilai_huruf is not None:
            skala_dipilih = (
                self.db.query(SkalaNilai)
                .filter(SkalaNilai.huruf == nilai_huruf.upper())
                .first()
            )
            if not skala_dipilih:
                raise GradeError(422, f"Huruf mutu '{nilai_huruf}' tidak valid di skala_nilai.")
        else:
            raise GradeError(422, "Wajib mengisi nilai_angka atau nilai_huruf.")

        nilai_lama = detail.nilai
        nilai_baru = skala_dipilih.huruf

        # Simpan perubahan nilai dan grade_history dalam transaksi yang sama
        detail.nilai = nilai_baru
        detail.nilai_angka = angka_simpan
        detail.updated_at = datetime.now(timezone.utc)

        riwayat = GradeHistory(
            krs_detail_id=detail.id,
            kelas_id=kelas_id,
            nim=nim,
            nilai_lama=nilai_lama,
            nilai_baru=nilai_baru,
            nilai_angka_baru=angka_simpan,
            diubah_oleh=dosen_id,
            alasan=alasan or ("Input nilai awal" if nilai_lama is None else "Perubahan nilai"),
        )
        self.db.add(riwayat)
        self.db.commit()
        self.db.refresh(detail)
        self.db.refresh(riwayat)

        return {
            "kelas_id": kelas_id,
            "nim": nim,
            "nilai_lama": nilai_lama,
            "nilai_baru": nilai_baru,
            "nilai_angka": str(angka_simpan) if angka_simpan is not None else None,
            "bobot": str(skala_dipilih.bobot),
            "lulus": skala_dipilih.lulus,
            "history_id": riwayat.id,
        }

    def ambil_riwayat(self, nim: Optional[str] = None, kelas_id: Optional[int] = None) -> List[GradeHistory]:
        query = self.db.query(GradeHistory).order_by(GradeHistory.id.desc())
        if nim:
            query = query.filter(GradeHistory.nim == nim)
        if kelas_id:
            query = query.filter(GradeHistory.kelas_id == kelas_id)
        return query.all()