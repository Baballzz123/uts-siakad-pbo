# Architecture Decision Record (ADR) - Validasi KRS

## 1. Strategi Penanganan Error: Fail-Fast (Berhenti) vs Collect-All (Kumpulkan Error)
* **Konteks:** Pada pola *Chain of Responsibility*, setiap validator dapat langsung menghentikan proses saat menemukan error pertama (*fail-fast*), atau meneruskan validasi hingga akhir rantai untuk mengumpulkan seluruh pesan error (*collect-all*).
* **Keputusan:** Menggunakan pendekatan **Collect-All (Kumpulkan Semua Error)**.
* **Alasan:**
  1. **Pengalaman Pengguna (UX):** Mahasiswa langsung mendapatkan daftar lengkap alasan penolakan mata kuliah dalam satu kali klik (misalnya: jadwal bentrok *sekaligus* prasyarat nilai belum terpenuhi), sehingga tidak perlu melakukan percobaan berulang kali (*trial-and-error*).
  2. **Efisiensi Transaksi:** Mengurangi jumlah *request* ulang ke server yang hanya akan gagal di tahap validasi berikutnya.

## 2. Urutan Rantai Validator (Chain Ordering)
* **Keputusan:** Urutan rantai disusun sebagai berikut:
  `DuplicateCourseValidator` -> `MaxSKSValidator` -> `ScheduleConflictValidator` -> `PrerequisiteValidator`
* **Alasan:**
  1. **Biaya Komputasi (Cheapest-First):** Tiga validator pertama (`Duplicate`, `MaxSKS`, dan `ScheduleConflict`) hanya memproses data list `existing_details` yang sudah dimuat ke memori (`O(N)` tanpa *query* tambahan ke database).
  2. **Isolasi Query Berat:** `PrerequisiteValidator` diletakkan di urutan terakhir karena melakukan *query* relasional `NOT EXISTS` yang menggabungkan tabel `prerequisite`, `riwayat_nilai`, dan `skala_nilai`.