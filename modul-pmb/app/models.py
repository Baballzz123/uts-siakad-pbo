import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Date, DateTime, ForeignKey,
    Enum as SqlEnum, CheckConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base

class StatusPendaftaran(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class JalurMasukEnum(str, enum.Enum):
    SNBP = "SNBP"
    SNBT = "SNBT"
    MANDIRI = "Mandiri"

class ProgramStudi(Base):
    __tablename__ = "program_studi"

    id = Column(Integer, primary_key=True, index=True)
    kode = Column(String(3), unique=True, nullable=False)  # 3 karakter, misal: '001'[cite: 1, 2]
    nama = Column(String(100), nullable=False)
    fakultas = Column(String(100), nullable=False)

    pendaftar = relationship("CalonMahasiswa", back_populates="program_studi")

class JalurMasuk(Base):
    __tablename__ = "jalur_masuk"

    id = Column(Integer, primary_key=True, index=True)
    nama_jalur = Column(SqlEnum(JalurMasukEnum), unique=True, nullable=False)
    kuota = Column(Integer, default=100)

    pendaftar = relationship("CalonMahasiswa", back_populates="jalur_rel")

class CalonMahasiswa(Base):
    __tablename__ = "calon_mahasiswa"

    id = Column(Integer, primary_key=True, index=True)
    nim = Column(String(12), unique=True, nullable=True, index=True)
    nama_lengkap = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)  # Unique email[cite: 1, 2]
    phone = Column(String(20), nullable=False)
    tanggal_lahir = Column(Date, nullable=False)
    alamat = Column(String(255), nullable=False)
    
    program_studi_id = Column(Integer, ForeignKey("program_studi.id"), nullable=False)
    jalur_masuk_id = Column(Integer, ForeignKey("jalur_masuk.id"), nullable=False)
    
    status = Column(
        SqlEnum(StatusPendaftaran),
        default=StatusPendaftaran.PENDING,
        nullable=False
    )
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    approved_at = Column(DateTime, nullable=True)

    program_studi = relationship("ProgramStudi", back_populates="pendaftar")
    jalur_rel = relationship("JalurMasuk", back_populates="pendaftar")

    # Constraint tingkat database untuk format HP Indonesia & Email[cite: 1, 2]
    __table_args__ = (
        CheckConstraint("phone LIKE '08%' OR phone LIKE '+628%'", name="check_phone_id"),
        CheckConstraint("email LIKE '%_@__%.__%'", name="check_email_format"),
    )