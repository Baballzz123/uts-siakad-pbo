from decimal import Decimal
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import Base, engine, get_db, SessionLocal
from models import Kelas, Mahasiswa, KRS, KRSDetail, GradeHistory
from presensi_port import PresensiPort, PresensiStub
from grade_service import GradeService, GradeError
from gpa_calculator import NilaiRepo, GPACalculator
from transcript_service import TranscriptService
from seed import seed_database

app = FastAPI(title="Sistem Nilai & Transkrip Akademik (Minggu 10)")


def get_presensi_port() -> PresensiPort:
    return PresensiStub(
        data_presensi={(1, "251636005"): Decimal("60.00")},
        default_persen=Decimal("90.00"),
    )


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


class InputNilaiRequest(BaseModel):
    dosen_id: str
    nilai_angka: Optional[float] = None
    nilai_huruf: Optional[str] = None
    alasan: Optional[str] = ""


@app.put("/api/kelas/{kelas_id}/nilai/{nim}")
def api_input_nilai(
    kelas_id: int,
    nim: str,
    payload: InputNilaiRequest,
    db: Session = Depends(get_db),
    presensi_port: PresensiPort = Depends(get_presensi_port),
):
    service = GradeService(db, presensi_port)
    try:
        hasil = service.input_nilai(
            kelas_id=kelas_id,
            nim=nim,
            dosen_id=payload.dosen_id,
            nilai_angka=payload.nilai_angka,
            nilai_huruf=payload.nilai_huruf,
            alasan=payload.alasan or "",
        )
        return {"status": "ok", "data": hasil}
    except GradeError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/api/mahasiswa/{nim}/ip")
def api_hitung_ip(nim: str, db: Session = Depends(get_db)):
    mhs = db.query(Mahasiswa).filter(Mahasiswa.nim == nim).first()
    if not mhs:
        raise HTTPException(status_code=404, detail=f"Mahasiswa {nim} tidak ditemukan.")

    repo = NilaiRepo(db)
    catatan = repo.ambil_nilai_mahasiswa(nim)
    semester_list = sorted({c.semester for c in catatan})

    return {
        "nim": mhs.nim,
        "nama": mhs.nama,
        "ips_per_semester": {
            sem: str(GPACalculator.hitung_ips(catatan, sem)) for sem in semester_list
        },
        "ipk": str(GPACalculator.hitung_ipk(catatan)),
        "rincian_nilai": [
            {
                "kode_mk": c.kode_mk,
                "nama_mk": c.nama_mk,
                "semester": c.semester,
                "sks": c.sks,
                "huruf": c.huruf,
                "bobot": str(c.bobot),
                "lulus": c.lulus,
            }
            for c in catatan
        ],
    }


@app.get("/api/mahasiswa/{nim}/history")
def api_grade_history(nim: str, db: Session = Depends(get_db)):
    rows = (
        db.query(GradeHistory)
        .join(KRSDetail, GradeHistory.krs_detail_id == KRSDetail.id)
        .join(KRS, KRSDetail.krs_id == KRS.id)
        .filter(KRS.nim == nim)
        .order_by(GradeHistory.id.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "krs_detail_id": r.krs_detail_id,
            "nilai_lama": r.nilai_lama,
            "nilai_baru": r.nilai_baru,
            "diubah_oleh": r.diubah_oleh,
            "alasan": r.alasan,
            "waktu_ubah": r.waktu_ubah.isoformat() if r.waktu_ubah else None,
        }
        for r in rows
    ]


@app.get("/api/mahasiswa/{nim}/transkrip")
def api_transkrip_json(nim: str, db: Session = Depends(get_db)):
    try:
        return TranscriptService(db).susun_transkrip(nim)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/mahasiswa/{nim}/transkrip.csv")
def api_transkrip_csv(nim: str, db: Session = Depends(get_db)):
    try:
        csv_content = TranscriptService(db).export_csv(nim)
        return Response(
            content=csv_content,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="transkrip_{nim}.csv"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/mahasiswa/{nim}/transkrip.pdf")
def api_transkrip_pdf(nim: str, db: Session = Depends(get_db)):
    try:
        pdf_bytes = TranscriptService(db).export_pdf(nim)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="transkrip_{nim}.pdf"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/dashboard/input-nilai")
def web_input_nilai(
    kelas_id: int = Form(...),
    nim: str = Form(...),
    dosen_id: str = Form(...),
    nilai_angka: str = Form(""),
    nilai_huruf: str = Form(""),
    alasan: str = Form(""),
    db: Session = Depends(get_db),
    presensi_port: PresensiPort = Depends(get_presensi_port),
):
    service = GradeService(db, presensi_port)
    angka_val = float(nilai_angka) if nilai_angka.strip() else None
    huruf_val = nilai_huruf.strip() if nilai_huruf.strip() else None
    try:
        service.input_nilai(kelas_id, nim, dosen_id, angka_val, huruf_val, alasan)
        return RedirectResponse(url=f"/dashboard?nim={nim}&msg=Nilai+tersimpan", status_code=303)
    except GradeError as e:
        return RedirectResponse(url=f"/dashboard?nim={nim}&err={str(e)}", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/dashboard?nim={nim}&err={str(e)}", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(nim: str = "251636004", msg: str = "", err: str = "", db: Session = Depends(get_db)):
    kelas_list = db.query(Kelas).all()
    catatan = NilaiRepo(db).ambil_nilai_mahasiswa(nim)
    semester_list = sorted({c.semester for c in catatan})
    ips_map = {sem: GPACalculator.hitung_ips(catatan, sem) for sem in semester_list}
    ipk = GPACalculator.hitung_ipk(catatan)
    transkrip = TranscriptService(db).susun_transkrip(nim)
    history_rows = (
        db.query(GradeHistory)
        .join(KRSDetail, GradeHistory.krs_detail_id == KRSDetail.id)
        .join(KRS, KRSDetail.krs_id == KRS.id)
        .filter(KRS.nim == nim)
        .order_by(GradeHistory.id.desc())
        .all()
    )

    alert = f"<p style='color:green'><b>{msg}</b></p>" if msg else (f"<p style='color:red'><b>{err}</b></p>" if err else "")
    opts = "".join(f'<option value="{k.id}">Kelas #{k.id} - {k.kode_mk} ({k.semester}) | {k.dosen_id}</option>' for k in kelas_list)
    rows = "".join(f"<tr><td>{c.semester}</td><td>{c.kode_mk}</td><td>{c.nama_mk}</td><td>{c.sks}</td><td>{c.huruf}</td><td>{c.bobot}</td><td>{'Lulus' if c.lulus else 'Tidak Lulus'}</td></tr>" for c in catatan)
    ips_txt = " | ".join(f"IPS {s}: <b>{v}</b>" for s, v in ips_map.items())
    hist_txt = "".join(f"<tr><td>{h.id}</td><td>{h.nilai_lama or '-'}</td><td>{h.nilai_baru}</td><td>{h.diubah_oleh}</td><td>{h.alasan or '-'}</td></tr>" for h in history_rows)

    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Nilai & Transkrip M10</title>
    <style>body{{font-family:sans-serif;max-width:900px;margin:20px auto;padding:0 16px}}table{{width:100%;border-collapse:collapse;margin:10px 0}}th,td{{border:1px solid #ccc;padding:8px;text-align:left}}.btn{{display:inline-block;padding:8px 12px;background:#2563eb;color:#fff;text-decoration:none;border-radius:4px;margin-right:6px}}</style>
    </head><body><h2>Sistem Nilai & Transkrip (Minggu 10)</h2>{alert}
    <form method="post" action="/dashboard/input-nilai">
      <select name="kelas_id">{opts}</select>
      <input name="nim" value="{nim}" placeholder="NIM" required>
      <input name="dosen_id" value="DSN01" placeholder="ID Dosen" required>
      <input type="number" step="0.01" name="nilai_angka" placeholder="Nilai Angka">
      <input name="nilai_huruf" placeholder="Atau Huruf (A/B/C)">
      <input name="alasan" placeholder="Alasan">
      <button type="submit">Simpan Nilai</button>
    </form><hr>
    <h3>Rekap Nilai & Transkrip (NIM: {nim})</h3>
    <p>{ips_txt} | IPK: <b>{ipk}</b> | SKS Lulus: <b>{transkrip['total_sks_lulus']}/{transkrip['total_sks_tempuh']}</b></p>
    <p><a class="btn" href="/api/mahasiswa/{nim}/transkrip.pdf" target="_blank">Unduh Transkrip PDF</a>
       <a class="btn" style="background:#059669" href="/api/mahasiswa/{nim}/transkrip.csv">Unduh Transkrip CSV</a></p>
    <table><tr><th>Semester</th><th>Kode</th><th>Mata Kuliah</th><th>SKS</th><th>Huruf</th><th>Bobot</th><th>Status</th></tr>{rows}</table>
    <h3>Riwayat Perubahan Nilai</h3>
    <table><tr><th>ID</th><th>Lama</th><th>Baru</th><th>Oleh</th><th>Alasan</th></tr>{hist_txt}</table>
    </body></html>"""