from sqlalchemy.orm import Session
from models import KRS, KRSDetail
from repository import KRSRepository
from validators import build_chain

class KRSManager:
    def __init__(self, db: Session):
        self.db = db
        self.repo = KRSRepository(db)
        self.validator_chain = build_chain()

    def validate_krs(self, krs: KRS, existing_details: list, new_course: dict) -> list[str]:
        context = {
            "nim": krs.nim,
            "existing_details": existing_details,
            "new_course": new_course,
            "repo": self.repo,
            "max_sks": 24,
        }
        return self.validator_chain.validate(context)

    def add_course(self, krs_id: int, new_course: dict) -> dict:
        # Row lock pada baris KRS untuk mencegah race condition
        krs = self.db.query(KRS).filter(KRS.id == krs_id).with_for_update().first()
        if not krs:
            raise ValueError("Data KRS tidak ditemukan.")

        existing_details = self.db.query(KRSDetail).filter(KRSDetail.krs_id == krs_id).all()
        errors = self.validate_krs(krs, existing_details, new_course)

        if errors:
            self.db.rollback()
            return {"status": "error", "errors": errors}

        detail = KRSDetail(krs_id=krs.id, **new_course)
        self.db.add(detail)
        krs.total_sks += new_course["sks"]
        self.db.commit()
        return {"status": "success", "total_sks": krs.total_sks}

    def remove_course(self, krs_id: int, kode_mk: str) -> dict:
        # Row lock saat menghapus mata kuliah dari KRS
        krs = self.db.query(KRS).filter(KRS.id == krs_id).with_for_update().first()
        if not krs:
            raise ValueError("Data KRS tidak ditemukan.")

        detail = (
            self.db.query(KRSDetail)
            .filter(KRSDetail.krs_id == krs_id, KRSDetail.kode_mk == kode_mk)
            .first()
        )
        if not detail:
            self.db.rollback()
            raise ValueError(f"Mata kuliah {kode_mk} tidak ditemukan di KRS.")

        krs.total_sks -= detail.sks
        self.db.delete(detail)
        self.db.commit()
        return {"status": "success", "total_sks": krs.total_sks}