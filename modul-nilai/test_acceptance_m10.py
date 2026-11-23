import csv
import io
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app, get_presensi_port
from presensi_port import PresensiStub
from seed import seed_database


@pytest.fixture()
def e2e_client():
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
        default_persen=Decimal("92.00"),
    )

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_presensi_port] = lambda: stub

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    db.close()


def test_acceptance_end_to_end_nilai_hingga_transkrip_csv_dan_pdf(e2e_client):
    """
    Acceptance Test End-to-End (Minggu 10):
    1. Dosen menginput nilai semester 1 (termasuk nilai D / tidak lulus).
    2. Dosen memperbaiki salah satu nilai + audit trail tercatat di grade_history.
    3. Mahasiswa mengulang mata kuliah yang tidak lulus di semester 2 dan mendapat nilai A.
    4. Sistem menghitung IPS & IPK menggunakan nilai terbaik per kode_mk.
    5. Mahasiswa/Admin mengunduh Transkrip JSON, CSV, dan PDF lalu memverifikasi isinya.
    """
    nim = "251636004"

    # 1. Input nilai awal Semester 2026-1
    r1 = e2e_client.put(
        f"/api/kelas/1/nilai/{nim}",
        json={"dosen_id": "DSN01", "nilai_angka": 76.0, "alasan": "Nilai UAS awal"},
    )
    assert r1.status_code == 200
    assert r1.json()["data"]["nilai_baru"] == "B"

    # Mata kuliah IF202 (kelas 2) awalnya mendapat nilai D (tidak lulus)
    r2 = e2e_client.put(
        f"/api/kelas/2/nilai/{nim}",
        json={"dosen_id": "DSN01", "nilai_angka": 45.0, "alasan": "Nilai UAS awal"},
    )
    assert r2.status_code == 200
    assert r2.json()["data"]["nilai_baru"] == "D"

    r3 = e2e_client.put(
        f"/api/kelas/3/nilai/{nim}",
        json={"dosen_id": "DSN02", "nilai_huruf": "B", "alasan": "Nilai akhir"},
    )
    assert r3.status_code == 200

    # 2. Perbaikan nilai kelas 1 dari B menjadi A + cek riwayat audit
    r1_revisi = e2e_client.put(
        f"/api/kelas/1/nilai/{nim}",
        json={"dosen_id": "DSN01", "nilai_angka": 91.0, "alasan": "Revisi nilai praktikum"},
    )
    assert r1_revisi.status_code == 200
    assert r1_revisi.json()["data"]["nilai_lama"] == "B"
    assert r1_revisi.json()["data"]["nilai_baru"] == "A"

    hist_res = e2e_client.get(f"/api/mahasiswa/{nim}/history")
    assert hist_res.status_code == 200
    hist_list = hist_res.json()
    assert len(hist_list) == 4
    assert hist_list[0]["nilai_lama"] == "B"
    assert hist_list[0]["nilai_baru"] == "A"

    # 3. Mahasiswa mengulang IF202 di Semester 2026-2 (kelas 4) dan lulus dengan nilai A
    r4_ulang = e2e_client.put(
        f"/api/kelas/4/nilai/{nim}",
        json={"dosen_id": "DSN01", "nilai_angka": 89.0, "alasan": "Nilai mengulang semester 2"},
    )
    assert r4_ulang.status_code == 200
    assert r4_ulang.json()["data"]["nilai_baru"] == "A"

    # 4. Verifikasi IPK menggunakan nilai terbaik (IF201=A [3 sks], IF202=A [4 sks], IF203=B [3 sks])
    # Total mutu = (3*4.0) + (4*4.0) + (3*3.0) = 12 + 16 + 9 = 37 / 10 SKS = 3.60
    ip_res = e2e_client.get(f"/api/mahasiswa/{nim}/ip")
    assert ip_res.status_code == 200
    assert ip_res.json()["ipk"] == "3.60"

    # 5a. Verifikasi endpoint Transkrip JSON
    json_res = e2e_client.get(f"/api/mahasiswa/{nim}/transkrip")
    assert json_res.status_code == 200
    transkrip = json_res.json()
    assert transkrip["total_sks_tempuh"] == 10
    assert transkrip["total_sks_lulus"] == 10
    assert transkrip["ipk"] == "3.60"
    assert len(transkrip["mata_kuliah"]) == 3

    # 5b. Verifikasi unduhan Transkrip CSV
    csv_res = e2e_client.get(f"/api/mahasiswa/{nim}/transkrip.csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    rows = list(csv.reader(io.StringIO(csv_res.text)))
    flat_text = "\n".join(",".join(r) for r in rows)
    assert "TRANSKRIP AKADEMIK MAHASISWA" in flat_text
    assert nim in flat_text
    assert "3.60" in flat_text

    # 5c. Verifikasi unduhan Transkrip PDF
    pdf_res = e2e_client.get(f"/api/mahasiswa/{nim}/transkrip.pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF-1.4")
    assert b"%%EOF" in pdf_res.content
    assert b"IPK Akhir        : 3.60" in pdf_res.content


def test_transkrip_mahasiswa_tidak_ditemukan(e2e_client):
    res_json = e2e_client.get("/api/mahasiswa/999999999/transkrip")
    res_csv = e2e_client.get("/api/mahasiswa/999999999/transkrip.csv")
    res_pdf = e2e_client.get("/api/mahasiswa/999999999/transkrip.pdf")
    assert res_json.status_code == 404
    assert res_csv.status_code == 404
    assert res_pdf.status_code == 404
    