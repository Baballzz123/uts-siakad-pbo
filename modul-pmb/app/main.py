from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import engine, Base, get_db, SessionLocal
from app.models import CalonMahasiswa, ProgramStudi, JalurMasuk, JalurMasukEnum, StatusPendaftaran
from app.schemas import PendaftaranCreate, CalonMahasiswaResponse
from app.services import approve_calon_mahasiswa


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Buat tabel otomatis & isi data awal Program Studi + Jalur Masuk
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(ProgramStudi).count() == 0:
        db.add_all([
            ProgramStudi(id=1, kode="001", nama="Teknik Informatika", fakultas="Fakultas Ilmu Komputer"),
            ProgramStudi(id=2, kode="002", nama="Sistem Informasi", fakultas="Fakultas Ilmu Komputer"),
        ])
        db.add_all([
            JalurMasuk(nama_jalur=JalurMasukEnum.SNBP, kuota=100),
            JalurMasuk(nama_jalur=JalurMasukEnum.SNBT, kuota=150),
            JalurMasuk(nama_jalur=JalurMasukEnum.MANDIRI, kuota=200),
        ])
        db.commit()
    db.close()
    yield


app = FastAPI(
    title="Sistem Penerimaan Mahasiswa Baru (PMB) API",
    description="REST API Modul PMB dengan Generator NIM Otomatis",
    version="1.0.0",
    lifespan=lifespan
)


# Ubah error validasi Pydantic menjadi HTTP 400 Bad Request
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": jsonable_encoder(exc.errors())},
    )


# 1. POST /api/pmb/register - Daftar calon mahasiswa
@app.post("/api/pmb/register", response_model=CalonMahasiswaResponse, status_code=status.HTTP_201_CREATED)
def register_mahasiswa(payload: PendaftaranCreate, db: Session = Depends(get_db)):
    # Cek duplicate email -> 409 Conflict
    existing_email = db.query(CalonMahasiswa).filter(CalonMahasiswa.email == payload.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email sudah terdaftar dalam sistem PMB"
        )

    # Validasi keberadaan Program Studi
    prodi = db.query(ProgramStudi).filter(ProgramStudi.id == payload.program_studi_id).first()
    if not prodi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program Studi tidak ditemukan"
        )

    jalur = db.query(JalurMasuk).filter(JalurMasuk.nama_jalur == payload.jalur_masuk).first()
    if not jalur:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jalur masuk tidak valid"
        )

    calon_baru = CalonMahasiswa(
        nama_lengkap=payload.nama_lengkap,
        email=payload.email,
        phone=payload.phone,
        tanggal_lahir=payload.tanggal_lahir,
        alamat=payload.alamat,
        program_studi_id=payload.program_studi_id,
        jalur_masuk_id=jalur.id,
        status=StatusPendaftaran.PENDING
    )
    db.add(calon_baru)
    db.commit()
    db.refresh(calon_baru)
    return calon_baru


# 2. GET /api/pmb/status/{id} - Cek status pendaftaran
@app.get("/api/pmb/status/{id}", response_model=CalonMahasiswaResponse)
def get_status_pendaftaran(id: int, db: Session = Depends(get_db)):
    calon = db.query(CalonMahasiswa).filter(CalonMahasiswa.id == id).first()
    if not calon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data pendaftar dengan ID {id} tidak ditemukan"
        )
    return calon


# 3. PUT /api/pmb/approve/{id} - Admin approve -> generate NIM
@app.put("/api/pmb/approve/{id}", response_model=CalonMahasiswaResponse)
def approve_pendaftaran(id: int, db: Session = Depends(get_db)):
    calon = db.query(CalonMahasiswa).filter(CalonMahasiswa.id == id).first()
    if not calon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data pendaftar dengan ID {id} tidak ditemukan"
        )

    if calon.status == StatusPendaftaran.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pendaftar yang sudah ditolak (rejected) tidak dapat di-approve"
        )

    hasil = approve_calon_mahasiswa(id, db)
    return hasil


# 4. GET /api/pmb/stats - Dashboard jumlah pendaftar
@app.get("/api/pmb/stats")
def get_pmb_stats(db: Session = Depends(get_db)):
    total = db.query(CalonMahasiswa).count()
    per_status = (
        db.query(CalonMahasiswa.status, func.count(CalonMahasiswa.id))
        .group_by(CalonMahasiswa.status)
        .all()
    )
    per_prodi = (
        db.query(ProgramStudi.nama, func.count(CalonMahasiswa.id))
        .join(CalonMahasiswa, ProgramStudi.id == CalonMahasiswa.program_studi_id)
        .group_by(ProgramStudi.nama)
        .all()
    )

    return {
        "total_pendaftar": total,
        "berdasarkan_status": {s.value: count for s, count in per_status},
        "berdasarkan_prodi": {nama: count for nama, count in per_prodi},
    }