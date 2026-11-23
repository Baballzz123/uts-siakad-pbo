# Desain Arsitektur Sistem Akademis (SEVIMA-Mini) — UML

**Nama:** Muhamad Iqbal Difano  
**NIM:** 251636004  
**Mata Kuliah:** Rekayasa Perangkat Lunak / Pemrograman Berorientasi Objek (Tugas Minggu 1–2)  

## Struktur Repositori
- `diagrams/class-diagram.mmd` — Class diagram lengkap (Hierarki `User`, modul PMB, KRS, Jadwal, Nilai, Pembayaran, dan Strategy Pattern validator).
- `diagrams/usecase-diagram.mmd` — Use case diagram seluruh aktor dengan relasi `<<include>>` dan `<<extend>>`.
- `diagrams/sequence-pmb.mmd` — Sequence diagram alur pendaftaran mahasiswa baru (PMB) beserta *alternate flow*.
- `diagrams/sequence-krs.mmd` — Sequence diagram validasi KRS (cek SKS maks 24, prasyarat MK, bentrok jadwal) beserta *alternate flow*.
- `prompts/prompt-pack.md` — Kumpulan 6 prompt terstruktur yang digunakan selama perancangan.
- `docs/ai-usage-log.md` — Dokumentasi perbandingan hasil awal AI vs revisi manual dan alasan perbaikannya.
- `docs/ADR-architecture-decisions.pdf` — Architecture Decision Record (keputusan arsitektur, *trade-off*, dan *design pattern*).
- `docs/Final-UML-diagram.pdf` — Laporan visual akhir seluruh diagram UML.