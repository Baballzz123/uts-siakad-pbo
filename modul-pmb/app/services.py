import threading
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import CalonMahasiswa, ProgramStudi, StatusPendaftaran

# Mutex lock untuk mencegah race condition pada level aplikasi/SQLite
_nim_lock = threading.Lock()

def generate_nim(tahun: int, kode_prodi: str, db: Session) -> str:
    """
    Generate NIM format: YYYY[KODE]-XXXX (Contoh: 2025001-0001)[cite: 1, 2]
    Thread-safe menggunakan lock dan query urutan terakhir.
    """
    prefix = f"{tahun}{kode_prodi}-"
    
    # Cari NIM terakhir dengan prefix tahun & kode prodi yang sama
    # Pada PostgreSQL/MySQL bisa ditambahkan .with_for_update() untuk row-level locking
    last_student = (
        db.query(CalonMahasiswa)
        .filter(CalonMahasiswa.nim.like(f"{prefix}%"))
        .order_by(CalonMahasiswa.nim.desc())
        .with_for_update()
        .first()
    )

    if last_student and last_student.nim:
        last_number = int(last_student.nim.split("-")[1])
        next_number = last_number + 1
    else:
        next_number = 1

    return f"{prefix}{next_number:04d}"

def approve_calon_mahasiswa(calon_id: int, db: Session) -> CalonMahasiswa:
    with _nim_lock:
        calon = db.query(CalonMahasiswa).filter(CalonMahasiswa.id == calon_id).first()
        if not calon:
            return None

        # Sifat Idempotent: Jika sudah approved dan punya NIM, langsung kembalikan data tanpa generate ulang
        if calon.status == StatusPendaftaran.APPROVED and calon.nim:
            return calon

        prodi = db.query(ProgramStudi).filter(ProgramStudi.id == calon.program_studi_id).first()
        tahun_sekarang = datetime.now(timezone.utc).year
        
        calon.nim = generate_nim(tahun_sekarang, prodi.kode, db)
        calon.status = StatusPendaftaran.APPROVED
        calon.approved_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(calon)
        return calon