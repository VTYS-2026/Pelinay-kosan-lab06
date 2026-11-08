-- S1 için tek sütunlu indeks
CREATE INDEX idx_girisler_uye ON girisler(uye_id);

-- S2 için tek sütunlu zaman indeksi
CREATE INDEX idx_girisler_zamani ON girisler(giris_zamani);

-- S3 için bileşik indeks (Eşitlik koşulu öne, aralık koşulu sona)
CREATE INDEX idx_girisler_salon_zaman ON girisler(salon_id, giris_zamani);