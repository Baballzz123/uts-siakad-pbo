import pytest
from fastapi.testclient import TestClient
from hypothesis import given, strategies as st, settings
from main import app
from conflict_detector import detect_naive, detect_schedule_conflict, is_overlap
from seed import run_seed

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_data():
    run_seed()

# --- 1. TEST CONTOH (API & EDGE CASE) ---

def test_get_conflicts_from_seeded_data():
    res = client.get("/conflicts")
    assert res.status_code == 200
    data = res.json()
    assert data["total_conflicts"] >= 3

def test_boundary_no_conflict_adjacent_times():
    # Jadwal bersambungan [08:00, 10:00) dan [10:00, 12:00) TIDAK boleh bentrok
    sample = [
        {"id": 1, "ruangan_id": 1, "dosen_id": 1, "hari": "Sabtu", "jam_mulai": 480, "jam_selesai": 600},
        {"id": 2, "ruangan_id": 1, "dosen_id": 1, "hari": "Sabtu", "jam_mulai": 600, "jam_selesai": 720},
    ]
    assert detect_schedule_conflict(sample) == []

def test_api_crud_and_status_codes():
    # 201 Created pada hari Sabtu (masih kosong)
    payload_ok = {
        "kelas_id": 1,
        "ruangan_id": 1,
        "dosen_id": 1,
        "hari": "Sabtu",
        "jam_mulai": 480,
        "jam_selesai": 580
    }
    res_create = client.post("/api/jadwal", json=payload_ok)
    assert res_create.status_code == 201
    created_id = res_create.json()["id"]

    # 409 Conflict jika bentrok ruangan/dosen di jam overlap
    payload_conflict = {
        "kelas_id": 2,
        "ruangan_id": 1,
        "dosen_id": 2,
        "hari": "Sabtu",
        "jam_mulai": 500,
        "jam_selesai": 600
    }
    res_409 = client.post("/api/jadwal", json=payload_conflict)
    assert res_409.status_code == 409
    assert "conflicts" in res_409.json()["detail"]

    # 422 Unprocessable Entity jika jam_mulai >= jam_selesai
    payload_invalid_time = {
        "kelas_id": 1,
        "ruangan_id": 1,
        "dosen_id": 1,
        "hari": "Sabtu",
        "jam_mulai": 600,
        "jam_selesai": 500
    }
    res_422 = client.post("/api/jadwal", json=payload_invalid_time)
    assert res_422.status_code == 422

    # 200 OK saat PUT update jadwal valid
    payload_update = {
        "kelas_id": 1,
        "ruangan_id": 1,
        "dosen_id": 1,
        "hari": "Sabtu",
        "jam_mulai": 600,
        "jam_selesai": 700
    }
    res_put = client.put(f"/api/jadwal/{created_id}", json=payload_update)
    assert res_put.status_code == 200

    # 204 No Content saat DELETE
    res_del = client.delete(f"/api/jadwal/{created_id}")
    assert res_del.status_code == 204

    # 404 Not Found jika DELETE ID yang sudah dihapus
    res_404 = client.delete(f"/api/jadwal/{created_id}")
    assert res_404.status_code == 404

# --- 2. DUA PROPERTY-BASED TEST (HYPOTHESIS) ---

# Properti 1: Sweep Line O(N log N) harus selalu menghasilkan pasangan bentrok yang identik dengan Naive O(N^2)
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=4),    # ruangan_id
            st.integers(min_value=1, max_value=4),    # dosen_id
            st.sampled_from(["Senin", "Selasa"]),     # hari
            st.integers(min_value=480, max_value=900),# jam_mulai
            st.integers(min_value=30, max_value=120), # durasi
        ),
        min_size=0,
        max_size=25
    )
)
@settings(max_examples=50)
def test_property_sweep_matches_naive(raw_items):
    schedules = []
    for idx, (r_id, d_id, hari, start, dur) in enumerate(raw_items, start=1):
        schedules.append({
            "id": idx,
            "ruangan_id": r_id,
            "dosen_id": d_id,
            "hari": hari,
            "jam_mulai": start,
            "jam_selesai": start + dur,
        })

    naive_pairs = {(c["jadwal_1_id"], c["jadwal_2_id"]) for c in detect_naive(schedules)}
    sweep_pairs = {(c["jadwal_1_id"], c["jadwal_2_id"]) for c in detect_schedule_conflict(schedules)}
    assert sweep_pairs == naive_pairs

# Properti 2: Simetri & Batas Interval Setengah Terbuka [mulai, selesai)
@given(
    s1=st.integers(min_value=480, max_value=1000),
    d1=st.integers(min_value=15, max_value=180),
    s2=st.integers(min_value=480, max_value=1000),
    d2=st.integers(min_value=15, max_value=180),
)
@settings(max_examples=50)
def test_property_interval_symmetry_and_boundary(s1, d1, s2, d2):
    e1, e2 = s1 + d1, s2 + d2
    # Simetri: overlap(A, B) == overlap(B, A)
    assert is_overlap(s1, e1, s2, e2) == is_overlap(s2, e2, s1, e1)
    # Boundary: [s1, e1) dan [e1, e1 + d2) tidak pernah overlap
    assert is_overlap(s1, e1, e1, e1 + d2) is False