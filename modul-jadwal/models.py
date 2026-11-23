from sqlalchemy import Column, Integer, String, ForeignKey, Index, DateTime
from datetime import datetime, timezone
from database import Base

class Ruangan(Base):
    __tablename__ = "ruangan"
    id = Column(Integer, primary_key=True, autoincrement=True)
    kode_ruang = Column(String(20), unique=True, nullable=False)
    nama_ruang = Column(String(100), nullable=False)
    kapasitas = Column(Integer, nullable=False)

class Dosen(Base):
    __tablename__ = "dosen"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nidn = Column(String(20), unique=True, nullable=False)
    nama_dosen = Column(String(100), nullable=False)

class Kelas(Base):
    __tablename__ = "kelas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    kode_kelas = Column(String(20), unique=True, nullable=False)
    kode_mk = Column(String(10), nullable=False)
    nama_mk = Column(String(100), nullable=False)
    kapasitas_kelas = Column(Integer, nullable=False)
    dosen_id = Column(Integer, ForeignKey("dosen.id"), nullable=False)

class Jadwal(Base):
    __tablename__ = "jadwal"
    id = Column(Integer, primary_key=True, autoincrement=True)
    kelas_id = Column(Integer, ForeignKey("kelas.id", ondelete="CASCADE"), nullable=False)
    ruangan_id = Column(Integer, ForeignKey("ruangan.id"), nullable=False)
    dosen_id = Column(Integer, ForeignKey("dosen.id"), nullable=False)
    hari = Column(String(10), nullable=False)
    jam_mulai = Column(Integer, nullable=False)
    jam_selesai = Column(Integer, nullable=False)

    __table_args__ = (
        Index("idx_jadwal_hari_ruang", "hari", "ruangan_id"),
        Index("idx_jadwal_hari_dosen", "hari", "dosen_id"),
    )

class KRSDetail(Base):
    __tablename__ = "krs_detail"
    id = Column(Integer, primary_key=True, autoincrement=True)
    krs_id = Column(Integer, nullable=False)
    nim = Column(String(20), nullable=False, default="251636004")
    kelas_id = Column(Integer, ForeignKey("kelas.id"), nullable=True)
    kode_mk = Column(String(10), nullable=False)
    nama_mk = Column(String(100), nullable=False)
    sks = Column(Integer, nullable=False)
    status_krs = Column(String(40), nullable=False, default="VALID")  # VALID | REVISION | LOCKED
    catatan = Column(String(255), nullable=True)

class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    idempotency_key = Column(String(100), unique=True, nullable=False)
    event_type = Column(String(50), nullable=False)
    payload_json = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING | SENT
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class NotificationLog(Base):
    __tablename__ = "notification_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient_role = Column(String(30), nullable=False)
    recipient_target = Column(String(100), nullable=False)
    channel = Column(String(20), nullable=False)
    event_type = Column(String(50), nullable=False)
    message = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))