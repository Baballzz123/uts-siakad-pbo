import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import Jadwal, KRSDetail, OutboxEvent
from krs_integration import KRSInvalidator, Actor
from seed import run_seed

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_week8_data():
    run_seed()

def test_1_ai_reschedule_3_filtered_json_alternatives():
    conflicts = client.get("/conflicts").json()["conflicts"]
    assert len(conflicts) >= 1
    conflicted_id = conflicts[0]["jadwal_2_id"]

    res = client.get(f"/api/ai-reschedule/{conflicted_id}")
    assert res.status_code == 200
    body = res.json()
    assert body["total_alternatives"] == 3
    for alt in body["alternatives"]:
        assert alt["validated_by_sweep_line"] is True

def test_2_outbox_observer_and_krs_revision_after_commit():
    db = SessionLocal()
    try:
        j1 = db.query(Jadwal).first()
        jadwal_id, kelas_id, ruangan_id, dosen_id = j1.id, j1.kelas_id, j1.ruangan_id, j1.dosen_id
    finally:
        db.close()

    res_put = client.put(f"/api/jadwal/{jadwal_id}", json={
        "kelas_id": kelas_id,
        "ruangan_id": ruangan_id,
        "dosen_id": dosen_id,
        "hari": "Sabtu",
        "jam_mulai": 780,
        "jam_selesai": 880
    })
    assert res_put.status_code == 200
    data = res_put.json()
    assert data["invalidated_krs_count"] >= 1
    assert {n["role"] for n in data["notifications_sent"]} == {"Mahasiswa", "Dosen", "Admin"}

    db = SessionLocal()
    try:
        sent_outbox = db.query(OutboxEvent).filter(OutboxEvent.status == "SENT").count()
        assert sent_outbox >= 1
    finally:
        db.close()

def test_3_krs_invalidator_illegal_transition_422():
    dummy_krs = KRSDetail(krs_id=99, nim="251636004", kode_mk="TI999", nama_mk="Test", sks=3, status_krs="VALID")
    with pytest.raises(HTTPException) as exc:
        KRSInvalidator.transition_status(dummy_krs, "REVISION", actor=Actor.MAHASISWA, reason="Uji ilegal")
    assert exc.value.status_code == 422

def test_4_export_ics_and_dashboard():
    res_ics = client.get("/api/jadwal/export.ics")
    assert res_ics.status_code == 200
    assert "BEGIN:VCALENDAR" in res_ics.text
    assert "BEGIN:VEVENT" in res_ics.text

    res_dash = client.get("/dashboard")
    assert res_dash.status_code == 200
    assert "Dashboard Conflict Resolver" in res_dash.text