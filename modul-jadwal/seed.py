from database import SessionLocal
from models import Ruangan, Dosen, Kelas, Jadwal, KRSDetail

def run_seed():
    db = SessionLocal()
    try:
        # Bersihkan data lama agar script idempotent
        db.query(KRSDetail).delete()
        db.query(Jadwal).delete()
        db.query(Kelas).delete()
        db.query(Ruangan).delete()
        db.query(Dosen).delete()
        db.commit()

        # 1. Seed 12 Ruangan (>= 10 ruang)
        ruangan_list = [
            Ruangan(kode_ruang=f"R-{101+i}", nama_ruang=f"Ruang Kuliah {101+i}", kapasitas=30 + (i % 4) * 10)
            for i in range(12)
        ]
        db.add_all(ruangan_list)
        db.commit()

        # 2. Seed 16 Dosen (>= 15 dosen)
        dosen_list = [
            Dosen(nidn=f"03100{10+i}", nama_dosen=f"Dr. Dosen Pengampu {i+1}, M.Kom.")
            for i in range(16)
        ]
        db.add_all(dosen_list)
        db.commit()

        # Refresh untuk mendapatkan ID
        ruangans = db.query(Ruangan).all()
        dosens = db.query(Dosen).all()

        # 3. Seed 42 Kelas
        kelas_list = []
        for i in range(42):
            d = dosens[i % len(dosens)]
            kelas_list.append(
                Kelas(
                    kode_kelas=f"IF-{200+i}",
                    kode_mk=f"MK{100+i}",
                    nama_mk=f"Mata Kuliah Informatika {i+1}",
                    kapasitas_kelas=30,
                    dosen_id=d.id
                )
            )
        db.add_all(kelas_list)
        db.commit()
        kelases = db.query(Kelas).all()

        # 4. Seed 42 Jadwal (>= 40 jadwal), 39 normal + 3 sengaja bentrok untuk uji GET /conflicts
        hari_list = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
        slot_waktu = [
            (480, 580),   # 08:00 - 09:40
            (600, 700),   # 10:00 - 11:40
            (780, 880),   # 13:00 - 14:40
            (900, 1000),  # 15:00 - 16:40
        ]

        jadwal_list = []
        # 39 Jadwal normal tersebar di berbagai hari, slot, dan ruangan
        for i in range(39):
            hari = hari_list[i % len(hari_list)]
            slot = slot_waktu[(i // len(hari_list)) % len(slot_waktu)]
            ruang = ruangans[i % len(ruangans)]
            kls = kelases[i]
            jadwal_list.append(
                Jadwal(
                    kelas_id=kls.id,
                    ruangan_id=ruang.id,
                    dosen_id=kls.dosen_id,
                    hari=hari,
                    jam_mulai=slot[0],
                    jam_selesai=slot[1]
                )
            )

        # 3 Jadwal sengaja dibuat bentrok (ruangan/dosen sama di hari & jam overlap)
        # Bentrok 1: Ruangan sama dengan jadwal indeks 0 (Senin 08:30 - 10:00)
        jadwal_list.append(
            Jadwal(
                kelas_id=kelases[39].id,
                ruangan_id=jadwal_list[0].ruangan_id,
                dosen_id=kelases[39].dosen_id,
                hari=jadwal_list[0].hari,
                jam_mulai=510,
                jam_selesai=600
            )
        )
        # Bentrok 2: Dosen sama dengan jadwal indeks 1 (Selasa 08:00 - 09:40)
        jadwal_list.append(
            Jadwal(
                kelas_id=kelases[40].id,
                ruangan_id=ruangans[-1].id,
                dosen_id=jadwal_list[1].dosen_id,
                hari=jadwal_list[1].hari,
                jam_mulai=480,
                jam_selesai=580
            )
        )
        # Bentrok 3: Ruangan & Dosen sama dengan jadwal indeks 2 (Rabu 09:00 - 10:30)
        jadwal_list.append(
            Jadwal(
                kelas_id=kelases[41].id,
                ruangan_id=jadwal_list[2].ruangan_id,
                dosen_id=jadwal_list[2].dosen_id,
                hari=jadwal_list[2].hari,
                jam_mulai=540,
                jam_selesai=630
            )
        )

        db.add_all(jadwal_list)
        db.commit()

        # Contoh sampel KRSDetail dengan relasi kelas_id
        db.add(KRSDetail(krs_id=1, kelas_id=kelases[0].id, kode_mk=kelases[0].kode_mk, nama_mk=kelases[0].nama_mk, sks=3))
        db.commit()

        print(f"Seed berhasil: {len(ruangans)} ruangan, {len(dosens)} dosen, {len(jadwal_list)} jadwal.")
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()