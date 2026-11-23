# AI Usage Log & Analisis OPAR - Tugas Minggu 7

- **Nama:** Muhamad Iqbal Difano
- **NIM:** 251636004
- **Mata Kuliah:** Pengembangan Sistem / Rekayasa Perangkat Lunak (Minggu 7)

## Log Penggunaan AI
1. **Perancangan Skema & Migrasi Alembic:** Meminta bantuan penyusunan model SQLAlchemy (`Ruangan`, `Dosen`, `Kelas`, `Jadwal`, `KRSDetail`) beserta indeks komposit `(hari, ruangan_id)` dan `(hari, dosen_id)`.
2. **Implementasi Sweep Line & REST API:** Menyusun `detect_schedule_conflict`, validasi kapasitas ruangan, *row-level locking*, serta kode status HTTP (`201`, `204`, `404`, `409`, `422`).
3. **Property-Based Testing:** Menggunakan library `hypothesis` untuk memverifikasi kesetaraan hasil antara `detect_naive` dan `detect_schedule_conflict`.

## Analisis OPAR (Observe, Plan, Act, Reflect)
- **Observe:** Deteksi bentrok jadwal perkuliahan memiliki dua hard constraint utama (ruangan ganda dan dosen ganda pada hari & rentang waktu beririsan) serta batasan kapasitas kelas terhadap kapasitas ruangan.
- **Plan:** Memisahkan lapisan deteksi algoritma murni (`conflict_detector.py`) dari lapisan transaksi database (`scheduling_service.py`) agar mudah diuji menggunakan *property-based testing*.
- **Act:** Mengimplementasikan algoritma Sweep Line dengan konvensi interval `[jam_mulai, jam_selesai)`, menambahkan *row lock* saat operasi `create`/`update`/`delete`, serta membuat data seed sebanyak 12 ruangan, 16 dosen, dan 42 jadwal (39 normal + 3 bentrok).
- **Reflect:** Pengujian otomatis membuktikan Sweep Line konsisten 100% dengan metode naif sekaligus menangani kasus batas jadwal bersambungan tanpa false positive.