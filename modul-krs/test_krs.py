import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models import SkalaNilai, Prerequisite, KRS, KRSDetail, RiwayatNilai
from krs_manager import KRSManager

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    db.add_all([
        SkalaNilai(huruf="A", bobot=4.0),
        SkalaNilai(huruf="B", bobot=3.0),
        SkalaNilai(huruf="C", bobot=2.0),
        SkalaNilai(huruf="D", bobot=1.0),
        SkalaNilai(huruf="E", bobot=0.0),
    ])
    db.add_all([
        Prerequisite(kode_mk="IF201", kode_mk_syarat="IF101", min_huruf="C"),
        Prerequisite(kode_mk="IF301", kode_mk_syarat="IF201", min_huruf="B"),
    ])
    db.add_all([
        RiwayatNilai(nim="251636004", kode_mk="IF101", nilai_huruf="B"),
        RiwayatNilai(nim="251636004", kode_mk="IF201", nilai_huruf="C"),
    ])
    krs = KRS(nim="251636004", semester="2026-1", status="DRAFT", total_sks=3)
    db.add(krs)
    db.flush()
    
    db.add(KRSDetail(
        krs_id=krs.id,
        kode_mk="IF202",
        nama_mk="Basis Data Lanjut",
        sks=3,
        hari="Senin",
        jam_mulai=480,
        jam_selesai=630
    ))
    db.commit()
    
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_add_course_success(db_session):
    manager = KRSManager(db_session)
    mk_valid = {
        "kode_mk": "IF201",
        "nama_mk": "Struktur Data",
        "sks": 3,
        "hari": "Selasa",
        "jam_mulai": 480,
        "jam_selesai": 630
    }
    res = manager.add_course(krs_id=1, new_course=mk_valid)
    assert res["status"] == "success"
    assert res["total_sks"] == 6

def test_duplicate_course_rejected(db_session):
    manager = KRSManager(db_session)
    mk_dup = {
        "kode_mk": "IF202",
        "nama_mk": "Basis Data Lanjut",
        "sks": 3,
        "hari": "Rabu",
        "jam_mulai": 600,
        "jam_selesai": 750
    }
    res = manager.add_course(krs_id=1, new_course=mk_dup)
    assert res["status"] == "error"
    assert any("sudah ada di dalam KRS" in err for err in res["errors"])

def test_schedule_conflict_rejected(db_session):
    manager = KRSManager(db_session)
    mk_bentrok = {
        "kode_mk": "IF205",
        "nama_mk": "Jaringan Komputer",
        "sks": 3,
        "hari": "Senin",
        "jam_mulai": 540,
        "jam_selesai": 660
    }
    res = manager.add_course(krs_id=1, new_course=mk_bentrok)
    assert res["status"] == "error"
    assert any("Jadwal bentrok" in err for err in res["errors"])

def test_unmet_prerequisite_rejected(db_session):
    manager = KRSManager(db_session)
    mk_gagal_syarat = {
        "kode_mk": "IF301",
        "nama_mk": "Kecerdasan Buatan",
        "sks": 3,
        "hari": "Kamis",
        "jam_mulai": 480,
        "jam_selesai": 630
    }
    res = manager.add_course(krs_id=1, new_course=mk_gagal_syarat)
    assert res["status"] == "error"
    assert any("Prasyarat IF201" in err for err in res["errors"])

def test_collect_all_errors_at_once(db_session):
    manager = KRSManager(db_session)
    mk_multi_error = {
        "kode_mk": "IF301",
        "nama_mk": "Kecerdasan Buatan",
        "sks": 22,
        "hari": "Senin",
        "jam_mulai": 500,
        "jam_selesai": 600
    }
    res = manager.add_course(krs_id=1, new_course=mk_multi_error)
    assert res["status"] == "error"
    assert len(res["errors"]) == 3

def test_remove_course_success(db_session):
    manager = KRSManager(db_session)
    res = manager.remove_course(krs_id=1, kode_mk="IF202")
    assert res["status"] == "success"
    assert res["total_sks"] == 0