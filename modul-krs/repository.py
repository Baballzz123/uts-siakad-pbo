from sqlalchemy.orm import Session
from sqlalchemy import text

class KRSRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_unmet_prerequisites(self, nim: str, target_kode_mk: str) -> list[dict]:
        """
        Query NOT EXISTS + bobot untuk mencari mata kuliah prasyarat
        yang belum lulus atau bobot nilainya di bawah syarat minimal.
        """
        query = text("""
            SELECT p.kode_mk_syarat, p.min_huruf
            FROM prerequisite p
            JOIN skala_nilai sn_min ON p.min_huruf = sn_min.huruf
            WHERE p.kode_mk = :target_kode_mk
              AND NOT EXISTS (
                  SELECT 1
                  FROM riwayat_nilai rn
                  JOIN skala_nilai sn_mhs ON rn.nilai_huruf = sn_mhs.huruf
                  WHERE rn.nim = :nim
                    AND rn.kode_mk = p.kode_mk_syarat
                    AND sn_mhs.bobot >= sn_min.bobot
              )
        """)
        result = self.db.execute(
            query, {"nim": nim, "target_kode_mk": target_kode_mk}
        ).fetchall()

        return [{"kode_mk_syarat": row[0], "min_huruf": row[1]} for row in result]