#!/usr/bin/env python3
"""Föy 06 — Otomatik Değerlendirici

GitHub Actions içinde çalışır. Öğrencinin numarasından üretilen KİŞİYE ÖZEL
büyük tabloyu (2,0–2,5M satır) CI ortamında yeniden kurar; setseed()
sayesinde öğrencinin makinesindekiyle birebir aynı veri oluşur. Ardından:

  * Görev 1'in ölçüm transkriptinde, ancak sorguları gerçekten çalıştırınca
    bilinebilecek kişiye özel sayım değerlerini arar.
  * Görev 2'nin CREATE INDEX'lerini çalıştırıp indekslenen sütunları
    pg_index üzerinden doğrular.
  * Görev 3 için hedef sorguların planlarını EXPLAIN ile alır ve
    öğrencinin indekslerinin GERÇEKTEN kullanıldığını denetler.

Bu haftanın hedef sorguları föyde açıkça verildiği için referans sorgular
bu dosyada görünür; ölçüm, indeks tasarımı ve plan yorumu öğrencinindir.
"""
import os
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "veri"))
from uret import uret, SABLON  # noqa: E402

try:
    import psycopg
except ImportError:
    print("HATA: psycopg kurulu değil (pip install 'psycopg[binary]').")
    sys.exit(2)

SONUCLAR = []

# Föydeki üç hedef sorgu (birebir aynı)
S1 = "SELECT COUNT(*), AVG(sure_dk) FROM girisler WHERE uye_id = 42"
S2 = ("SELECT COUNT(*) FROM girisler WHERE giris_zamani >= '2026-01-01' "
      "AND giris_zamani < '2026-02-01'")
S3 = ("SELECT COUNT(*) FROM girisler WHERE salon_id = 3 "
      "AND giris_zamani >= '2026-06-01'")


def kaydet(gorev, alinan, tam, mesaj):
    SONUCLAR.append((gorev, alinan, tam, mesaj))
    durum = "✓" if alinan == tam else ("~" if alinan > 0 else "✗")
    print(f"[{durum}] {gorev}: {alinan}/{tam} — {mesaj}")


def oku(yol):
    p = KOK / yol
    # is_file(): ogrenci bazen dosya yerine AYNI ADLA KLASOR olusturuyor
    # (ornegin "sonuc/g1.txt/g1.txt"). exists() bunu dosya sanip read_bytes()
    # ile cokuyor ve TUM degerlendirme sifirlaniyordu.
    if not p.is_file():
        return None
    try:
        ham = p.read_bytes()
    except OSError:
        return None
    # Windows'ta PowerShell'in ">" yonlendirmesi UTF-16 yazar; Not Defteri de
    # UTF-8'e BOM ekler. Bunlari cozmezsek ogrencinin dogru cikti dosyasi
    # taninmaz ve haksiz puan kaybi olur.
    if ham[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return ham.decode("utf-16", errors="replace")
    return ham.decode("utf-8-sig", errors="replace")

def sql_kodu(metin):
    """SQL metninden yorumlari atar.

    Sablon dosyalarinin KENDI yorumlarinda "CREATE TABLE komutunuzu yazin"
    gibi ifadeler gectigi icin, ham metinde anahtar kelime aramak bos teslimi
    gecerli sayiyordu. Denetimler bu fonksiyonun ciktisi uzerinde yapilir.
    """
    metin = re.sub(r"/\*.*?\*/", " ", metin or "", flags=re.S)
    return re.sub("--.*", " ", metin)


def baglanti():
    return psycopg.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        user=os.environ.get("PGUSER", "vtys"),
        password=os.environ.get("PGPASSWORD", "vtys2026"),
        dbname=os.environ.get("PGDATABASE", "vtysdb"),
        autocommit=True,
    )


def ogrno_al():
    icerik = oku("ogrno.txt")
    if icerik is None:
        return None
    icerik = icerik.strip()
    return icerik if icerik.isdigit() else None


def sayi_var(metin, deger):
    return re.search(rf"(?<!\d){deger}(?!\d)", metin) is not None


def tablo_kur(con, ogrno):
    print("Büyük tablo CI ortamında kuruluyor (30–60 sn sürebilir)...")
    con.execute(SABLON.format(**uret(ogrno)))


# ------------------------------------------------------------- Görev 1
def kontrol_g1(con):
    n1 = con.execute(S1).fetchone()[0]
    n2 = con.execute(S2).fetchone()[0]
    n3 = con.execute(S3).fetchone()[0]

    icerik = oku("sonuc/g1.txt") or ""
    puan = 0
    mesajlar = []
    if not icerik:
        kaydet("Görev 1 (Ölçüm)", 0, 20, "sonuc/g1.txt bulunamadı.")
        return
    bulunan = sum(1 for n in (n1, n2, n3) if sayi_var(icerik, n))
    puan += 4 * bulunan
    if bulunan < 3:
        mesajlar.append(f"Üç sorgunun sayım sonucundan {bulunan}/3'ü transkriptte "
                        "bulundu — sorguları kendi verinizde çalıştırdınız mı?")
    if "Seq Scan" in icerik:
        puan += 4
    else:
        mesajlar.append("Transkriptte 'Seq Scan' görünmüyor (indekssiz plan bekleniyor).")
    if "Execution Time" in icerik:
        puan += 4
    else:
        mesajlar.append("EXPLAIN ANALYZE çıktısı ('Execution Time') eksik.")
    kaydet("Görev 1 (Ölçüm)", puan, 20, " ".join(mesajlar) or "Ölçüm kanıtı tam.")


# ------------------------------------------------------------- Görev 2
def kontrol_g2(con):
    sql = oku("sql/g2_indeksler.sql")
    if not sql or "CREATE" not in sql_kodu(sql).upper():
        kaydet("Görev 2 (İndeksler)", 0, 30,
               "sql/g2_indeksler.sql bulunamadı veya CREATE INDEX içermiyor.")
        return False
    try:
        con.execute(sql)
    except Exception as e:
        kaydet("Görev 2 (İndeksler)", 0, 30, f"Çalıştırılamadı: {e}")
        return False

    satirlar = con.execute("""
        SELECT i.relname, array_agg(a.attname ORDER BY x.ordinality)
        FROM pg_class t
        JOIN pg_index ix ON t.oid = ix.indrelid
        JOIN pg_class i ON i.oid = ix.indexrelid
        JOIN unnest(ix.indkey) WITH ORDINALITY x(attnum, ordinality) ON true
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = x.attnum
        WHERE t.relname = 'girisler' AND NOT ix.indisprimary
        GROUP BY i.relname""").fetchall()
    kolonlar = {tuple(r[1]) for r in satirlar}

    def ile_basliyor(sutun):
        """Bu sutunun ILK sirada oldugu herhangi bir indeks var mi?

        S1'i hizlandiran sey uye_id'nin indeksin ILK sutunu olmasidir:
        (uye_id) de (uye_id, sure_dk) de isi gorur, ikincisi AVG'yi de
        kapsadigi icin daha iyidir. Foyun savunma sorusu ogrenciyi zaten
        o kapsayici indekse yonlendiriyor ("AVG(sure_dk) yuzunden
        planlayici neden yine tabloya gitti? Hangi indeks bunu da ortadan
        kaldirirdi?"); dogru cevabi UYGULAYAN ogrenci puan kaybetmemeli.
        Ayni mantik S2 icin giris_zamani'nda da gecerlidir.
        """
        return any(k and k[0] == sutun for k in kolonlar)

    puan = 0
    mesajlar = []
    if ile_basliyor("uye_id"):
        puan += 10
    else:
        mesajlar.append("uye_id ile başlayan bir indeks yok.")
    if ile_basliyor("giris_zamani"):
        puan += 10
    else:
        mesajlar.append("giris_zamani ile başlayan bir indeks yok.")
    if ("salon_id", "giris_zamani") in kolonlar:
        puan += 10
    elif ("giris_zamani", "salon_id") in kolonlar:
        puan += 5
        mesajlar.append("Bileşik indeks var ama sütun sırası ters: eşitlik "
                        "koşulu (salon_id) önce gelmeli — yarım puan.")
    else:
        mesajlar.append("(salon_id, giris_zamani) bileşik indeksi yok.")
    kaydet("Görev 2 (İndeksler)", puan, 30,
           " ".join(mesajlar) or "Üç indeks de doğru tasarlanmış.")
    return True


# ------------------------------------------------------------- Görev 3
def kontrol_g3(con, indeksler_var):
    puan = 0
    mesajlar = []
    if indeksler_var:
        for ad, q in (("S1", S1), ("S2", S2), ("S3", S3)):
            plan = str(con.execute("EXPLAIN (FORMAT JSON) " + q).fetchone()[0])
            if "Index" in plan:
                puan += 6
            else:
                mesajlar.append(f"{ad} hâlâ indeks kullanmıyor.")
    else:
        mesajlar.append("İndeksler kurulamadığı için plan denetimi yapılamadı.")

    icerik = oku("sonuc/g3.txt") or ""
    if icerik and "Index" in icerik and "Execution Time" in icerik:
        puan += 7
    elif icerik:
        mesajlar.append("g3.txt'de indeksli plan ('Index ... Scan') ve "
                        "'Execution Time' birlikte görünmeli.")
    else:
        mesajlar.append("sonuc/g3.txt bulunamadı.")
    kaydet("Görev 3 (Plan Kanıtı)", puan, 25,
           " ".join(mesajlar) or "Üç sorgu da indeks kullanıyor; ölçüm belgelenmiş.")


# ------------------------------------------------------------- Görev 4
def kontrol_g4():
    icerik = oku("sonuc/g4.txt") or ""
    puan = 0
    mesajlar = []
    if not icerik:
        kaydet("Görev 4 (Ödünleşim)", 0, 15, "sonuc/g4.txt bulunamadı.")
        return
    if re.search(r"\d+\s*(MB|kB|GB)", icerik):
        puan += 8
    else:
        mesajlar.append("Boyut ölçümleri (MB/kB değerleri) görünmüyor.")
    if re.search(r"Time:|Execution Time", icerik) and len(icerik.strip()) > 250:
        puan += 7
    else:
        mesajlar.append("Ekleme süresi ölçümü (\\timing çıktısı) ya da yorum eksik.")
    kaydet("Görev 4 (Ödünleşim)", puan, 15, " ".join(mesajlar) or "Ödünleşim kanıtı tam.")


def ogrenci_metni(markdown):
    """Markdown'dan kod bloklarini atip ogrencinin KENDI yazdigi metni birakir.

    Yapay zekanin urettigi SQL'i yapistirip tek satir elestiri yazmayan
    teslimler yalnizca uzunluga bakildiginda esigi gecip tam puan aliyordu
    (gercek teslimlerde tespit edildi). Puan artik duz metne gore verilir.
    """
    m = markdown or ""
    m = re.sub(r"```.*?```", " ", m, flags=re.S)
    m = re.sub(r"```.*", " ", m, flags=re.S)
    m = re.sub(r"^\s{4,}\S.*$", " ", m, flags=re.M)
    m = re.sub(r"`[^`]*`", " ", m)
    return re.sub(r"\s+", " ", m).strip()


def kontrol_ai():
    icerik = oku("sonuc/ai_elestiri.md")
    if not icerik or len(ogrenci_metni(icerik)) < 300:
        kaydet("AI Köşesi", 0, 10,
               "sonuc/ai_elestiri.md yok ya da eleştiri metniniz 300 karakterden kısa "
               "(yapıştırdığınız kod blokları sayılmaz). Föyde istenen iki "
               "somut eleştiriyi yazdığınızda bu uzunluk zaten aşılır "
               "(içerik ayrıca asistan tarafından okunur).")
    else:
        kaydet("AI Köşesi", 10, 10,
               "Dosya teslim edildi (isabet puanı asistan değerlendirmesiyle kesinleşir).")


# ------------------------------------------------------------- ana akış
def main():
    print("=" * 64)
    print("Föy 06 — Otomatik Değerlendirme")
    print("=" * 64)

    ogrno = ogrno_al()
    if not ogrno:
        print("HATA: ogrno.txt bulunamadı ya da geçerli bir numara içermiyor.")
        sys.exit(1)
    print(f"Öğrenci no: {ogrno} (veri seti bu numaradan yeniden üretiliyor)\n")

    with baglanti() as con:
        tablo_kur(con, ogrno)
        kontrol_g1(con)
        indeksler_var = kontrol_g2(con)
        kontrol_g3(con, indeksler_var)
    kontrol_g4()
    kontrol_ai()

    alinan = sum(s[1] for s in SONUCLAR)
    tam = sum(s[2] for s in SONUCLAR)
    print("\n" + "=" * 64)
    print(f"TOPLAM (otomatik kontrol edilen kısım): {alinan}/{tam}")
    print("Transkript yorumları ve AI köşesi asistan tarafından")
    print("ayrıca değerlendirilir.")
    print("=" * 64)

    ozet = os.environ.get("GITHUB_STEP_SUMMARY")
    if ozet:
        with open(ozet, "a", encoding="utf-8") as f:
            f.write("## Föy 06 — Otomatik Değerlendirme\n\n")
            f.write("| Bileşen | Puan | Açıklama |\n|---|---|---|\n")
            for gorev, a, tp, m in SONUCLAR:
                f.write(f"| {gorev} | {a}/{tp} | {m} |\n")
            f.write(f"| **Toplam** | **{alinan}/{tam}** | |\n")

    sys.exit(0 if alinan == tam else 1)


if __name__ == "__main__":
    main()
