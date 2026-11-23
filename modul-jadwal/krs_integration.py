from enum import Enum
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import KRSDetail

class Actor(str, Enum):
    SISTEM = "SISTEM"
    MAHASISWA = "MAHASISWA"
    ADMIN = "ADMIN"

class KRSInvalidator:
    @staticmethod
    def transition_status(krs_row: KRSDetail, target_status: str, actor: Actor, reason: str):
        # Aturan transisi: hanya Actor.SISTEM yang boleh memaksa transisi VALID -> REVISION
        if target_status == "REVISION" and actor != Actor.SISTEM:
            raise HTTPException(
                status_code=422,
                detail=f"Transisi ilegal: Aktor {actor.value} tidak diizinkan mengubah status ke REVISION"
            )
        # Status LOCKED tidak boleh diubah langsung ke REVISION tanpa pembukaan kunci
        if krs_row.status_krs == "LOCKED" and target_status == "REVISION":
            raise HTTPException(
                status_code=422,
                detail="Transisi ilegal: KRS berstatus LOCKED tidak dapat langsung diubah ke REVISION"
            )
        krs_row.status_krs = target_status
        krs_row.catatan = reason

    @classmethod
    def invalidate_affected_krs(cls, db: Session, kelas_id: int, reason: str, actor: Actor = Actor.SISTEM) -> int:
        affected_rows = (
            db.query(KRSDetail)
            .filter(KRSDetail.kelas_id == kelas_id, KRSDetail.status_krs == "VALID")
            .all()
        )
        for row in affected_rows:
            cls.transition_status(row, "REVISION", actor=actor, reason=reason)
        return len(affected_rows)