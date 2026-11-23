# Kumpulan Prompt Terbaik (Prompt Engineering Log)

**Nama:** Muhamad Iqbal Difano  
**NIM:** 251636004  

## Prompt 1: Perancangan Awal Class Diagram Inti & Hierarki User
> "Anda adalah senior software architect. Buat class diagram UML dalam format Mermaid untuk sistem informasi akademik (SEVIMA-Mini) dengan hierarki User (CalonMahasiswa, Mahasiswa, Dosen, Admin) serta class inti Course, Enrollment, Schedule, Grade, dan Payment. Terapkan prinsip SOLID, bedakan relasi composition dan aggregation, serta sertakan visibility modifier (+, -, #)."

## Prompt 2: Refactoring Validasi KRS dengan Strategy Pattern (Menghindari God Object)
> "Audit class diagram modul KRS berikut agar mematuhi prinsip Single Responsibility dan Open/Closed Principle. Pisahkan logika pengecekan SKS maksimal 24, prasyarat mata kuliah, dan jadwal bentrok menjadi class tersendiri menggunakan Strategy Pattern (KRSValidator dan IValidationRule). Output dalam format Mermaid."

## Prompt 3: Perancangan Use Case Diagram dengan Include & Extend
> "Buat use case diagram sistem akademik dalam format Mermaid dengan aktor CalonMahasiswa, Mahasiswa, Dosen, Admin Akademik, dan Sistem PMB. Sertakan alur PMB, isi & approve KRS, input nilai, hingga cetak transkrip. Tandai relasi <<include>> dan <<extend>> secara eksplisit."

## Prompt 4: Sequence Diagram Alur Pendaftaran Mahasiswa Baru (PMB)
> "Buat sequence diagram Mermaid untuk proses pendaftaran mahasiswa baru (PMB) dari pengisian formulir, upload dokumen, pembuatan tagihan virtual account, konfirmasi pembayaran, hingga generate NIM. Wajib sertakan blok alt/else untuk penanganan berkas tidak lengkap dan hasil tidak lulus seleksi."

## Prompt 5: Sequence Diagram Validasi KRS & Pengecekan Prasyarat
> "Buat sequence diagram Mermaid untuk proses submit dan validasi KRS oleh Mahasiswa melalui KRSValidator (cek maksimal 24 SKS, prasyarat mata kuliah lulus, dan jadwal bentrok). Sertakan alternate flow penolakan HTTP 422 jika salah satu aturan gagal, serta pengiriman notifikasi ke Dosen PA jika status menjadi Pending Approval."

## Prompt 6: Audit & Validasi Akhir Konsistensi Antar-Diagram
> "Periksa konsistensi nama class, method, dan parameter antara class-diagram.mmd, sequence-pmb.mmd, dan sequence-krs.mmd. Pastikan tidak ada circular dependency dan setiap method yang dipanggil di sequence diagram tersedia di class diagram."