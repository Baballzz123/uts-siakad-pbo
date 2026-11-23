# AI Usage Log - Implementasi Modul PMB (Minggu 3-4)

1. **Perancangan Skema Database & Migrasi**
   - **Prompt:** Merancang tabel SQLAlchemy (`calon_mahasiswa`, `program_studi`, `jalur_masuk`) lengkap dengan Enum status, validasi format telepon Indonesia, dan script migrasi Alembic beserta `downgrade()` rollback.
   - **Verifikasi Manual:** Memastikan urutan penghapusan tabel pada `downgrade()` sesuai dengan relasi *Foreign Key*.

2. **Pembuatan REST API FastAPI**
   - **Prompt:** Membuat endpoint `/api/pmb/register`, `/api/pmb/status/{id}`, `/api/pmb/approve/{id}`, dan `/api/pmb/stats` dengan HTTP status code `201`, `400`, `404`, dan `409`.
   - **Verifikasi Manual:** Menguji seluruh endpoint secara interaktif melalui Swagger UI (`/docs`).

3. **Algoritma NIM Generator Thread-Safe**
   - **Prompt:** Mengimplementasikan fungsi `generate_nim` berformat `YYYY[KODE]-XXXX` yang *idempotent* dan mencegah *race condition*.
   - **Verifikasi Manual:** Menambahkan mekanisme `threading.Lock()` dan `.with_for_update()` serta memverifikasi urutan nomor NIM saat dilakukan *approve* berulang.

4. **Pembuatan Unit Test Pytest**
   - **Prompt:** Menyusun *test suite* otomatis menggunakan `pytest` dan `TestClient` dengan database terisolasi.
   - **Verifikasi Manual:** Menjalankan `pytest -v` dan memastikan seluruh skenario *pass*.