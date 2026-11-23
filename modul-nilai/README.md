# Sistem Nilai & Transkrip Akademik (Materi 5 · Minggu 9–10)

**Nama:** Muhamad Iqbal Difano  
**NIM:** 251636004  

## Fitur Utama (Minggu 9 & Minggu 10)
1. **Database & Migrasi (`alembic`)**:
   - Tabel referensi `skala_nilai` dengan flag `lulus` sebagai data (bukan hardcoded).
   - Kolom `krs_detail.nilai` terhubung Foreign Key ke `skala_nilai.huruf`.
   - Tabel `grade_history` mencatat audit trail setiap input/perubahan nilai dalam satu transaksi database.
2. **Input Nilai & Validasi (`GradeService` & `PresensiPort`)**:
   - Validasi dosen pengampu kelas (`is_pengampu`).
   - Validasi kehadiran minimal 75% melalui port `PresensiPort` (`PresensiStub`).
3. **Perhitungan IPS & IPK (`GPACalculator`)**:
   - Menggunakan tipe `Decimal` dan pembulatan `ROUND_HALF_UP` satu kali di akhir.
   - Mengambil nilai terbaik per `kode_mk` untuk mata kuliah yang diulang pada perhitungan IPK.
4. **Transkrip Akademik CSV & PDF (`TranscriptService`)**:
   - `GET /api/mahasiswa/{nim}/transkrip` (JSON ringkasan transkrip & SKS lulus).
   - `GET /api/mahasiswa/{nim}/transkrip.csv` (unduh file CSV).
   - `GET /api/mahasiswa/{nim}/transkrip.pdf` (unduh dokumen PDF).
5. **Pengujian Otomatis (`pytest`)**:
   - `test_nilai_m9.py`: 12 kasus `pytest.mark.parametrize` + 3 properti `hypothesis`.
   - `test_acceptance_m10.py`: Acceptance test end-to-end dari input nilai, revisi, mengulang mata kuliah, IPK, hingga unduhan CSV & PDF.

## Cara Menjalankan
```powershell
# Menjalankan seluruh unit test, property test, dan acceptance test
..\sistem_jadwal_m8\venv\Scripts\python.exe -m pytest -v

# Menjalankan server web FastAPI
..\sistem_jadwal_m8\venv\Scripts\python.exe -m uvicorn main:app --reload