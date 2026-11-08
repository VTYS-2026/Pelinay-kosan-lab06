Kullanılan yapay zeka modeli:Claude
### Kullanılan İstem 
PostgreSQL veritabanımda girisler(giris_id,uye_id,salon_id,giris_zamani,sue_dk) adında 2 milyon satırlık bir tablo var. Çalıştırdığım 3 hedef sorgu şunlar:
1.SELECT COUNT(*), AVG (sure_dk) FROM girisler WHERE uye_id = 42;
2.SELECT COUNT(*) FROM girisler WHERE giris_zamani >= '2026-01-01 AND giris_zamani < '2026-02-01;
3.SELECT COUNT(*) FROM girisler WHERE salon_id = 3 AND giris_zamani >=
 '2026-06-01;
 Bu iş yükü için hangi indeksleri önerirsin?

 ### Yapay zekanın Önerileri
 1. `CREATE INDEX idx_girisler_uye_id ON girisler (uye_id) INCLUDE (sure_dk);`
2. `CREATE INDEX idx_girisler_giris_zamani ON girisler (giris_zamani);`
3. `CREATE INDEX idx_girisler_salon_zaman ON girisler (salon_id, giris_zamani);`

### Ölçümle doğrulama ve eleştiri
Claude S2 ve S3 için önerdiği indeksler benim görev 2 de tasarladığım indeks yapısyla birebir eşleşiyor S3 sorgusunda eşitlik filtresi olan salon_id sütunu başa, aralık filtresi olan giris_zamani sütununu sona koyması B-tree mantğına tamamen uygun.
Claude fark yarattığı kısımsa S1 sorgusu için INCLUDE (sue_dk) kullanarak Index_Only Scan elde etme tavsiyesiydi.Bu sorhuyu girince tabloya hiç gitmeden yalnızda indeks üzerinden sonucu hesapladığını gördüm.