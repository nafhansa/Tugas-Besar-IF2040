# Dataset & Database `basdat_movie` - Tugas Besar IF2040

Repositori ini berisi skema database streaming film/serial TV lengkap dengan tools generator data dummy, model relasional, dan skrip tambah/kelola konten.

---

## 📂 Daftar File & Fungsi

### 📊 Database Schema & Model
| File | Deskripsi |
|------|-----------|
| `basdat_movie_schema.sql` | Skema lengkap database `basdat_movie` dengan 17 tabel (entities + relasi) |
| `basdat_movie_relational_model.puml` | Diagram ER relasional (PlantUML format, tema biru-putih) — bisa di-render di VS Code |

### 📝 Data Dummy & Generator
| File | Deskripsi |
|------|-----------|
| `generate_fixtures.py` | Skrip Python generator data dummy (≥150 baris per tabel untuk data utama) |
| `basdat_movie_fixtures.sql` | File SQL hasil generate (siap di-import ke database) |
| `basdat_movie_real_data.sql` | Data dummy alternatif (dari scrape/real source) |
| `generate_real_data.py` | Skrip scraper untuk mendapatkan data real film dari API/website |

### 🎬 Fitur Tambahan
| File | Deskripsi |
|------|-----------|
| `adding_movie_tv.py` | Skrip Python untuk menambah/update film & serial TV ke database |
| `cek_api.py` | Utility untuk test koneksi database & jalankan query |

### 📂 Direktori
- `out/` — Folder untuk output export (gambar diagram, laporan, dll)

---

## 🏗️ Skema Database

### Entitas Utama (Strong Entity)
- **Paket_Langganan** (5 baris) — Jenis paket langganan: Basic, Standard, Premium, Mobile, Family
- **Kartu_Kredit** (150 baris) — Data kartu kredit pelanggan
- **Pelanggan** (150 baris) — Data pelanggan utama
- **Konten** (300 baris) — Daftar semua film & serial TV
  - **Film** (150 baris) — Film dengan durasi & sutradara
  - **Serial_TV** (150 baris) — Serial dengan total season

### Transaksi & Aktivitas
- **Transaksi** (150 baris) — Pembayaran langganan pelanggan
- **Menonton** (150 baris) — Riwayat menonton per profil
- **Rating** (150 baris) — Rating & komentar per profil untuk konten

### Weak Entity & Associative
- **Profil** (150 baris) — Profil dalam satu akun pelanggan (1 profil per pelanggan di fixtures)
- **Episode** (300 baris) — Episode serial TV (2 per serial di fixtures)

### Detail Konten
- **Aktor** (150 baris) — Database pemain film
- **Genre** (150 baris) — Kategori genre film/serial
- **Audio** (458 baris) — Pilihan bahasa audio per konten (1–2 per konten)
- **Subtitle** (454 baris) — Pilihan bahasa subtitle per konten (1–2 per konten)

### Relasi Many-to-Many
- **Genre_Konten** (609 baris) — Relasi genre dengan konten (1–3 genre per konten)
- **Peran** (200 baris) — Relasi aktor dengan konten (peran yang dimainkan)

---

## 📊 Verifikasi Jumlah Data

Hasil count INSERT dari `basdat_movie_fixtures.sql`:

```
Aktor:                150 ✓
Audio:                458 (banyak karena multi-bahasa)
Episode:              300 (2 per serial)
Film:                 150 ✓
Genre:                150 ✓
Genre_Konten:         609 (1–3 genre per konten)
Kartu_Kredit:         150 ✓
Konten:               300 (150 Film + 150 Serial_TV)
Menonton:             150 ✓
Paket_Langganan:      5 (realistic: Basic, Standard, Premium, Mobile, Family)
Pelanggan:            150 ✓
Peran:                200 (relasi aktor-konten, ~1.3 per aktor)
Profil:               150 ✓ (1 per pelanggan)
Rating:               150 ✓
Serial_TV:            150 ✓
Subtitle:             454 (banyak karena multi-bahasa)
Transaksi:            150 ✓
```

### Penjelasan Tabel Khusus

**Paket_Langganan (5 baris):**
- Tabel referensi kecil untuk jenis paket langganan.
- Realistis hanya 5 paket; tidak masuk akal membuat 150 variasi unik.
- Semua pelanggan di fixtures memakai salah satu dari 5 paket ini.

**Audio, Subtitle, Genre_Konten:**
- Lebih dari 150 karena relasi many-to-many.
- Audio/Subtitle: 1–2 bahasa per konten × 300 konten = ~450.
- Genre_Konten: 1–3 genre per konten × 300 konten = ~609.

---

## 🚀 Cara Menggunakan

### 1. Import Skema Database

Pastikan MySQL/MariaDB sudah terinstall.

```bash
mysql -u <user> -p < basdat_movie_schema.sql
```

Masukkan password saat diminta. Database `basdat_movie` akan tercipta kosong.

Alternatif (MariaDB):
```bash
mariadb -u <user> -p < basdat_movie_schema.sql
```

### 2. Import Data Dummy

```bash
mysql -u <user> -p basdat_movie < basdat_movie_fixtures.sql
```

Atau dengan real data:
```bash
mysql -u <user> -p basdat_movie < basdat_movie_real_data.sql
```

### 3. Regenerate Data Dummy (Opsional)

Jika ingin membuat dataset baru dengan seed berbeda:

```bash
python3 generate_fixtures.py
```

Ini akan menimpa `basdat_movie_fixtures.sql` dengan data dummy baru.

### 4. Generate Real Data (Opsional)

```bash
python3 generate_real_data.py
```

Skrip akan scrape data dari sumber eksternal dan generate `basdat_movie_real_data.sql`.

### 5. Menambah Film/Serial TV

```bash
python3 adding_movie_tv.py
```

Skrip interaktif untuk menambah film atau serial TV baru ke database.

### 6. Test Koneksi Database

```bash
python3 cek_api.py
```

Utility untuk test koneksi dan jalankan query database.

---

## 📈 Visualisasi Model Relasional

File `basdat_movie_relational_model.puml` adalah diagram ER dalam format PlantUML dengan tema biru-putih.

### Preview di VS Code

1. Pastikan extension **PlantUML** (jebbs.plantuml) sudah terinstall.
2. Buka file `basdat_movie_relational_model.puml`.
3. Tekan **Alt+D** atau gunakan Command Palette:
   ```
   Ctrl+Shift+P → "PlantUML: Preview Current Diagram"
   ```
4. Preview akan muncul di panel samping.

### Export ke Gambar

Dengan PlantUML extension di VS Code:

1. Command Palette:
   ```
   Ctrl+Shift+P → "PlantUML: Export Current Diagram"
   ```
2. Pilih format: PNG, SVG, PDF.
3. Gambar akan disimpan di folder yang sama (bisa atur "plantuml.exportOutDir" di Settings).

### Offline Render

Gunakan PlantUML JAR atau Docker:

```bash
# Install Graphviz & Java (Linux/Ubuntu)
sudo apt-get install graphviz default-jre

# Render .puml ke PNG
java -jar plantuml.jar basdat_movie_relational_model.puml
```

---

## 🔧 Troubleshooting

### Error Foreign Key saat Import

**Masalah:** Foreign key constraint fails saat import `basdat_movie_fixtures.sql`.

**Solusi:**
1. Pastikan skema sudah diimport terlebih dahulu: `basdat_movie_schema.sql`.
2. Pastikan database aktif adalah `basdat_movie`:
   ```sql
   USE basdat_movie;
   ```
3. Pastikan urutan insert sesuai (parent dulu, child kemudian).

### Conflict Primary Key

**Masalah:** "Duplicate entry" saat menjalankan ulang import.

**Solusi:**
- Drop database lama dan import ulang:
  ```sql
  DROP DATABASE IF EXISTS basdat_movie;
  ```
  Lalu jalankan import skema & fixtures lagi.
- Atau clear data tanpa drop database:
  ```sql
  TRUNCATE TABLE Rating;
  TRUNCATE TABLE Menonton;
  -- dst untuk semua tabel
  ```

### Import Lamban untuk Dataset Besar

**Masalah:** Import terasa lambat dengan 3000+ INSERT statements.

**Solusi:** Matikan foreign_key_checks sementara:

```sql
SET FOREIGN_KEY_CHECKS=0;
-- source /path/to/basdat_movie_fixtures.sql;
SET FOREIGN_KEY_CHECKS=1;
```

Atau gunakan flag di command line:

```bash
mysql -u <user> -p basdat_movie \
  --disable-local-infile=0 \
  --max_allowed_packet=512M \
  < basdat_movie_fixtures.sql
```

### PlantUML Preview Tidak Muncul

**Masalah:** "dot not found" atau preview blank.

**Solusi:**
1. Install Graphviz:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install graphviz
   
   # macOS
   brew install graphviz
   ```
2. Install Java JRE:
   ```bash
   sudo apt-get install default-jre
   ```
3. Restart VS Code.
4. Alternatif: Settings PlantUML → Render → pilih "PlantUMLServer" (online).

---

## 💡 Ide Pengembangan Lanjutan

- **Lebih Banyak Episode:** Ubah loop Episode di `generate_fixtures.py` untuk 5–10 episode per season.
- **Faker Library:** Ganti random string dengan nama/email realistis menggunakan `pip install faker`.
- **Stress Testing:** Buat 1000+ pelanggan dan 10000+ transaksi untuk benchmark database.
- **REST API:** Tambah Flask/FastAPI untuk access database via HTTP endpoint.
- **Dashboard:** Buat UI dashboard menggunakan Streamlit atau Tableau untuk visualisasi analytics.
- **Automated Tests:** Tambah test suite untuk validasi schema & data integrity.

---

## 📝 Changelog

### v1.0 (Current - November 2024)
- ✅ Skema database `basdat_movie` dengan 17 tabel
- ✅ Generator data dummy Python (`generate_fixtures.py`)
- ✅ ≥150 baris data untuk tabel utama
- ✅ Diagram ER relasional PlantUML (tema biru-putih)
- ✅ Skrip tambahan (adding_movie_tv.py, cek_api.py, generate_real_data.py)
- ✅ README lengkap dengan instruksi & troubleshooting

---

## 👥 Contributors

- **Nafhan Shafy Aulia** — Database schema, generator, & documentation

---

## 📄 Catatan Penting

- Nama database di skema: **`basdat_movie`** (bukan `basdar_movie`).
- Pesan "Deprecated program name" saat pakai `mysql` hanya warning MariaDB; fungsionalitas tetap berjalan.
- Foreign key constraints aktif — pastikan import skema dulu sebelum data.
- Semua timestamp menggunakan format datetime standard SQL.
- Total ~3863 statements SQL dalam fixtures.sql (termasuk skema + 3800+ data insert).

---

**Generated:** November 2024  
**Repository:** Tugas-Besar-IF2040  
**Branch:** main

---