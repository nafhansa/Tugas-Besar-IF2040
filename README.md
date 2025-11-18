# Tugas-Besar-IF2040
# Dataset Dummy Skema `basdat_movie`

## Ringkasan
- File skema basis data: `basdar_movie_schema.sql` (membuat database `basdat_movie`).
- Skrip generator data dummy: `generate_fixtures.py`.
- File hasil generasi data dummy: `basdar_movie_fixtures.sql`.

## Skema (Entity Utama)
Tabel utama meliputi: `Paket_Langganan`, `Kartu_Kredit`, `Pelanggan`, `Transaksi`, `Konten`, `Film`, `Serial_TV`, `Episode`, `Aktor`, `Genre`, serta tabel relasi: `Genre_Konten`, `Peran`, `Audio`, `Subtitle`, `Menonton`, `Rating`, dan weak entity `Profil`.

## Generator Data
Skrip `generate_fixtures.py`
- Menghasilkan konten: 300 judul (150 Film + 150 Serial_TV).
- Menambahkan 2 episode untuk tiap serial (total 300 episode).
- Menentukan variasi bahasa audio & subtitle (1–2 per konten).
- Memberi 1–3 genre per konten.
- Membuat 150 aktor, 200 peran unik (aktor-konten).
- Membuat 150 pelanggan, masing-masing 1 profil (150 profil).
- Menambahkan transaksi, menonton, rating (masing-masing 150, dengan logika unik di rating).

Kalo mau reproduce:
```bash
python3 generate_fixtures.py
```
Output: `basdat_movie_fixtures.sql`.

## Cara Menggunakan (Import ke MySQL/MariaDB)
Pastikan MySQL/MariaDB terpasang. Nama database di skema adalah `basdat_movie` (hati-hati jangan salah ketik jadi `basdar_movie`).

1. Import skema:
```bash
mysql -u <user> -p < basdat_movie_schema.sql
```
2. Import data dummy:
```bash
mysql -u <user> -p basdat_movie < basdat_movie_fixtures.sql
```
Ganti `<user>` dengan user MySQL Anda (mis. `root`). Masukkan password saat diminta.

Catatan: Pesan "Deprecated program name" yang muncul saat pakai `mysql` hanya peringatan dari MariaDB agar memakai binary `mariadb` di versi mendatang; fungsionalitas tetap berjalan. Alternatif perintah sama:
```bash
mariadb -u <user> -p basdat_movie < basdat_movie_fixtures.sql
```

## Verifikasi Jumlah Data
Hasil perhitungan jumlah baris INSERT per tabel:
```
Aktor: 150
Audio: 458
Episode: 300
Film: 150
Genre: 150
Genre_Konten: 609
Kartu_Kredit: 150
Konten: 300
Menonton: 150
Paket_Langganan: 5
Pelanggan: 150
Peran: 200
Profil: 150
Rating: 150
Serial_TV: 150
Subtitle: 454
Transaksi: 150
```
Semua tabel yang wajar untuk memiliki 150+ baris sudah terpenuhi. Volume tambahan pada tabel relasi (mis. `Genre_Konten`, `Audio`, `Subtitle`) terjadi karena hubungan many-to-many dan multi-bahasa.

## Tabel yang Tidak Mencapai 150 Baris
- `Paket_Langganan` (5 baris): Tabel referensi kecil untuk jenis paket (Basic, Standard, Premium, Mobile, Family). Secara konseptual jumlahnya terbatas dan tidak realistis jika dipaksa menjadi 150 variasi paket.

Jika tetap diperlukan 150 baris (misal untuk stress test), skrip dapat diubah dengan membuat daftar paket ter-generate otomatis. Contoh modifikasi singkat:
```python
pakets = [(f'Paket_{i+1}', round(random.uniform(2.99,29.99),2), random.choice(['480p','720p','1080p','4K']), random.randint(1,8)) for i in range(150)]
```

## Validasi Konsistensi Foreign Key
Urutan insert diatur agar parent selalu ada sebelum child:
- `Konten` sebelum `Film` / `Serial_TV` / `Audio` / `Subtitle` / `Genre_Konten` / `Peran` / `Menonton` / `Rating` / `Episode`.
- `Pelanggan` sebelum `Profil`, `Transaksi`, `Menonton`, `Rating`.
- `Profil` sebelum `Menonton` & `Rating`.
- `Serial_TV` sebelum `Episode`.
- `Genre` sebelum `Genre_Konten`.
- `Aktor` sebelum `Peran`.

## Menambah / Menyesuaikan Data
Beberapa ide lanjutan:
- Tambah lebih banyak episode per serial (ubah loop Episode).
- Pakai library Faker untuk nama, email, komentar lebih natural.
- Tambah variasi durasi dengan distribusi (mis. normal truncated) agar lebih realistis.
- Tambah indeks sekunder (mis. pada kolom pencarian umum seperti `tahun_rilis`).

## Troubleshooting
- Jika terjadi error foreign key saat import: pastikan Anda mengimport skema terlebih dahulu dan database aktif adalah `basdat_movie`.
- Jika menjalankan ulang generator beberapa kali, hapus data lama atau drop database untuk menghindari konflik primary key.
- Jika ingin mempercepat import besar, bisa sementara matikan foreign_key_checks:
```sql
SET FOREIGN_KEY_CHECKS=0; -- sebelum import massal
-- lakukan import
SET FOREIGN_KEY_CHECKS=1; -- aktifkan kembali
```

## Lisensi
Made by Nafhan Shafy Aulia

---