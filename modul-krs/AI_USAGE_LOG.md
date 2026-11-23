# AI Usage Log & Refleksi OPAR - Tugas Minggu 5

## Log Prompt & Revisi
1. **Prompt 1 (Perancangan Skema & Lingkungan Kerja):**
   * *Tujuan:* Merancang 4 tabel database (`skala_nilai`, `prerequisite`, `krs`, `krs_detail`) beserta tabel pendukung `riwayat_nilai` menggunakan SQLAlchemy dan Alembic.
   * *Revisi / Troubleshooting:* Terjadi pemblokiran Windows Application Control pada file `pip.exe` dan C-extension SQLAlchemy (`_collections_cy`). Solusi: menjalankan modul melalui `python -m` dan menginstal SQLAlchemy versi Python murni (`DISABLE_SQLALCHEMY_CEXT=1`).
2. **Prompt 2 (Implementasi Chain of Responsibility & Query Prasyarat):**
   * *Tujuan:* Membangun `build_chain()` dengan 4 validator, query `NOT EXISTS` + bobot nilai, serta mekanisme *row lock* (`with_for_update()`) pada `KRSManager`.
   * *Revisi:* Menyimpan `jam_mulai` dan `jam_selesai` dalam satuan menit integer (contoh: 08:00 = 480) agar pengecekan irisan interval jadwal lebih akurat dan bebas error parsing waktu.
3. **Prompt 3 (Pengujian & Bukti Index):**
   * *Tujuan:* Membuat skrip verifikasi `EXPLAIN QUERY PLAN` dan unit/integration test menggunakan `pytest` dengan database in-memory.

## Ringkasan OPAR (Observe, Plan, Act, Reflect)
* **Observe:** Sistem KRS membutuhkan validasi berlapis yang konsisten serta perlindungan dari *race condition* saat menambah/menghapus mata kuliah.
* **Plan:** Memisahkan akses database (`repository.py`), aturan bisnis (`validators.py`), dan orkestrasi transaksi (`krs_manager.py`).
* **Act:** Mengimplementasikan migrasi Alembic, seed data dummy, 4 validator berantai, row-level locking, dan 6 skenario pengujian `pytest`.
* **Reflect:** Penggunaan indeks gabungan (`idx_prereq_mk_syarat` dan `idx_riwayat_nim_mk`) terbukti digunakan oleh query planner berdasarkan hasil `EXPLAIN`.