-- Skema
DROP DATABASE IF EXISTS `basdat_movie`;
CREATE DATABASE IF NOT EXISTS `basdat_movie`;
USE `basdat_movie`;


-- Strong Entity
CREATE TABLE IF NOT EXISTS `Paket_Langganan` (
  `nama_paket` VARCHAR(50) NOT NULL,
  `harga_bulanan` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
  `maks_resolusi` VARCHAR(20) NOT NULL, -- Penyesuaian dengan revisi tidak boleh NULL
  `maks_perangkat` INT NOT NULL,        -- Penyesuaian dengan revisi tidak boleh NULL
  PRIMARY KEY (`nama_paket`)
);


CREATE TABLE IF NOT EXISTS `Kartu_Kredit` (
  `nomor_kartu` VARCHAR(19) NOT NULL,
  `jenis` VARCHAR(50) NOT NULL,               -- Penyesuaian dengan revisi tidak boleh NULL
  `empat_digit_nomor` CHAR(4) NOT NULL,    -- Penyesuaian dengan revisi tidak boleh NULL
  `tanggal_kadaluarsa` DATE NOT NULL,         -- Penyesuaian dengan revisi tidak boleh NULL
  PRIMARY KEY (`nomor_kartu`)
);


CREATE TABLE IF NOT EXISTS `Pelanggan` (
  `email` VARCHAR(100) NOT NULL,
  `nama_lengkap` VARCHAR(100) NOT NULL,
  `tanggal_lahir` DATE NOT NULL,          -- Penyesuaian dengan revisi tidak boleh NULL
  `nama_paket` VARCHAR(50) NOT NULL,
  `nomor_kartu` VARCHAR(19) NULL,         -- Penyesuaian dengan revisi diperbolehkan NULL
  PRIMARY KEY (`email`),
  CONSTRAINT `fk_pelanggan_paket`
    FOREIGN KEY (`nama_paket`) REFERENCES `Paket_Langganan` (`nama_paket`)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_pelanggan_kartu`
    FOREIGN KEY (`nomor_kartu`) REFERENCES `Kartu_Kredit` (`nomor_kartu`)
    ON DELETE SET NULL ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS `Transaksi` (
  `id_transaksi` INT NOT NULL AUTO_INCREMENT,
  `tanggal_pembayaran` DATE NOT NULL,
  `biaya_tagihan` DECIMAL(10, 2) NOT NULL,
  `status` ENUM('Berhasil', 'Menunggu', 'Gagal') NOT NULL,
  `email_pelanggan` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id_transaksi`),
  CONSTRAINT `fk_transaksi_pelanggan`
    FOREIGN KEY (`email_pelanggan`)
    REFERENCES `Pelanggan` (`email`)
    ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS `Konten` (
  `judul` VARCHAR(255) NOT NULL,
  `sinopsis` TEXT NOT NULL,           -- Penyesuaian dengan revisi tidak boleh NULL
  `tahun_rilis` YEAR NOT NULL,        -- Penyesuaian dengan revisi tidak boleh NULL
  `rating_usia` VARCHAR(10) NOT NULL, -- Penyesuaian dengan revisi tidak boleh NULL
  `type` ENUM('Film','Serial_TV') NOT NULL DEFAULT 'Film',
  PRIMARY KEY (`judul`)
);


CREATE TABLE IF NOT EXISTS `Aktor` (
  `nama_lengkap` VARCHAR(100) NOT NULL,
  `tanggal_lahir` DATE NULL,
  `negara_asal` VARCHAR(50) NULL,
  PRIMARY KEY (`nama_lengkap`)
);


CREATE TABLE IF NOT EXISTS `Genre` (
  `genre_id` INT NOT NULL AUTO_INCREMENT,
  `nama_genre` VARCHAR(50) NOT NULL UNIQUE,
  PRIMARY KEY (`genre_id`)
);


-- Tabel Spesialisasi 

CREATE TABLE IF NOT EXISTS `Film` (
  `judul` VARCHAR(255) NOT NULL,
  `durasi` INT NULL,
  `sutradara` VARCHAR(100) NULL,
  PRIMARY KEY (`judul`),
  CONSTRAINT `fk_film_konten`
    FOREIGN KEY (`judul`)
    REFERENCES `Konten` (`judul`)
    ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS `Serial_TV` (
  `judul` VARCHAR(255) NOT NULL,
  `total_season` INT NOT NULL,  -- Penyesuaian dengan revisi tidak boleh NULL
  PRIMARY KEY (`judul`),
  CONSTRAINT `fk_serial_konten`
    FOREIGN KEY (`judul`) REFERENCES `Konten` (`judul`)
    ON DELETE CASCADE ON UPDATE CASCADE
);


-- Weak Entity

CREATE TABLE IF NOT EXISTS `Profil` (
  `email_pelanggan` VARCHAR(100) NOT NULL,
  `nama` VARCHAR(50) NOT NULL,
  `kategori_usia` VARCHAR(20) NOT NULL, -- Penyesuaian dengan revisi tidak boleh NULL
  PRIMARY KEY (`email_pelanggan`, `nama`),
  CONSTRAINT `fk_profil_pelanggan`
    FOREIGN KEY (`email_pelanggan`) REFERENCES `Pelanggan` (`email`)
    ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS `Episode` (
  `judul` VARCHAR(255) NOT NULL,          -- Ganti nama dari 'judul_serial' jadi 'judul'
  `judul_episode` VARCHAR(255) NOT NULL,  -- Bagian dari Primary Key
  `nomor_season` INT NOT NULL,
  `nomor_urut_episode` INT NOT NULL,
  `sinopsis` TEXT NOT NULL,               -- Penyesuaian dengan revisi tidak boleh NULL
  `durasi` INT NOT NULL,                  -- Penyesuaian dengan revisi tidak boleh NULL
  PRIMARY KEY (`judul`, `judul_episode`), -- PK sesuai PDF (bukan nomor urut)
  CONSTRAINT `fk_episode_serial`
    FOREIGN KEY (`judul`) REFERENCES `Serial_TV` (`judul`)
    ON DELETE CASCADE ON UPDATE CASCADE
);


-- Tabel Relasi Many-to-Many
CREATE TABLE IF NOT EXISTS `Genre_Konten` (
  `judul` VARCHAR(255) NOT NULL,
  `genre_id` INT NOT NULL,
  PRIMARY KEY (`judul`, `genre_id`),
  CONSTRAINT `fk_genre_konten_judul`
    FOREIGN KEY (`judul`)
    REFERENCES `Konten` (`judul`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_genre_konten_id`
    FOREIGN KEY (`genre_id`)
    REFERENCES `Genre` (`genre_id`)
    ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS `Peran` (
  `nama_aktor` VARCHAR(100) NOT NULL,
  `judul` VARCHAR(255) NOT NULL,
  `peran` VARCHAR(50) NULL,
  PRIMARY KEY (`nama_aktor`, `judul`),
  CONSTRAINT `fk_peran_aktor`
    FOREIGN KEY (`nama_aktor`)
    REFERENCES `Aktor` (`nama_lengkap`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_peran_konten`
    FOREIGN KEY (`judul`)
    REFERENCES `Konten` (`judul`)
    ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS `Audio` (
  `judul` VARCHAR(255) NOT NULL,
  `bahasa_audio` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`judul`, `bahasa_audio`),
  CONSTRAINT `fk_audio_konten`
    FOREIGN KEY (`judul`)
    REFERENCES `Konten` (`judul`)
    ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS `Subtitle` (
  `judul` VARCHAR(255) NOT NULL,
  `bahasa_subtitle` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`judul`, `bahasa_subtitle`),
  CONSTRAINT `fk_subtitle_konten`
    FOREIGN KEY (`judul`)
    REFERENCES `Konten` (`judul`)
    ON DELETE CASCADE ON UPDATE CASCADE
);


-- Tabel Relasi Tambahan
CREATE TABLE IF NOT EXISTS `Menonton` (
  `email_pelanggan` VARCHAR(100) NOT NULL,
  `nama_profil` VARCHAR(50) NOT NULL,
  `judul_konten` VARCHAR(255) NOT NULL,
  `waktu_terakhir` DATETIME NOT NULL,  -- Penyesuaian dengan revisi tidak boleh NULL
  `posisi_terakhir` INT NOT NULL,      -- Penyesuaian dengan revisi tidak boleh NULL
  PRIMARY KEY (`email_pelanggan`, `nama_profil`, `judul_konten`),
  CONSTRAINT `fk_menonton_profil`
    FOREIGN KEY (`email_pelanggan`, `nama_profil`)
    REFERENCES `Profil` (`email_pelanggan`, `nama`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_menonton_konten`
    FOREIGN KEY (`judul_konten`) REFERENCES `Konten` (`judul`)
    ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS `Rating` (
  `email_pelanggan` VARCHAR(100) NOT NULL,
  `nama_profil` VARCHAR(50) NOT NULL,
  `judul_konten` VARCHAR(255) NOT NULL,
  `skor` INT NOT NULL CHECK (`skor` BETWEEN 1 AND 5),
  `komentar` TEXT NOT NULL, -- Penyesuaian dengan revisi tidak boleh NULL
  PRIMARY KEY (`email_pelanggan`, `nama_profil`, `judul_konten`),
  CONSTRAINT `fk_rating_profil`
    FOREIGN KEY (`email_pelanggan`, `nama_profil`)
    REFERENCES `Profil` (`email_pelanggan`, `nama`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_rating_konten`
    FOREIGN KEY (`judul_konten`) REFERENCES `Konten` (`judul`)
    ON DELETE CASCADE ON UPDATE CASCADE
);