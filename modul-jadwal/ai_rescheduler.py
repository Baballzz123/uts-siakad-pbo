from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import Jadwal, Kelas, Ruangan
from conflict_detector import detect_schedule_conflict

def _minutes_to_hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"

class AIRescheduler:
    CANDIDATE_DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]
    CANDIDATE_SLOTS = [
        (480, 580),
        (600, 700),
        (780, 880),
        (900, 1000),
        (1020, 1120),
    ]

    @staticmethod
    def saring_saran(
        raw_candidates: List[Dict[str, Any]],
        existing_schedules: List[Dict[str, Any]],
        kapasitas_kelas: int
    ) -> List[Dict[str, Any]]:
        """Menyaring kandidat saran AI agar memenuhi kapasitas ruang dan bebas bentrok Sweep Line."""
        filtered = []
        for cand in raw_candidates:
            if cand["kapasitas_ruang"] < kapasitas_kelas:
                continue
            probe = {
                "id": -999,
                "kelas_id": cand["kelas_id"],
                "ruangan_id": cand["ruangan_id"],
                "dosen_id": cand["dosen_id"],
                "hari": cand["hari"],
                "jam_mulai": cand["jam_mulai"],
                "jam_selesai": cand["jam_selesai"],
            }
            conflicts = detect_schedule_conflict(existing_schedules + [probe])
            if not any(c["jadwal_1_id"] == -999 or c["jadwal_2_id"] == -999 for c in conflicts):
                filtered.append(cand)
        return filtered

    @classmethod
    def generate_3_alternatives(cls, db: Session, jadwal_id: int) -> Dict[str, Any]:
        target = db.query(Jadwal).filter(Jadwal.id == jadwal_id).first()
        if not target:
            raise HTTPException(status_code=404, detail=f"Jadwal ID {jadwal_id} tidak ditemukan")

        kelas = db.query(Kelas).filter(Kelas.id == target.kelas_id).first()
        durasi = target.jam_selesai - target.jam_mulai

        existing_schedules = [
            {
                "id": j.id,
                "kelas_id": j.kelas_id,
                "ruangan_id": j.ruangan_id,
                "dosen_id": j.dosen_id,
                "hari": j.hari,
                "jam_mulai": j.jam_mulai,
                "jam_selesai": j.jam_selesai,
            }
            for j in db.query(Jadwal).filter(Jadwal.id != jadwal_id).all()
        ]

        rooms = db.query(Ruangan).order_by(Ruangan.kapasitas.asc()).all()
        prioritized_days = [target.hari] + [d for d in cls.CANDIDATE_DAYS if d != target.hari]

        raw_candidates: List[Dict[str, Any]] = []
        for hari in prioritized_days:
            for start_min, _ in cls.CANDIDATE_SLOTS:
                end_min = start_min + durasi
                for room in rooms:
                    if hari == target.hari and start_min == target.jam_mulai and room.id == target.ruangan_id:
                        continue
                    raw_candidates.append({
                        "kelas_id": target.kelas_id,
                        "hari": hari,
                        "jam_mulai": start_min,
                        "jam_selesai": end_min,
                        "waktu_formatted": f"{_minutes_to_hhmm(start_min)} - {_minutes_to_hhmm(end_min)}",
                        "ruangan_id": room.id,
                        "kode_ruang": room.kode_ruang,
                        "kapasitas_ruang": room.kapasitas,
                        "dosen_id": target.dosen_id,
                    })

        valid_suggestions = cls.saring_saran(raw_candidates, existing_schedules, kelas.kapasitas_kelas)[:3]
        alternatives = []
        for idx, item in enumerate(valid_suggestions, start=1):
            score = 95 if item["hari"] == target.hari else (88 if item["ruangan_id"] == target.ruangan_id else 80)
            alternatives.append({
                "option_rank": idx,
                **item,
                "validated_by_sweep_line": True,
                "ai_confidence_score": score,
                "alasan_rekomendasi": f"Tersaring aman: bebas bentrok ruang {item['kode_ruang']} & dosen."
            })

        return {
            "jadwal_id": target.id,
            "kelas": f"{kelas.kode_kelas} - {kelas.nama_mk}",
            "total_alternatives": len(alternatives),
            "alternatives": alternatives
        }