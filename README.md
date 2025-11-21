# 🎬 Streaming Database - `basdat_movie`
## Tugas Besar PBD - Kelompok IF2040

Database streaming film & serial TV dengan 17 tabel, 1000+ data, dan dokumentasi lengkap.

---

## � File Utama

| File | Deskripsi |
|------|-----------|
| `basdat_movie_schema.sql` | Skema database (17 tabel dengan FK & constraints) |
| `basdat_movie.sql` | Data gabungan (1000+ insert statements) |
| `README.md` | Dokumentasi (file ini) |
| `scrapper/` | Folder skrip scraper untuk data real (opsional) |

## 🗄️ 17 Tabel Database

**Strong Entities:**
- Paket_Langganan | Pelanggan | Konten | Aktor | Genre

**Specialization:**
- Film | Serial_TV | Episode

**Weak Entity:**
- Profil

**Relasi Many-to-Many:**
- Genre_Konten | Peran | Audio | Subtitle

**Transaksi & Activity:**
- Transaksi | Menonton | Rating

**Support:**
- Kartu_Kredit

---

## � Cara Setup

### 1. Import Schema
```bash
mysql -u root -p < basdat_movie_schema.sql
```

### 2. Import Data
```bash
mysql -u root -p basdat_movie < basdat_movie.sql
```

### Alternatif (MariaDB)
```bash
mariadb -u root -p < basdat_movie_schema.sql
mariadb -u root -p basdat_movie < basdat_movie.sql
```

---

## ✅ Verifikasi Data

Jalankan query di MySQL:
```sql
USE basdat_movie;

SELECT 
    'Aktor' AS table_name, COUNT(*) AS total FROM Aktor
UNION ALL SELECT 'Audio', COUNT(*) FROM Audio
UNION ALL SELECT 'Episode', COUNT(*) FROM Episode
UNION ALL SELECT 'Film', COUNT(*) FROM Film
UNION ALL SELECT 'Genre', COUNT(*) FROM Genre
UNION ALL SELECT 'Genre_Konten', COUNT(*) FROM Genre_Konten
UNION ALL SELECT 'Kartu_Kredit', COUNT(*) FROM Kartu_Kredit
UNION ALL SELECT 'Konten', COUNT(*) FROM Konten
UNION ALL SELECT 'Menonton', COUNT(*) FROM Menonton
UNION ALL SELECT 'Paket_Langganan', COUNT(*) FROM Paket_Langganan
UNION ALL SELECT 'Pelanggan', COUNT(*) FROM Pelanggan
UNION ALL SELECT 'Peran', COUNT(*) FROM Peran
UNION ALL SELECT 'Profil', COUNT(*) FROM Profil
UNION ALL SELECT 'Rating', COUNT(*) FROM Rating
UNION ALL SELECT 'Serial_TV', COUNT(*) FROM Serial_TV
UNION ALL SELECT 'Subtitle', COUNT(*) FROM Subtitle
UNION ALL SELECT 'Transaksi', COUNT(*) FROM Transaksi
ORDER BY total DESC;
```

---