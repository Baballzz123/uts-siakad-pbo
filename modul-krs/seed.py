from database import SessionLocal
from models import SkalaNilai, Prerequisite, KRS, KRSDetail, RiwayatNilai

def run_seed():
    db = SessionLocal()
    try:
        if db.query(SkalaNilai).first():
            print("Data dummy sudah ada di database!")
            return

        # 1. Isi Skala Nilai
        skala = [
            SkalaNilai(huruf="A", bobot=4.0),
            SkalaNilai(huruf="B", bobot=3.0),
            SkalaNilai(huruf="C", bobot=2.0),
            SkalaNilai(huruf="D", bobot=1.0),
            SkalaNilai(huruf="E", bobot=0.0),
        ]
        db.add_all(skala)

        # 2. Isi Aturan Prasyarat
        prereqs = [
            Prerequisite(kode_mk="IF201", kode_mk_syarat="IF101", min_huruf="C"),
            Prerequisite(kode_mk="IF301", kode_mk_syarat="IF201", min_huruf="B"),
        ]
        db.add_all(prereqs)

        # 3. Isi Riwayat Nilai Mahasiswa (NIM: 251636004)
        riwayat = [
            RiwayatNilai(nim="251636004", kode_mk="IF101", nilai_huruf="B"),
            RiwayatNilai(nim="251636004", kode_mk="IF201", nilai_huruf="C"),
        ]
        db.add_all(riwayat)

        # 4. Buat 1 Header KRS
        krs = KRS(nim="251636004", semester="2026-1", status="DRAFT", total_sks=3)
        db.add(krs)
        db.flush()

        # 5. Isi 1 Mata Kuliah Awal di KRS Detail (Senin 08:00 - 10:30 -> 480 - 630 menit)
        detail_awal = KRSDetail(
            krs_id=krs.id,
            kode_mk="IF202",
            nama_mk="Basis Data Lanjut",
            sks=3,
            hari="Senin",
            jam_mulai=480,
            jam_selesai=630
        )
        db.add(detail_awal)

        db.commit()
        print("Berhasil mengisi seed data dummy!")
    except Exception as e:
        db.rollback()
        print(f"Terjadi error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()