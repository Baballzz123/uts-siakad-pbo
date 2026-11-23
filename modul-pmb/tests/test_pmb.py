import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import ProgramStudi, JalurMasuk, JalurMasukEnum

# Gunakan SQLite in-memory khusus untuk testing
SQLALCHEMY_TEST_URL = "sqlite:///./test_pmb.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Seed data master
    db.add(ProgramStudi(id=1, kode="001", nama="Teknik Informatika", fakultas="Ilmu Komputer"))
    db.add(JalurMasuk(id=1, nama_jalur=JalurMasukEnum.SNBT, kuota=100))
    db.commit()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_register_success(client):
    payload = {
        "nama_lengkap": "Budi Santoso",
        "email": "budi@example.com",
        "phone": "081234567890",
        "tanggal_lahir": "2006-05-14",
        "alamat": "Jl. Merdeka No. 10, Bandung",
        "program_studi_id": 1,
        "jalur_masuk": "SNBT"
    }
    res = client.post("/api/pmb/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "budi@example.com"
    assert data["status"] == "pending"
    assert data["nim"] is None

def test_register_duplicate_email(client):
    payload = {
        "nama_lengkap": "Budi Santoso",
        "email": "budi@example.com",
        "phone": "081234567890",
        "tanggal_lahir": "2006-05-14",
        "alamat": "Bandung",
        "program_studi_id": 1,
        "jalur_masuk": "SNBT"
    }
    client.post("/api/pmb/register", json=payload)
    res_dup = client.post("/api/pmb/register", json=payload)
    assert res_dup.status_code == 409

def test_invalid_phone_format(client):
    payload = {
        "nama_lengkap": "Siti Aminah",
        "email": "siti@example.com",
        "phone": "021-5551234",  # Bukan format HP Indonesia 08 / +628
        "tanggal_lahir": "2006-08-20",
        "alamat": "Jakarta",
        "program_studi_id": 1,
        "jalur_masuk": "SNBT"
    }
    res = client.post("/api/pmb/register", json=payload)
    assert res.status_code == 400

def test_approve_generate_nim_sequential(client):
    tahun = datetime.now(timezone.utc).year
    
    # Daftar 2 mahasiswa
    res1 = client.post("/api/pmb/register", json={
        "nama_lengkap": "Mahasiswa Satu",
        "email": "mhs1@example.com",
        "phone": "081211112222",
        "tanggal_lahir": "2006-01-01",
        "alamat": "Surabaya",
        "program_studi_id": 1,
        "jalur_masuk": "SNBT"
    })
    res2 = client.post("/api/pmb/register", json={
        "nama_lengkap": "Mahasiswa Dua",
        "email": "mhs2@example.com",
        "phone": "+6281233334444",
        "tanggal_lahir": "2006-02-02",
        "alamat": "Malang",
        "program_studi_id": 1,
        "jalur_masuk": "SNBT"
    })

    id1 = res1.json()["id"]
    id2 = res2.json()["id"]

    # Approve kedua mahasiswa
    app1 = client.put(f"/api/pmb/approve/{id1}")
    app2 = client.put(f"/api/pmb/approve/{id2}")

    assert app1.status_code == 200
    assert app2.status_code == 200
    assert app1.json()["nim"] == f"{tahun}001-0001"
    assert app2.json()["nim"] == f"{tahun}001-0002"

def test_approve_idempotent(client):
    res = client.post("/api/pmb/register", json={
        "nama_lengkap": "Andi Wijaya",
        "email": "andi@example.com",
        "phone": "081299998888",
        "tanggal_lahir": "2006-03-10",
        "alamat": "Yogyakarta",
        "program_studi_id": 1,
        "jalur_masuk": "SNBT"
    })
    mhs_id = res.json()["id"]

    # Approve pertama dan kedua kali
    first_approve = client.put(f"/api/pmb/approve/{mhs_id}").json()
    second_approve = client.put(f"/api/pmb/approve/{mhs_id}").json()

    # NIM harus tetap sama (tidak bertambah)
    assert first_approve["nim"] == second_approve["nim"]

def test_approve_invalid_id(client):
    res = client.put("/api/pmb/approve/9999")
    assert res.status_code == 404

def test_status_and_stats_endpoint(client):
    res = client.post("/api/pmb/register", json={
        "nama_lengkap": "Rina Putri",
        "email": "rina@example.com",
        "phone": "081355556666",
        "tanggal_lahir": "2006-07-12",
        "alamat": "Semarang",
        "program_studi_id": 1,
        "jalur_masuk": "SNBT"
    })
    mhs_id = res.json()["id"]

    status_res = client.get(f"/api/pmb/status/{mhs_id}")
    assert status_res.status_code == 200
    assert status_res.json()["nama_lengkap"] == "Rina Putri"

    stats_res = client.get("/api/pmb/stats")
    assert stats_res.status_code == 200
    assert stats_res.json()["total_pendaftar"] == 1