import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models import NotificationLog, OutboxEvent

class ScheduleObserver(ABC):
    @abstractmethod
    def update(self, db: Session, event_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

class MahasiswaObserver(ScheduleObserver):
    def update(self, db: Session, event_data: Dict[str, Any]) -> Dict[str, Any]:
        msg = (
            f"[PUSH Mahasiswa] Jadwal {event_data['kode_kelas']} ({event_data['nama_mk']}) "
            f"berubah ({event_data['event_type']}): {event_data['detail']}. Status KRS -> REVISION."
        )
        db.add(NotificationLog(
            recipient_role="Mahasiswa",
            recipient_target=f"Mahasiswa {event_data['kode_kelas']}",
            channel="PUSH",
            event_type=event_data["event_type"],
            message=msg
        ))
        return {"role": "Mahasiswa", "channel": "PUSH", "message": msg}

class DosenObserver(ScheduleObserver):
    def update(self, db: Session, event_data: Dict[str, Any]) -> Dict[str, Any]:
        msg = (
            f"[SMS Dosen] Yth. Dosen ID {event_data['dosen_id']}, jadwal {event_data['kode_kelas']} "
            f"diperbarui ({event_data['event_type']}): {event_data['detail']}."
        )
        db.add(NotificationLog(
            recipient_role="Dosen",
            recipient_target=f"Dosen ID {event_data['dosen_id']}",
            channel="SMS",
            event_type=event_data["event_type"],
            message=msg
        ))
        return {"role": "Dosen", "channel": "SMS", "message": msg}

class AdminObserver(ScheduleObserver):
    def update(self, db: Session, event_data: Dict[str, Any]) -> Dict[str, Any]:
        msg = (
            f"[EMAIL Admin] Audit {event_data['event_type']} Jadwal #{event_data['jadwal_id']} "
            f"({event_data['kode_kelas']}): {event_data['detail']}."
        )
        db.add(NotificationLog(
            recipient_role="Admin",
            recipient_target="admin-akademik@istn.ac.id",
            channel="EMAIL",
            event_type=event_data["event_type"],
            message=msg
        ))
        return {"role": "Admin", "channel": "EMAIL", "message": msg}

class ScheduleSubject:
    def __init__(self):
        self._observers: List[ScheduleObserver] = []

    def attach(self, observer: ScheduleObserver):
        self._observers.append(observer)

    def notify(self, db: Session, event_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        for observer in self._observers:
            try:
                results.append(observer.update(db, event_data))
            except Exception as exc:
                results.append({"role": observer.__class__.__name__, "error": str(exc)})
        return results

def create_default_subject() -> ScheduleSubject:
    subject = ScheduleSubject()
    subject.attach(MahasiswaObserver())
    subject.attach(DosenObserver())
    subject.attach(AdminObserver())
    return subject

class OutboxDispatcher:
    @staticmethod
    def enqueue(db: Session, idempotency_key: str, event_type: str, event_data: Dict[str, Any]) -> OutboxEvent:
        existing = db.query(OutboxEvent).filter(OutboxEvent.idempotency_key == idempotency_key).first()
        if existing:
            return existing
        outbox = OutboxEvent(
            idempotency_key=idempotency_key,
            event_type=event_type,
            payload_json=json.dumps(event_data),
            status="PENDING"
        )
        db.add(outbox)
        return outbox

    @staticmethod
    def dispatch_pending(db: Session) -> List[Dict[str, Any]]:
        """Dieksekusi SETELAH transaksi utama jadwal di-commit."""
        pending_events = db.query(OutboxEvent).filter(OutboxEvent.status == "PENDING").all()
        subject = create_default_subject()
        dispatched_logs: List[Dict[str, Any]] = []
        for ev in pending_events:
            data = json.loads(ev.payload_json)
            sent = subject.notify(db, data)
            ev.status = "SENT"
            dispatched_logs.extend(sent)
        if pending_events:
            db.commit()
        return dispatched_logs