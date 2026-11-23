from sqlalchemy import Column, Integer, String, Float, ForeignKey, Index, UniqueConstraint
from database import Base

# 1. Tabel Skala Nilai
class SkalaNilai(Base):
    __tablename__ = "skala_nilai"
    huruf = Column(String(2), primary_key=True)
    bobot = Column(Float, nullable=False)

# 2. Tabel Prerequisite
class Prerequisite(Base):
    __tablename__ = "prerequisite"
    id = Column(Integer, primary_key=True, autoincrement=True)
    kode_mk = Column(String(10), nullable=False)
    kode_mk_syarat = Column(String(10), nullable=False)
    min_huruf = Column(String(2), ForeignKey("skala_nilai.huruf"), nullable=False)

    __table_args__ = (
        Index("idx_prereq_mk_syarat", "kode_mk", "kode_mk_syarat"),
    )

# 3. Tabel KRS
class KRS(Base):
    __tablename__ = "krs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nim = Column(String(20), nullable=False, index=True)
    semester = Column(String(10), nullable=False)
    status = Column(String(20), default="DRAFT")
    total_sks = Column(Integer, default=0)

# 4. Tabel KRS Detail
class KRSDetail(Base):
    __tablename__ = "krs_detail"
    id = Column(Integer, primary_key=True, autoincrement=True)
    krs_id = Column(Integer, ForeignKey("krs.id", ondelete="CASCADE"), nullable=False)
    kode_mk = Column(String(10), nullable=False)
    nama_mk = Column(String(100), nullable=False)
    sks = Column(Integer, nullable=False)
    hari = Column(String(10), nullable=False)
    jam_mulai = Column(Integer, nullable=False)
    jam_selesai = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("krs_id", "kode_mk", name="uq_krs_mk"),
        Index("idx_krs_detail_krs_id", "krs_id"),
    )

# Tabel Pendukung: Riwayat Nilai Mahasiswa
class RiwayatNilai(Base):
    __tablename__ = "riwayat_nilai"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nim = Column(String(20), nullable=False)
    kode_mk = Column(String(10), nullable=False)
    nilai_huruf = Column(String(2), ForeignKey("skala_nilai.huruf"), nullable=False)

    __table_args__ = (
        Index("idx_riwayat_nim_mk", "nim", "kode_mk"),
    )