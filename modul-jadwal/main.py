from fastapi import FastAPI, Depends, Response, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from database import get_db
from models import Jadwal, Kelas, Ruangan, KRSDetail, NotificationLog
from scheduling_service import SchedulingService
from ai_rescheduler import AIRescheduler

app = FastAPI(title="Sistem Penjadwalan, Outbox Observer & AI Rescheduling - Minggu 8")

class JadwalSchema(BaseModel):
    kelas_id: int
    ruangan_id: int
    dosen_id: int
    hari: str = Field(..., pattern="^(Senin|Selasa|Rabu|Kamis|Jumat|Sabtu)$")
    jam_mulai: int = Field(..., ge=420, le=1260)
    jam_selesai: int = Field(..., ge=420, le=1320)

class JadwalResponse(JadwalSchema):
    id: int
    model_config = ConfigDict(from_attributes=True)

@app.post("/api/jadwal", response_model=JadwalResponse, status_code=status.HTTP_201_CREATED)
def create_jadwal(payload: JadwalSchema, db: Session = Depends(get_db)):
    return SchedulingService.create_jadwal(db, payload.model_dump())

@app.put("/api/jadwal/{jadwal_id}")
def update_jadwal(jadwal_id: int, payload: JadwalSchema, db: Session = Depends(get_db)):
    result = SchedulingService.update_jadwal(db, jadwal_id, payload.model_dump())
    return {
        "jadwal": JadwalResponse.model_validate(result["jadwal"]),
        "invalidated_krs_count": result["invalidated_krs_count"],
        "notifications_sent": result["notifications_sent"]
    }

@app.delete("/api/jadwal/{jadwal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_jadwal(jadwal_id: int, db: Session = Depends(get_db)):
    SchedulingService.delete_jadwal(db, jadwal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/conflicts")
def list_conflicts(db: Session = Depends(get_db)):
    conflicts = SchedulingService.get_all_conflicts(db)
    return {"total_conflicts": len(conflicts), "conflicts": conflicts}

@app.get("/api/ai-reschedule/{jadwal_id}")
def ai_reschedule_suggestions(jadwal_id: int, db: Session = Depends(get_db)):
    return AIRescheduler.generate_3_alternatives(db, jadwal_id)

@app.get("/api/notifications")
def list_notifications(db: Session = Depends(get_db)):
    return db.query(NotificationLog).order_by(NotificationLog.id.desc()).limit(30).all()

@app.get("/api/krs-status")
def list_krs_status(db: Session = Depends(get_db)):
    return db.query(KRSDetail).all()

# Ekspor Kalender Standar iCalendar (.ics)
@app.get("/api/jadwal/export.ics")
def export_jadwal_ics(db: Session = Depends(get_db)):
    day_map = {"Senin": "20261123", "Selasa": "20261124", "Rabu": "20261125", "Kamis": "20261126", "Jumat": "20261127", "Sabtu": "20261128"}
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ISTN//Sistem Jadwal Kuliah//ID"]
    for j in db.query(Jadwal).all():
        kelas = db.query(Kelas).filter(Kelas.id == j.kelas_id).first()
        ruang = db.query(Ruangan).filter(Ruangan.id == j.ruangan_id).first()
        tgl = day_map.get(j.hari, "20261123")
        dtstart = f"{tgl}T{j.jam_mulai // 60:02d}{j.jam_mulai % 60:02d}00"
        dtend = f"{tgl}T{j.jam_selesai // 60:02d}{j.jam_selesai % 60:02d}00"
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:jadwal-{j.id}@istn.ac.id",
            f"SUMMARY:{kelas.kode_kelas if kelas else 'MK'} - {kelas.nama_mk if kelas else 'Kuliah'}",
            f"LOCATION:{ruang.kode_ruang if ruang else 'Ruang'}",
            f"DTSTART:{dtstart}",
            f"DTEND:{dtend}",
            "END:VEVENT"
        ])
    lines.append("END:VCALENDAR")
    return PlainTextResponse(
        content="\r\n".join(lines),
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=jadwal_kuliah.ics"}
    )

@app.get("/dashboard", response_class=HTMLResponse)
def admin_conflict_dashboard(db: Session = Depends(get_db)):
    conflicts = SchedulingService.get_all_conflicts(db)
    logs = db.query(NotificationLog).order_by(NotificationLog.id.desc()).limit(10).all()
    krs_rev = db.query(KRSDetail).filter(KRSDetail.status_krs != "VALID").all()

    conflict_rows = "".join([
        f"<tr><td>#{c['jadwal_1_id']} vs #{c['jadwal_2_id']}</td><td>{c['hari']}</td><td>{c['alasan']}</td>"
        f"<td><button onclick='loadAI({c['jadwal_2_id']})'>Saran AI & Resolve</button></td></tr>"
        for c in conflicts
    ]) or "<tr><td colspan='4'>Tidak ada jadwal bentrok saat ini.</td></tr>"

    log_rows = "".join([f"<li><b>[{l.recipient_role} - {l.channel}]</b> {l.message}</li>" for l in logs]) or "<li>Belum ada log.</li>"
    krs_rows = "".join([f"<li>NIM {k.nim} | {k.kode_mk} &rarr; <b>{k.status_krs}</b> ({k.catatan})</li>" for k in krs_rev]) or "<li>Semua KRS VALID.</li>"

    html_template = """<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Dashboard Conflict Resolver - Minggu 8</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 24px; background: #f8fafc; color: #0f172a; }
        .card { background: white; padding: 18px; border-radius: 8px; margin-bottom: 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #cbd5e1; padding: 10px; text-align: left; }
        th { background: #1e293b; color: white; }
        button { background: #2563eb; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; margin-right: 6px; }
        a.btn { display: inline-block; background: #059669; color: white; padding: 8px 14px; border-radius: 4px; text-decoration: none; margin-bottom: 12px; }
        pre { background: #0f172a; color: #38bdf8; padding: 12px; border-radius: 6px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Dashboard Conflict Resolver & AI Rescheduling</h1>
    <a class="btn" href="/api/jadwal/export.ics">Unduh Kalender Jadwal (.ics)</a>
    <div class="card">
        <h2>1. Daftar Jadwal Bentrok (__TOTAL_CONFLICTS__)</h2>
        <table>
            <thead><tr><th>Pasangan Jadwal</th><th>Hari</th><th>Alasan Bentrok</th><th>Aksi</th></tr></thead>
            <tbody>__CONFLICT_ROWS__</tbody>
        </table>
        <div id="resolve-actions" style="margin-top:12px;"></div>
        <pre id="ai-output">Klik tombol "Saran AI & Resolve" pada tabel bentrok di atas...</pre>
    </div>
    <div class="card">
        <h2>2. Status KRS Terdampak (__TOTAL_KRS_REV__ REVISION)</h2>
        <ul>__KRS_ROWS__</ul>
    </div>
    <div class="card">
        <h2>3. Outbox Notification Log (Mahasiswa, Dosen, Admin)</h2>
        <ul>__LOG_ROWS__</ul>
    </div>
    <script>
        async function loadAI(jadwalId) {
            const out = document.getElementById('ai-output');
            const actions = document.getElementById('resolve-actions');
            out.textContent = 'Meminta 3 alternatif tersaring untuk Jadwal ID ' + jadwalId + '...';
            const res = await fetch('/api/ai-reschedule/' + jadwalId);
            const data = await res.json();
            out.textContent = JSON.stringify(data, null, 2);
            actions.innerHTML = '';
            data.alternatives.forEach(alt => {
                const btn = document.createElement('button');
                btn.textContent = 'Terapkan Opsi #' + alt.option_rank + ' (' + alt.hari + ' ' + alt.waktu_formatted + ')';
                btn.onclick = async () => {
                    await fetch('/api/jadwal/' + jadwalId, {
                        method: 'PUT',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            kelas_id: alt.kelas_id,
                            ruangan_id: alt.ruangan_id,
                            dosen_id: alt.dosen_id,
                            hari: alt.hari,
                            jam_mulai: alt.jam_mulai,
                            jam_selesai: alt.jam_selesai
                        })
                    });
                    location.reload();
                };
                actions.appendChild(btn);
            });
        }
    </script>
</body>
</html>"""
    return (
        html_template
        .replace("__TOTAL_CONFLICTS__", str(len(conflicts)))
        .replace("__CONFLICT_ROWS__", conflict_rows)
        .replace("__TOTAL_KRS_REV__", str(len(krs_rev)))
        .replace("__KRS_ROWS__", krs_rows)
        .replace("__LOG_ROWS__", log_rows)
    )