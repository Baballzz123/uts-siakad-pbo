from sqlalchemy import text
from database import engine

explain_sql = text("""
EXPLAIN QUERY PLAN
SELECT p.kode_mk_syarat, p.min_huruf
FROM prerequisite p
JOIN skala_nilai sn_min ON p.min_huruf = sn_min.huruf
WHERE p.kode_mk = 'IF301'
  AND NOT EXISTS (
      SELECT 1
      FROM riwayat_nilai rn
      JOIN skala_nilai sn_mhs ON rn.nilai_huruf = sn_mhs.huruf
      WHERE rn.nim = '251636004'
        AND rn.kode_mk = p.kode_mk_syarat
        AND sn_mhs.bobot >= sn_min.bobot
  );
""")

with engine.connect() as conn:
    rows = conn.execute(explain_sql).fetchall()
    print("=== HASIL EXPLAIN QUERY PLAN ===")
    for row in rows:
        print(row)