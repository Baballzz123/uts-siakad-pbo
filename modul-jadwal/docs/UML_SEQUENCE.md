# UML Sequence Diagram - Perubahan Jadwal, Observer Pattern & AI Rescheduling (Minggu 8)

- **Nama:** Muhamad Iqbal Difano
- **NIM:** 251636004

## 1. Alur AI Rescheduling & Pembaruan Jadwal + Notifikasi Observer

```mermaid
sequenceDiagram
    autonumber
    actor Admin
    participant Dashboard as Dashboard / REST API (main.py)
    participant AI as AIRescheduler
    participant Sweep as SweepLineDetector
    participant Service as SchedulingService
    participant KRS as KRSIntegrationService
    participant Subject as ScheduleSubject (Observer)
    participant DB as SQLite (jadwal.db)

    Admin->>Dashboard: GET /api/ai-reschedule/{jadwal_id}
    Dashboard->>AI: generate_3_alternatives(jadwal_id)
    loop Cari 3 Slot & Ruangan Kandidat
        AI->>Sweep: detect_schedule_conflict(existing + candidate)
        Sweep-->>AI: [] (Bebas Bentrok)
    end
    AI-->>Dashboard: JSON (3 Alternatif Tervalidasi)
    Dashboard-->>Admin: Tampilkan 3 Opsi Jadwal Pengganti

    Admin->>Dashboard: PUT /api/jadwal/{jadwal_id} (Terapkan Opsi Terpilih)
    Dashboard->>Service: update_jadwal(jadwal_id, payload)
    Service->>Sweep: detect_schedule_conflict(candidate)
    Sweep-->>Service: [] (Valid)
    Service->>DB: UPDATE jadwal
    Service->>KRS: invalidate_affected_krs(kelas_id)
    KRS->>DB: UPDATE krs_detail SET status_krs = 'INVALID_SCHEDULE_CHANGED'
    Service->>Subject: notify(SCHEDULE_UPDATED)
    par Broadcast ke 3 Observer
        Subject->>DB: INSERT NotificationLog (Mahasiswa - PUSH)
        Subject->>DB: INSERT NotificationLog (Dosen - SMS)
        Subject->>DB: INSERT NotificationLog (Admin - EMAIL)
    end
    Service-->>Dashboard: 200 OK + Ringkasan Notifikasi & KRS Invalid
    Dashboard-->>Admin: Konfirmasi Pembaruan Berhasil