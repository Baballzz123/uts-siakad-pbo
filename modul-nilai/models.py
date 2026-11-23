from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base


class SkalaNilai(Base):
    __tablename__ = "skala_nilai"

    huruf = Column(String(2), primary_key=True, index=True)  # A, AB, B, BC, C, D, E
    bobot = Column(Numeric(3, 2), nullable=False)            # 4.00, 3.50, dst.
    nilai_min = Column(Numeric(5, 2), nullable=False)
    nilai_max = Column(Numeric(5, 2), nullable=False)
    lulus = Column(Boolean, nullable=False, default=True)    # lulus = data (bukan hardcode huruf)


class Mahasiswa(Base):
    __tablename__ = "mahasiswa"

    nim = Column(String(20), primary_key=True, index=True)
    nama = Column(String(100), nullable=False)
    prodi = Column(String(100), nullable=False, default="Teknik Informatika")
    angkatan = Column(Integer, nullable=False, default=2025)


class MataKuliah(Base):
    __tablename__ = "mata_kuliah"

    kode_mk = Column(String(20), primary_key=True, index=True)
    nama_mk = Column(String(100), nullable=False)
    sks = Column(Integer, nullable=False)


class Kelas(Base):
    __tablename__ = "kelas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    kode_mk = Column(String(20), ForeignKey("mata_kuliah.kode_mk"), nullable=False)
    semester = Column(String(20), nullable=False)  # Contoh: "2026-1", "2026-2"
    nama_kelas = Column(String(20), nullable=False, default="A")
    dosen_id = Column(String(50), nullable=False)

    mata_kuliah = relationship("MataKuliah")


class KRS(Base):
    __tablename__ = "krs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nim = Column(String(20), ForeignKey("mahasiswa.nim"), nullable=False)
    semester = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="APPROVED")

    mahasiswa = relationship("Mahasiswa")
    details = relationship("KRSDetail", back_populates="krs")


class KRSDetail(Base):
    __tablename__ = "krs_detail"
    __table_args__ = (UniqueConstraint("krs_id", "kelas_id", name="uq_krs_kelas"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    krs_id = Column(Integer, ForeignKey("krs.id"), nullable=False)
    kelas_id = Column(Integer, ForeignKey("kelas.id"), nullable=False)
    nilai_angka = Column(Numeric(5, 2), nullable=True)
    nilai = Column(String(2), ForeignKey("skala_nilai.huruf"), nullable=True)  # FK ke skala_nilai
    updated_at = Column(DateTime, nullable=True)

    krs = relationship("KRS", back_populates="details")
    kelas = relationship("Kelas")
    skala = relationship("SkalaNilai")


class GradeHistory(Base):
    __tablename__ = "grade_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    krs_detail_id = Column(Integer, ForeignKey("krs_detail.id"), nullable=False)
    kelas_id = Column(Integer, nullable=False)
    nim = Column(String(20), nullable=False)
    nilai_lama = Column(String(2), nullable=True)
    nilai_baru = Column(String(2), nullable=False)
    nilai_angka_baru = Column(Numeric(5, 2), nullable=True)
    diubah_oleh = Column(String(50), nullable=False)
    alasan = Column(String(255), nullable=True)
    waktu_ubah = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)