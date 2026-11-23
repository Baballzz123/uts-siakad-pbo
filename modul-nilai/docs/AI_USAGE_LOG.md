# AI Usage Log & OPAR — Tugas Minggu 9

| No | Bagian / Modul | Peran AI | Verifikasi & Keputusan Mahasiswa |
|----|----------------|----------|----------------------------------|
| 1 | Migrasi Alembic & Model SQLAlchemy (`models.py`) | Menyusun relasi FK `krs_detail.nilai -> skala_nilai.huruf` dan tabel `grade_history`. | Diverifikasi dengan menjalankan `alembic upgrade head` dan inspeksi schema SQLite `nilai.db`. |
| 2 | `GradeService` & `PresensiPort` | Menyusun validasi `is_pengampu`, cek presensi >= 75%, dan penyimpanan transaksi atomik. | Diuji pada skenario dosen salah (403), presensi kurang (422), dan update nilai berulang. |
| 3 | `GPACalculator` (`Decimal` + `ROUND_HALF_UP`) | Mengimplementasikan perhitungan IPS per semester dan IPK nilai terbaik per `kode_mk`. | Diverifikasi manual dengan kasus mengulang mata kuliah `IF202` (D -> A) dan 3 properti Hypothesis. |

## Catatan OPAR (Observe - Plan - Act - Reflect)
- **Observe:** Perhitungan IPK sering keliru jika memakai `float` atau menghitung ulang mata kuliah yang diulang dua kali.
- **Plan:** Pisahkan `NilaiRepo` dan `GPACalculator` murni menggunakan `Decimal`, lalu uji dengan `pytest.mark.parametrize` dan `hypothesis`.
- **Act:** Membangun endpoint `PUT /api/kelas/{id}/nilai/{nim}`, form web `/dashboard`, 12 test parametrize, dan 3 test properti.
- **Reflect:** Seluruh pengujian lolos dan perubahan nilai tercatat lengkap di `grade_history`.