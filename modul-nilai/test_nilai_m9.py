from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings, strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app, get_presensi_port
from models import GradeHistory
from presensi_port import PresensiStub
from gpa_calculator import CatatanNilai, GPACalculator
from seed import seed_database


@pytest.fixture()
def test_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    seed_database(db)

    stub = PresensiStub(
        data_presensi={(1, "251636005"): Decimal("60.00")},
        default_persen=Decimal("90.00"),
    )

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_presensi_port] = lambda: stub

    with TestClient(app) as client:
        yield client, db, stub

    app.dependency_overrides.clear()
    db.close()


# --- 1. 12 Kasus pytest.mark.parametrize (Melebihi syarat minimal 10+ kasus) ---
@pytest.mark.parametrize(
    "kelas_id,nim,dosen_id,nilai_angka,nilai_huruf,expected_status,expected_huruf",
    [
        (1, "251636004", "DSN01", 92.0, None, 200, "A"),          # 1. Konversi angka -> A
        (1, "251636004", "DSN01", 82.5, None, 200, "AB"),         # 2. Konversi angka -> AB
        (1, "251636004", "DSN01", 75.0, None, 200, "B"),          # 3. Konversi angka -> B
        (1, "251636004", "DSN01", 67.0, None, 200, "BC"),         # 4. Konversi angka -> BC
        (1, "251636004", "DSN01", 58.0, None, 200, "C"),          # 5. Konversi angka -> C
        (2, "251636004", "DSN01", 45.0, None, 200, "D"),          # 6. Nilai D (tidak lulus)
        (2, "251636004", "DSN01", 20.0, None, 200, "E"),          # 7. Nilai E (tidak lulus)
        (3, "251636004", "DSN02", None, "A", 200, "A"),           # 8. Input langsung huruf A
        (1, "251636004", "DSN99", 90.0, None, 403, None),         # 9. Ditolak: bukan dosen pengampu
        (1, "251636005", "DSN01", 88.0, None, 422, None),         # 10. Ditolak: presensi < 75%
        (1, "251636004", "DSN01", None, "Z", 422, None),          # 11. Ditolak: huruf mutu tidak valid
        (999, "251636004", "DSN01", 85.0, None, 404, None),       # 12. Ditolak: kelas tidak ditemukan
    ],
)
def test_put_nilai_parametrize(
    test_client, kelas_id, nim, dosen_id, nilai_angka, nilai_huruf, expected_status, expected_huruf
):
    client, db, _ = test_client
    payload = {"dosen_id": dosen_id, "alasan": "Uji parametrize"}
    if nilai_angka is not None:
        payload["nilai_angka"] = nilai_angka
    if nilai_huruf is not None:
        payload["nilai_huruf"] = nilai_huruf

    res = client.put(f"/api/kelas/{kelas_id}/nilai/{nim}", json=payload)
    assert res.status_code == expected_status

    if expected_status == 200:
        body = res.json()["data"]
        assert body["nilai_baru"] == expected_huruf
        history = db.query(GradeHistory).filter(GradeHistory.id == body["history_id"]).first()
        assert history is not None
        assert history.nilai_baru == expected_huruf


def test_ipk_nilai_terbaik_per_kode_mk_dan_grade_history(test_client):
    client, _, _ = test_client
    client.put("/api/kelas/1/nilai/251636004", json={"dosen_id": "DSN01", "nilai_huruf": "A"})
    client.put("/api/kelas/2/nilai/251636004", json={"dosen_id": "DSN01", "nilai_huruf": "D"})
    client.put("/api/kelas/3/nilai/251636004", json={"dosen_id": "DSN02", "nilai_huruf": "B"})
    client.put("/api/kelas/4/nilai/251636004", json={"dosen_id": "DSN01", "nilai_huruf": "A"})

    res = client.get("/api/mahasiswa/251636004/ip")
    assert res.status_code == 200
    data = res.json()
    assert data["ips_per_semester"]["2026-1"] == "2.70"
    assert data["ips_per_semester"]["2026-2"] == "4.00"
    assert data["ipk"] == "3.60"


# --- 2. 3 Properti Hypothesis (Sesuai syarat slide Minggu 9) ---
bobot_strategy = st.sampled_from(
    [Decimal("0.00"), Decimal("1.00"), Decimal("2.00"), Decimal("2.50"), Decimal("3.00"), Decimal("3.50"), Decimal("4.00")]
)
sks_strategy = st.integers(min_value=1, max_value=6)


@given(st.lists(st.tuples(st.text(min_size=3, max_size=6), sks_strategy, bobot_strategy), min_size=1, max_size=10))
@settings(max_examples=50)
def test_hypothesis_ipk_dalam_rentang_valid(items):
    catatan = [
        CatatanNilai(
            kode_mk=kode,
            nama_mk=f"MK {kode}",
            semester="2026-1",
            sks=sks,
            huruf="A",
            bobot=bobot,
            lulus=bobot >= Decimal("2.00"),
        )
        for kode, sks, bobot in items
    ]
    ipk = GPACalculator.hitung_ipk(catatan)
    assert Decimal("0.00") <= ipk <= Decimal("4.00")
    assert ipk == ipk.quantize(Decimal("0.01"))


@given(sks=sks_strategy, bobot_awal=bobot_strategy, bobot_ulang=bobot_strategy)
@settings(max_examples=50)
def test_hypothesis_mengulang_tidak_menurunkan_ipk(sks, bobot_awal, bobot_ulang):
    awal = [CatatanNilai("IF201", "PBO", "2026-1", sks, "C", bobot_awal, True)]
    sesudah = awal + [CatatanNilai("IF201", "PBO", "2026-2", sks, "A", bobot_ulang, True)]
    assert GPACalculator.hitung_ipk(sesudah) >= GPACalculator.hitung_ipk(awal)


@given(bobot=bobot_strategy, daftar_sks=st.lists(sks_strategy, min_size=1, max_size=8))
@settings(max_examples=50)
def test_hypothesis_bobot_seragam_menghasilkan_ip_sama(bobot, daftar_sks):
    catatan = [
        CatatanNilai(f"MK{idx}", f"Matkul {idx}", "2026-1", sks, "B", bobot, True)
        for idx, sks in enumerate(daftar_sks)
    ]
    assert GPACalculator.hitung_ips(catatan, "2026-1") == bobot
    assert GPACalculator.hitung_ipk(catatan) == bobot