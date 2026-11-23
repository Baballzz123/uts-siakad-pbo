from decimal import Decimal
from sqlalchemy.orm import Session
from database import SessionLocal
from models import SkalaNilai, Mahasiswa, MataKuliah, Kelas, KRS, KRSDetail


def seed_database(db: Session) -> None:
    # 1. Master skala_nilai (lulus = data, bukan hardcode di kode)
    skala_data = [
        ("A", Decimal("4.00"), Decimal("85.00"), Decimal("100.00"), True),
        ("AB", Decimal("3.50"), Decimal("80.00"), Decimal("84.99"), True),
        ("B", Decimal("3.00"), Decimal("70.00"), Decimal("79.99"), True),
        ("BC", Decimal("2.50"), Decimal("65.00"), Decimal("69.99"), True),
        ("C", Decimal("2.00"), Decimal("55.00"), Decimal("64.99"), True),
        ("D", Decimal("1.00"), Decimal("40.00"), Decimal("54.99"), False),
        ("E", Decimal("0.00"), Decimal("0.00"), Decimal("39.99"), False),
    ]
    for huruf, bobot, n_min, n_max, lulus in skala_data:
        if not db.query(SkalaNilai).filter(SkalaNilai.huruf == huruf).first():
            db.add(SkalaNilai(huruf=huruf, bobot=bobot, nilai_min=n_min, nilai_max=n_max, lulus=lulus))
    db.commit()

    # 2. Data Mahasiswa (termasuk NIM kamu 251636004)
    mahasiswa_data = [
        ("251636004", "Muhamad Iqbal Difano", "Teknik Informatika", 2025),
        ("251636005", "Rina Maharani", "Teknik Informatika", 2025),
    ]
    for nim, nama, prodi, angkatan in mahasiswa_data:
        if not db.query(Mahasiswa).filter(Mahasiswa.nim == nim).first():
            db.add(Mahasiswa(nim=nim, nama=nama, prodi=prodi, angkatan=angkatan))
    db.commit()

    # 3. Data Mata Kuliah
    mk_data = [
        ("IF201", "Pemrograman Berorientasi Objek", 3),
        ("IF202", "Basis Data Lanjut", 3),
        ("IF203", "Algoritma & Struktur Data", 4),
    ]
    for kode_mk, nama_mk, sks in mk_data:
        if not db.query(MataKuliah).filter(MataKuliah.kode_mk == kode_mk).first():
            db.add(MataKuliah(kode_mk=kode_mk, nama_mk=nama_mk, sks=sks))
    db.commit()

    # 4. Data Kelas (termasuk contoh mengulang mata kuliah di semester berikutnya)
    if db.query(Kelas).count() == 0:
        kelas_list = [
            Kelas(id=1, kode_mk="IF201", semester="2026-1", nama_kelas="A", dosen_id="DSN01"),
            Kelas(id=2, kode_mk="IF202", semester="2026-1", nama_kelas="A", dosen_id="DSN01"),
            Kelas(id=3, kode_mk="IF203", semester="2026-1", nama_kelas="A", dosen_id="DSN02"),
            Kelas(id=4, kode_mk="IF202", semester="2026-2", nama_kelas="B", dosen_id="DSN01"),  # Kelas ulang IF202
        ]
        db.add_all(kelas_list)
        db.commit()

    # 5. Data KRS & KRS Detail
    if db.query(KRS).count() == 0:
        krs_sem1 = KRS(id=1, nim="251636004", semester="2026-1", status="APPROVED")
        krs_sem2 = KRS(id=2, nim="251636004", semester="2026-2", status="APPROVED")
        krs_rina = KRS(id=3, nim="251636005", semester="2026-1", status="APPROVED")
        db.add_all([krs_sem1, krs_sem2, krs_rina])
        db.commit()

        details = [
            KRSDetail(krs_id=1, kelas_id=1),  # Iqbal - PBO (2026-1)
            KRSDetail(krs_id=1, kelas_id=2),  # Iqbal - Basis Data (2026-1)
            KRSDetail(krs_id=1, kelas_id=3),  # Iqbal - Algoritma (2026-1)
            KRSDetail(krs_id=2, kelas_id=4),  # Iqbal - Basis Data ulang (2026-2)
            KRSDetail(krs_id=3, kelas_id=1),  # Rina - PBO (2026-1, contoh presensi kurang)
        ]
        db.add_all(details)
        db.commit()


if __name__ == "__main__":
    session = SessionLocal()
    try:
        seed_database(session)
        print("Seed database Minggu 9 berhasil dijalankan!")
    finally:
        session.close()