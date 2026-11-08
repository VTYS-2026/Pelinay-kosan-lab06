# Föy 06 — Transaction Yönetimi ve İndeksleme

Modern Veritabanı Yönetim Sistemleri — Laboratuvar teslim deposu.
Görevlerin tam açıklaması **Föy 06 PDF**'indedir; bu dosya kısa bir hatırlatmadır.

## Bu hafta

FıratFit'in turnike sistemi üç buçuk yıldır her girişi kaydediyor:
**girisler** tablosu, size özel 2,0–2,5 milyon satır. Yönetim raporların
yavaşlığından şikâyetçi. Göreviniz: yavaşlığı `EXPLAIN ANALYZE` ile ölçmek,
doğru indeksleri tasarlamak ve kazancı kanıtlamak — bedavaya gelmediğini de
(yazma maliyeti, disk boyutu) göstererek.

## Hızlı başlangıç

```bash
echo "230541001" > ogrno.txt              # kendi numaranız
docker compose up -d
python3 veri/uret.py 230541001            # kendi numaranız → kurulum SQL'i
docker exec -i vtys-postgres psql -U vtys -d vtysdb < veri/buyuk_tablo_hazir.sql
docker exec -it vtys-postgres psql -U vtys -d vtysdb
```

Büyük tablonun kurulumu donanıma göre **30–90 saniye** sürebilir; normaldir.
CSV yok: veri, size özel tohumla (`setseed`) doğrudan sunucuda üretilir ve
her makinede birebir aynı çıkar.

## Depo yapısı

| Yol | Ne |
|---|---|
| `ogrno.txt` | Öğrenci numaranız (ilk iş: doldurun) |
| `veri/uret.py` | Size özel kurulum SQL'ini üretir |
| `sql/g2_indeksler.sql` | Görev 2 — üç CREATE INDEX komutunuz |
| `sonuc/g1.txt` | Görev 1 — indekssiz ölçüm transkripti |
| `sonuc/g3.txt` | Görev 3 — indeksli ölçüm transkripti + yorum |
| `sonuc/g4.txt` | Görev 4 — boyut ve yazma maliyeti ölçümleri |

Değerlendirici tabloyu CI'da sizin tohumunuzla yeniden kurar: transkriptteki
sayım değerleri size özeldir ve indekslerinizin hedef sorgular tarafından
**gerçekten kullanılıp kullanılmadığı** plan üzerinden denetlenir.


## Push etmeden önce kendinizi kontrol edin

Değerlendiriciyi kendi bilgisayarınızda çalıştırabilirsiniz — GitHub'daki ile
**aynı dosya, aynı puan**:

```bash
docker compose run --rm kontrol
```

Ekrana görev görev puanınız ve eksikleriniz düşer. İlk çalıştırma birkaç
saniye sürer, sonrakiler ~2 saniye. Ayrıca bir şey kurmanız gerekmez; Docker
zaten kurulu.

**Önce burada tam puan alın, sonra push edin.** Her push GitHub'da sınıfın
ortak Actions kotasından dakika harcar; deneme-yanılmayı buraya taşırsanız
kota dönem sonuna kadar yeter.

## Teslim

```bash
git add ogrno.txt sql/ sonuc/
git commit -m "Foy 06 teslimi"
git push
```
