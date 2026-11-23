# AI Usage Documentation & Review Log

**Nama:** Muhamad Iqbal Difano  
**NIM:** 251636004  
**Topik:** Desain Arsitektur Sistem Akademis (SEVIMA-Mini) dengan UML  

## 1. Ringkasan Penggunaan AI
Dalam pengerjaan tugas ini, AI digunakan sebagai asisten perancangan untuk menghasilkan draf awal diagram UML berbasis teks (Mermaid), kemudian dilakukan validasi dan revisi manual berdasarkan prinsip Object-Oriented Programming (OOP) dan SOLID.

## 2. Perbandingan Hasil AI vs Revisi Manual

| No | Aspek / Diagram | Hasil Awal dari AI (Before) | Revisi Manual yang Dilakukan (After) | Alasan Revisi Diperlukan |
|---|---|---|---|---|
| 1 | **Class Diagram: Validasi KRS** | AI menaruh semua method validasi (`cekSKS`, `cekPrasyarat`, `cekBentrok`, `approveKRS`) langsung di dalam class `Enrollment`. | Memecah validasi menjadi `KRSValidator` dan interface `IValidationRule` (`MaxSKSValidationRule`, `PrerequisiteValidationRule`, `ScheduleConflictValidationRule`). | Mencegah *God Object* dan menerapkan *Single Responsibility* serta *Open/Closed Principle* (aturan baru dapat ditambah tanpa mengubah `Enrollment`). |
| 2 | **Class Diagram: Relasi Kepemilikan** | AI menggunakan asosiasi biasa (`-->`) untuk seluruh hubungan antar class. | Mengubah relasi `Enrollment`–`EnrollmentDetail` dan `Course`–`CoursePrerequisite` menjadi **Composition (`*--`)**, serta `Mahasiswa`–`Enrollment` menjadi **Aggregation (`o--`)**. | Detail KRS dan prasyarat tidak memiliki siklus hidup mandiri tanpa induknya, sedangkan data `Mahasiswa` tetap ada meskipun KRS semester dihapus. |
| 3 | **Class Diagram: Tipe Data Keuangan & Nilai** | AI menggunakan tipe data `float` untuk nominal pembayaran dan nilai angka. | Mengubah tipe data `nominal`, `nilaiAngka`, dan `bobotMutu` menjadi `Decimal`. | Menghindari *floating-point rounding error* pada perhitungan IPS/IPK dan transaksi biaya pendidikan. |
| 4 | **Use Case Diagram: Relasi Fungsional** | AI menghubungkan aktor langsung ke seluruh use case tanpa membedakan perilaku wajib dan opsional. | Menambahkan relasi `<<include>>` untuk `Validasi Prasyarat, SKS & Bentrok` dan `Autentikasi Login`, serta `<<extend>>` untuk `Export Transkrip PDF / CSV` dan `Revisi Nilai`. | Memperjelas alur prasyarat wajib vs fitur tambahan yang hanya dijalankan dalam kondisi tertentu. |
| 5 | **Sequence Diagram: Penanganan Error** | Draf awal AI hanya menampilkan *happy path* (semua validasi berhasil). | Menambahkan blok `alt / else` untuk kegagalan validasi berkas PMB, ketidaklulusan seleksi, serta penolakan KRS (SKS > 24, prasyarat tidak terpenuhi, bentrok jadwal). | Sistem akademik nyata wajib mendokumentasikan skenario penolakan (*alternate flow*) dan status HTTP error yang dikembalikan ke pengguna. |

## 3. Kesimpulan Validasi
Seluruh nama class, atribut, dan method pada `class-diagram.mmd` telah disinkronkan dengan pemanggilan pesan pada `sequence-pmb.mmd` dan `sequence-krs.mmd`, bebas dari *circular dependency*, serta siap menjadi cetak biru implementasi modul PMB hingga Transkrip.