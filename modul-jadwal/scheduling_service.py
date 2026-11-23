import uuid
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from models import Jadwal, Kelas, Ruangan, Dosen
from conflict_detector import detect_schedule_conflict
from observer import OutboxDispatcher
from krs_integration import KRSInvalidator, Actor

def _serialize_jadwal(j: Jadwal) -> dict:
    return {
        "id": j.id,
        "kelas_id": j.kelas_id,
        "ruangan_id": j.ruangan_id,
        "dosen_id": j.dosen_id,
        "hari": j.hari,
        "jam_mulai": j.jam_mulai,
        "jam_selesai": j.jam_selesai,
    }

class SchedulingService:
    @staticmethod
    def _validate_and_check_conflicts(
        db: Session,
        kelas_id: int,
        ruangan_id: int,
        dosen_id: int,
        hari: str,
        jam_mulai: int,
        jam_selesai: int,
        exclude_jadwal_id: int | None = None
    ):
        if jam_mulai >= jam_selesai:
            raise HTTPException(status_code=422, detail="jam_mulai harus lebih kecil dari jam_selesai")

        kelas = db.query(Kelas).filter(Kelas.id == kelas_id).first()
        if not kelas:
            raise HTTPException(status_code=404, detail=f"Kelas ID {kelas_id} tidak ditemukan")

        ruangan = db.query(Ruangan).filter(Ruangan.id == ruangan_id).first()
        if not ruangan:
            raise HTTPException(status_code=404, detail=f"Ruangan ID {ruangan_id} tidak ditemukan")

        dosen = db.query(Dosen).filter(Dosen.id == dosen_id).first()
        if not dosen:
            raise HTTPException(status_code=404, detail=f"Dosen ID {dosen_id} tidak ditemukan")

        if kelas.kapasitas_kelas > ruangan.kapasitas:
            raise HTTPException(
                status_code=422,
                detail=f"Kapasitas kelas ({kelas.kapasitas_kelas}) melebihi kapasitas ruangan {ruangan.kode_ruang} ({ruangan.kapasitas})"
            )

        existing = db.query(Jadwal).filter(Jadwal.hari == hari).with_for_update().all()
        candidate_list = [
            _serialize_jadwal(item)
            for item in existing
            if exclude_jadwal_id is None or item.id != exclude_jadwal_id
        ]
        candidate_list.append({
            "id": -1,
            "kelas_id": kelas_id,
            "ruangan_id": ruangan_id,
            "dosen_id": dosen_id,
            "hari": hari,
            "jam_mulai": jam_mulai,
            "jam_selesai": jam_selesai,
        })

        conflicts = detect_schedule_conflict(candidate_list)
        new_conflicts = [c for c in conflicts if c["jadwal_1_id"] == -1 or c["jadwal_2_id"] == -1]
        if new_conflicts:
            raise HTTPException(
                status_code=409,
                detail={"message": "Jadwal bentrok dengan jadwal yang sudah ada", "conflicts": new_conflicts}
            )
        return kelas

    @staticmethod
    def create_jadwal(db: Session, payload: dict) -> Jadwal:
        db.execute(text("SELECT 1"))
        SchedulingService._validate_and_check_conflicts(
            db=db,
            kelas_id=payload["kelas_id"],
            ruangan_id=payload["ruangan_id"],
            dosen_id=payload["dosen_id"],
            hari=payload["hari"],
            jam_mulai=payload["jam_mulai"],
            jam_selesai=payload["jam_selesai"],
        )
        new_jadwal = Jadwal(**payload)
        db.add(new_jadwal)
        db.commit()
        db.refresh(new_jadwal)
        return new_jadwal

    @staticmethod
    def update_jadwal(db: Session, jadwal_id: int, payload: dict) -> dict:
        jadwal = db.query(Jadwal).filter(Jadwal.id == jadwal_id).with_for_update().first()
        if not jadwal:
            raise HTTPException(status_code=404, detail=f"Jadwal ID {jadwal_id} tidak ditemukan")

        kelas = SchedulingService._validate_and_check_conflicts(
            db=db,
            kelas_id=payload["kelas_id"],
            ruangan_id=payload["ruangan_id"],
            dosen_id=payload["dosen_id"],
            hari=payload["hari"],
            jam_mulai=payload["jam_mulai"],
            jam_selesai=payload["jam_selesai"],
            exclude_jadwal_id=jadwal_id,
        )

        old_info = f"{jadwal.hari} ({jadwal.jam_mulai}-{jadwal.jam_selesai}) Ruang {jadwal.ruangan_id}"
        for key, val in payload.items():
            setattr(jadwal, key, val)
        new_info = f"{jadwal.hari} ({jadwal.jam_mulai}-{jadwal.jam_selesai}) Ruang {jadwal.ruangan_id}"

        invalidated_count = KRSInvalidator.invalidate_affected_krs(
            db=db,
            kelas_id=jadwal.kelas_id,
            reason=f"Jadwal {kelas.kode_kelas} berubah [{old_info}] -> [{new_info}]",
            actor=Actor.SISTEM
        )

        OutboxDispatcher.enqueue(
            db=db,
            idempotency_key=f"upd-{jadwal.id}-{uuid.uuid4().hex[:8]}",
            event_type="SCHEDULE_UPDATED",
            event_data={
                "event_type": "SCHEDULE_UPDATED",
                "jadwal_id": jadwal.id,
                "kode_kelas": kelas.kode_kelas,
                "nama_mk": kelas.nama_mk,
                "dosen_id": jadwal.dosen_id,
                "detail": f"{old_info} -> {new_info}"
            }
        )

        # Commit transaksi utama dulu, BARU dispatch Outbox!
        db.commit()
        db.refresh(jadwal)
        notifications = OutboxDispatcher.dispatch_pending(db)

        return {
            "jadwal": jadwal,
            "invalidated_krs_count": invalidated_count,
            "notifications_sent": notifications
        }

    @staticmethod
    def delete_jadwal(db: Session, jadwal_id: int) -> dict:
        jadwal = db.query(Jadwal).filter(Jadwal.id == jadwal_id).with_for_update().first()
        if not jadwal:
            raise HTTPException(status_code=404, detail=f"Jadwal ID {jadwal_id} tidak ditemukan")

        kelas = db.query(Kelas).filter(Kelas.id == jadwal.kelas_id).first()
        kode_kelas = kelas.kode_kelas if kelas else f"KELAS-{jadwal.kelas_id}"
        nama_mk = kelas.nama_mk if kelas else "Mata Kuliah"
        detail_str = f"{jadwal.hari} ({jadwal.jam_mulai}-{jadwal.jam_selesai})"

        invalidated_count = KRSInvalidator.invalidate_affected_krs(
            db=db,
            kelas_id=jadwal.kelas_id,
            reason=f"Jadwal {kode_kelas} ({detail_str}) dihapus",
            actor=Actor.SISTEM
        )

        OutboxDispatcher.enqueue(
            db=db,
            idempotency_key=f"del-{jadwal.id}-{uuid.uuid4().hex[:8]}",
            event_type="SCHEDULE_DELETED",
            event_data={
                "event_type": "SCHEDULE_DELETED",
                "jadwal_id": jadwal.id,
                "kode_kelas": kode_kelas,
                "nama_mk": nama_mk,
                "dosen_id": jadwal.dosen_id,
                "detail": f"Jadwal {detail_str} dihapus"
            }
        )

        db.delete(jadwal)
        db.commit()
        notifications = OutboxDispatcher.dispatch_pending(db)

        return {
            "invalidated_krs_count": invalidated_count,
            "notifications_sent": notifications
        }

    @staticmethod
    def get_all_conflicts(db: Session) -> list[dict]:
        all_schedules = [_serialize_jadwal(j) for j in db.query(Jadwal).all()]
        return detect_schedule_conflict(all_schedules)