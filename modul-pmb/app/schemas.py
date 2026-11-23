import re
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from app.models import JalurMasukEnum, StatusPendaftaran

class PendaftaranCreate(BaseModel):
    nama_lengkap: str
    email: EmailStr
    phone: str
    tanggal_lahir: date
    alamat: str
    program_studi_id: int
    jalur_masuk: JalurMasukEnum

    @field_validator("phone")
    @classmethod
    def validate_indonesian_phone(cls, v: str) -> str:
        # Format valid: 08xxxxxxxxxx atau +628xxxxxxxxxx (10-15 digit)
        pattern = r"^(\+62|0)8[1-9][0-9]{7,11}$"
        if not re.match(pattern, v):
            raise ValueError("Format nomor HP Indonesia tidak valid (harus diawali 08 atau +628)")
        return v

class CalonMahasiswaResponse(BaseModel):
    id: int
    nim: Optional[str] = None
    nama_lengkap: str
    email: str
    phone: str
    tanggal_lahir: date
    alamat: str
    program_studi_id: int
    status: StatusPendaftaran
    created_at: datetime
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True