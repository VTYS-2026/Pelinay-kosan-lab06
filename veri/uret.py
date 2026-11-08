#!/usr/bin/env python3
"""Kişiye özel veri üreteci — Föy 06 (FıratFit turnike kayıtları)

Kullanım:
    python3 veri/uret.py <ogrenci_no>

Bu hafta CSV yok: milyonlarca satırı dosyayla taşımak yerine, size özel
parametrelerle (satır sayısı ve rastgelelik tohumu) donatılmış bir kurulum
SQL'i üretilir: veri/buyuk_tablo_hazir.sql. PostgreSQL'in setseed()
fonksiyonu sayesinde aynı öğrenci numarası her makinede AYNI veriyi üretir.
"""
import sys
from pathlib import Path


def uret(ogrno: str):
    """Öğrenci numarasından büyük tablo parametrelerini türetir."""
    tohum = int(ogrno)
    return {
        "satir_sayisi": 2_000_000 + tohum % 500_000,   # 2,0M – 2,5M satır
        "tohum": (tohum % 999_983) / 1_000_000,        # setseed için 0..1
    }


SABLON = """-- =====================================================
-- Föy 06 — Büyük tablonun kurulumu (bu dosya uret.py tarafından üretildi)
-- Çalıştırma:
--   docker exec -i vtys-postgres psql -U vtys -d vtysdb < veri/buyuk_tablo_hazir.sql
-- Kurulum donanıma göre 30–90 saniye sürebilir; normaldir.
-- =====================================================
DROP TABLE IF EXISTS girisler;

CREATE TABLE girisler (
    giris_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    uye_id       INTEGER   NOT NULL,
    salon_id     INTEGER   NOT NULL,
    giris_zamani TIMESTAMP NOT NULL,
    sure_dk      INTEGER   NOT NULL
);

SELECT setseed({tohum});

INSERT INTO girisler (uye_id, salon_id, giris_zamani, sure_dk)
SELECT (random() * 199)::int + 1,
       (random() * 5)::int + 1,
       timestamp '2023-01-01'
         + random() * (timestamp '2026-08-31' - timestamp '2023-01-01'),
       (random() * 170)::int + 10
FROM generate_series(1, {satir_sayisi});

ANALYZE girisler;

SELECT COUNT(*) AS toplam_satir FROM girisler;
"""


def main():
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print("Kullanım: python3 veri/uret.py <ogrenci_no>")
        print("Örnek   : python3 veri/uret.py 230541001")
        sys.exit(1)

    p = uret(sys.argv[1])
    hedef = Path(__file__).resolve().parent / "buyuk_tablo_hazir.sql"
    hedef.write_text(SABLON.format(**p), encoding="utf-8")
    print(f"Üretildi: {hedef}")
    print(f"  Satır sayısı : {p['satir_sayisi']:,} (size özel)")
    print("Kurulum için:")
    print("  docker exec -i vtys-postgres psql -U vtys -d vtysdb "
          "< veri/buyuk_tablo_hazir.sql")


if __name__ == "__main__":
    main()
