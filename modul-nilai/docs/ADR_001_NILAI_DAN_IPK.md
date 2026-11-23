# ADR-001: Arsitektur Penyimpanan Nilai, Audit Trail, dan Kalkulasi IPS/IPK

- **Status:** Accepted
- **Konteks:** Sistem membutuhkan pencatatan nilai mahasiswa yang tervalidasi, tahan terhadap perubahan aturan batas lulus, memiliki riwayat perubahan nilai yang tidak hilang, serta presisi tinggi pada perhitungan IPS dan IPK.
- **Keputusan:**
  1. **Foreign Key & Data-Driven Passing Grade:** Kolom `krs_detail.nilai` direlasikan sebagai Foreign Key ke `skala_nilai.huruf`. Status kelulusan disimpan sebagai kolom boolean `skala_nilai.lulus` (bukan *hardcode* `if huruf != 'E'`).
  2. **Transactional Audit Trail:** Setiap panggilan `GradeService.input_nilai` memperbarui `krs_detail` sekaligus menyisipkan baris baru ke `grade_history` dalam satu transaksi `commit()` atomik.
  3. **Hexagonal Port untuk Presensi:** Menggunakan abstraksi `PresensiPort` dan implementasi `PresensiStub` agar modul nilai tidak terikat langsung pada implementasi database presensi.
  4. **Presisi Desimal & Nilai Terbaik:** `GPACalculator` menggunakan tipe `Decimal` dan menerapkan `ROUND_HALF_UP` **satu kali** di akhir pembagian `total_mutu / total_sks`, dengan pengelompokan nilai terbaik per `kode_mk` untuk IPK.