# Architecture Decision Record (ADR) - Pemilihan Algoritma Deteksi Bentrok Jadwal

## Konteks
Sistem penjadwalan perkuliahan membutuhkan deteksi bentrok waktu pada resource yang sama (Ruangan dan Dosen) menggunakan representasi interval setengah terbuka `[jam_mulai, jam_selesai)`.

## Opsi yang Dipertimbangkan
1. **Algoritma Naif (Nested Loop)** — Kompleksitas waktu $O(N^2)$, ruang $O(1)$. Mudah ditulis namun lambat ketika jumlah jadwal dalam satu semester mencapai ratusan hingga ribuan kelas.
2. **Sweep Line Algorithm** — Kompleksitas waktu $O(N \log N)$ untuk pengurutan titik event mulai/selesai dan $O(N + K)$ untuk pemindaian interval aktif ($K$ = jumlah bentrok). Sangat efisien untuk batch validation (`GET /conflicts`) dan pengecekan jadwal per hari tanpa struktur tree persisten.
3. **Interval Tree / Augmented BST** — Kompleksitas build $O(N \log N)$ dan query overlap $O(\log N + K)$. Optimal apabila sistem membutuhkan ribuan query pembacaan dinamis tanpa memodifikasi seluruh daftar setiap saat, namun membutuhkan implementasi struktur pohon seimbang tambahan dan sinkronisasi memori dengan database relasional.

## Keputusan
Memilih **Sweep Line Algorithm** (`detect_schedule_conflict`) sebagai detektor utama di backend karena memberikan keseimbangan terbaik antara kompleksitas asimtotik $O(N \log N)$, determinisme urutan pemrosesan event selesai sebelum mulai pada titik waktu yang sama, dan kesederhanaan pemeliharaan kode.