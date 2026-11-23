from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, List, Optional
from sqlalchemy.orm import Session
from models import KRS, KRSDetail, Kelas, MataKuliah, SkalaNilai


@dataclass(frozen=True)
class CatatanNilai:
    kode_mk: str
    nama_mk: str
    semester: str
    sks: int
    huruf: str
    bobot: Decimal
    lulus: bool


class NilaiRepo:
    """Repository untuk mengambil data nilai mahasiswa dari database."""

    def __init__(self, db: Session):
        self.db = db

    def ambil_nilai_mahasiswa(self, nim: str, semester: Optional[str] = None) -> List[CatatanNilai]:
        query = (
            self.db.query(KRSDetail, KRS, Kelas, MataKuliah, SkalaNilai)
            .join(KRS, KRSDetail.krs_id == KRS.id)
            .join(Kelas, KRSDetail.kelas_id == Kelas.id)
            .join(MataKuliah, Kelas.kode_mk == MataKuliah.kode_mk)
            .join(SkalaNilai, KRSDetail.nilai == SkalaNilai.huruf)
            .filter(KRS.nim == nim, KRSDetail.nilai.isnot(None))
        )
        if semester is not None:
            query = query.filter(KRS.semester == semester)

        hasil: List[CatatanNilai] = []
        for detail, krs, kelas, mk, skala in query.all():
            hasil.append(
                CatatanNilai(
                    kode_mk=mk.kode_mk,
                    nama_mk=mk.nama_mk,
                    semester=krs.semester,
                    sks=int(mk.sks),
                    huruf=skala.huruf,
                    bobot=Decimal(str(skala.bobot)),
                    lulus=bool(skala.lulus),
                )
            )
        return hasil


class GPACalculator:
    """Kalkulator IPS & IPK dengan Decimal, ROUND_HALF_UP sekali, dan nilai terbaik per kode_mk."""

    @staticmethod
    def _bulatkan_ip(nilai: Decimal) -> Decimal:
        return nilai.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def hitung_ips(cls, daftar_nilai: Iterable[CatatanNilai], semester: str) -> Decimal:
        total_sks = 0
        total_mutu = Decimal("0")

        for item in daftar_nilai:
            if item.semester != semester:
                continue
            if item.sks <= 0:
                continue
            total_sks += item.sks
            total_mutu += Decimal(item.sks) * item.bobot

        if total_sks == 0:
            return Decimal("0.00")

        ip_mentah = total_mutu / Decimal(total_sks)
        return cls._bulatkan_ip(ip_mentah)

    @classmethod
    def hitung_ipk(cls, daftar_nilai: Iterable[CatatanNilai]) -> Decimal:
        terbaik_per_mk: dict[str, CatatanNilai] = {}

        for item in daftar_nilai:
            if item.sks <= 0:
                continue
            existing = terbaik_per_mk.get(item.kode_mk)
            if existing is None or item.bobot > existing.bobot:
                terbaik_per_mk[item.kode_mk] = item

        total_sks = 0
        total_mutu = Decimal("0")
        for item in terbaik_per_mk.values():
            total_sks += item.sks
            total_mutu += Decimal(item.sks) * item.bobot

        if total_sks == 0:
            return Decimal("0.00")

        ipk_mentah = total_mutu / Decimal(total_sks)
        return cls._bulatkan_ip(ipk_mentah)