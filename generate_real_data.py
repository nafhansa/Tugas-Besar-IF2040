import requests
import random
from datetime import datetime, timedelta

# ============================================
# KONFIGURASI UTAMA
# ============================================
API_KEY = "f25e8035a509c59ccc243f96b5237829" 
OUTPUT_FILE = "basdat_movie_real_data.sql"
DB_NAME = "basdat_movie"

# Jumlah minimal data
LIMIT_MOVIES = 150        # minimal 150 film
LIMIT_TV = 150            # minimal 150 serial TV
JUMLAH_PELANGGAN = 200    # supaya tabel operasional >= 150 baris

# Pengaturan verbose logging
VERBOSE = True            # kalau mau lebih sepi, ubah ke False
LOG_EVERY_N_MOVIES = 25   # log setiap N film
LOG_EVERY_N_TV = 25       # log setiap N serial TV


# ============================================
# HELPER LOGGING & UTIL
# ============================================

def log(msg: str):
    """Cetak log hanya kalau VERBOSE = True."""
    if VERBOSE:
        print(msg)


def escape_sql(value: str) -> str:
    """Escape tanda petik tunggal untuk dimasukkan ke SQL."""
    if value is None:
        return ""
    return str(value).replace("'", "''")


def random_date(start_year: int, end_year: int) -> str:
    """Generate tanggal random antara 1 Jan start_year dan 31 Des end_year."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    d = start + timedelta(days=random_days)
    return d.strftime("%Y-%m-%d")


def get_age_category(birth_date_str: str) -> str:
    """Kategori usia sederhana untuk profil (Anak-anak / Remaja / Dewasa)."""
    try:
        birth = datetime.strptime(birth_date_str, "%Y-%m-%d")
    except Exception:
        return "Dewasa"
    age = (datetime.now() - birth).days // 365
    if age < 13:
        return "Anak-anak"
    elif age < 18:
        return "Remaja"
    else:
        return "Dewasa"


# ============================================
# FUNGSI FETCH DARI TMDB
# ============================================

BASE_URL = "https://api.themoviedb.org/3"


def fetch_tmdb(endpoint: str, params: dict):
    """Wrapper sederhana untuk request ke TMDB."""
    params = params.copy()
    params["api_key"] = API_KEY
    resp = requests.get(f"{BASE_URL}/{endpoint}", params=params)
    if resp.status_code != 200:
        print(f"[WARN] Gagal fetch {endpoint}: HTTP {resp.status_code}")
        return None
    return resp.json()


def fetch_movies(limit=LIMIT_MOVIES):
    print(f"\n=== MENGAMBIL DATA FILM POPULER (TARGET: {limit}) ===")
    page = 1
    collected = []
    while len(collected) < limit:
        data = fetch_tmdb("movie/popular", {"page": page, "language": "en-US"})
        if not data or "results" not in data:
            print("[ERROR] Tidak ada data 'results' pada response movie/popular.")
            break

        results = data["results"]
        if not results:
            print("[WARN] Hasil kosong untuk page", page)
            break

        for m in results:
            if len(collected) >= limit:
                break
            collected.append(m)

        print(f"  -> Page {page} diproses, total film terkumpul: {len(collected)}")
        page += 1

    print(f"=== SELESAI FETCH FILM: {len(collected)} DIDAPAT ===\n")
    return collected


def fetch_tv(limit=LIMIT_TV):
    print(f"\n=== MENGAMBIL DATA SERIAL TV POPULER (TARGET: {limit}) ===")
    page = 1
    collected = []
    while len(collected) < limit:
        data = fetch_tmdb("tv/popular", {"page": page, "language": "en-US"})
        if not data or "results" not in data:
            print("[ERROR] Tidak ada data 'results' pada response tv/popular.")
            break

        results = data["results"]
        if not results:
            print("[WARN] Hasil kosong untuk page", page)
            break

        for tv in results:
            if len(collected) >= limit:
                break
            collected.append(tv)

        print(f"  -> Page {page} diproses, total serial terkumpul: {len(collected)}")
        page += 1

    print(f"=== SELESAI FETCH TV: {len(collected)} DIDAPAT ===\n")
    return collected


def fetch_movie_detail(movie_id: int):
    return fetch_tmdb(
        f"movie/{movie_id}",
        {"language": "en-US", "append_to_response": "credits,release_dates"},
    )


def fetch_tv_detail(tv_id: int):
    return fetch_tmdb(
        f"tv/{tv_id}",
        {"language": "en-US", "append_to_response": "credits,content_ratings"},
    )


def fetch_tv_season(tv_id: int, season_number: int = 1):
    return fetch_tmdb(
        f"tv/{tv_id}/season/{season_number}",
        {"language": "en-US"},
    )


def extract_certification_from_movie(detail: dict) -> str:
    """Ambil rating usia (certification) dari detail film TMDB."""
    results = (detail.get("release_dates") or {}).get("results") or []
    for country_code in ["ID", "US"]:
        for r in results:
            if r.get("iso_3166_1") == country_code:
                for rel in r.get("release_dates", []):
                    cert = rel.get("certification")
                    if cert:
                        return cert
    return "NR"  # Not Rated


def extract_certification_from_tv(detail: dict) -> str:
    """Ambil rating usia (content rating) dari detail TV TMDB."""
    results = (detail.get("content_ratings") or {}).get("results") or []
    for country_code in ["ID", "US"]:
        for r in results:
            if r.get("iso_3166_1") == country_code:
                cert = r.get("rating")
                if cert:
                    return cert
    return "NR"


# ============================================
# FUNGSI UTAMA GENERATE SQL
# ============================================

def main():
    print("=======================================")
    print("   GENERATE REAL DATA basdat_movie     ")
    print("=======================================\n")

    final_lines = []
    final_lines.append(f"USE `{DB_NAME}`;")
    final_lines.append("SET FOREIGN_KEY_CHECKS = 0;")
    final_lines.append("START TRANSACTION;")

    # ------------------------------------
    # 1. AMBIL DATA FILM & TV
    # ------------------------------------
    movies = fetch_movies(LIMIT_MOVIES)
    tvshows = fetch_tv(LIMIT_TV)

    genre_map = {}      # nama_genre -> genre_id
    next_genre_id = 1

    konten_judul_list = []  # untuk Menonton & Rating

    # Bahasa untuk Audio & Subtitle
    language_map = {
        "en": "Inggris",
        "id": "Indonesia",
        "ja": "Jepang",
        "ko": "Korea",
        "es": "Spanyol",
    }
    language_names = list(language_map.values())

    # ------------------------------------
    # 2. PROSES FILM
    # ------------------------------------
    print("=== MEMPROSES DETAIL FILM ===")
    for idx, m in enumerate(movies, start=1):
        movie_id = m.get("id")
        if not movie_id:
            continue

        detail = fetch_movie_detail(movie_id)
        if not detail:
            print(f"[WARN] Detail film ID {movie_id} tidak berhasil diambil.")
            continue

        judul = escape_sql(detail.get("title") or "")
        if not judul:
            continue

        sinopsis = escape_sql(detail.get("overview") or "")
        release_date = detail.get("release_date") or ""
        tahun_rilis = release_date[:4] if len(release_date) >= 4 else "NULL"
        certification = extract_certification_from_movie(detail)
        tipe = "Film"

        # Log progress setiap beberapa film
        if idx % LOG_EVERY_N_MOVIES == 0 or idx == 1 or idx == len(movies):
            log(f"  [Film] Proses ke-{idx}/{len(movies)}: {judul}")

        # Konten
        if tahun_rilis == "NULL":
            final_lines.append(
                "INSERT IGNORE INTO `Konten` "
                "(`judul`,`sinopsis`,`tahun_rilis`,`rating_usia`,`type`) "
                f"VALUES ('{judul}', '{sinopsis}', NULL, '{escape_sql(certification)}', '{tipe}');"
            )
        else:
            final_lines.append(
                "INSERT IGNORE INTO `Konten` "
                "(`judul`,`sinopsis`,`tahun_rilis`,`rating_usia`,`type`) "
                f"VALUES ('{judul}', '{sinopsis}', {tahun_rilis}, '{escape_sql(certification)}', '{tipe}');"
            )

        konten_judul_list.append(judul)

        # Film spesialisasi
        durasi = detail.get("runtime")
        if isinstance(durasi, int) and durasi > 0:
            durasi_sql = str(durasi)
        else:
            durasi_sql = "NULL"

        # cari sutradara
        sutradara = ""
        credits = detail.get("credits") or {}
        for crew in credits.get("crew", []):
            if crew.get("job") == "Director":
                sutradara = escape_sql(crew.get("name") or "")
                break

        sutradara_sql = f"'{sutradara}'" if sutradara else "NULL"
        final_lines.append(
            "INSERT IGNORE INTO `Film` (`judul`,`durasi`,`sutradara`) "
            f"VALUES ('{judul}', {durasi_sql}, {sutradara_sql});"
        )

        # Genre & Genre_Konten
        for g in detail.get("genres", []):
            nama_genre = escape_sql(g.get("name") or "")
            if not nama_genre:
                continue
            if nama_genre not in genre_map:
                genre_map[nama_genre] = next_genre_id
                final_lines.append(
                    "INSERT IGNORE INTO `Genre` (`genre_id`,`nama_genre`) "
                    f"VALUES ({next_genre_id}, '{nama_genre}');"
                )
                next_genre_id += 1
            gid = genre_map[nama_genre]
            final_lines.append(
                "INSERT IGNORE INTO `Genre_Konten` (`judul_konten`,`genre_id`) "
                f"VALUES ('{judul}', {gid});"
            )

        # Aktor & Peran
        cast = (credits or {}).get("cast", [])[:10]
        for c in cast:
            nama_aktor = escape_sql(c.get("name") or "")
            if not nama_aktor:
                continue
            karakter = escape_sql(c.get("character") or "")
            final_lines.append(
                "INSERT IGNORE INTO `Aktor` (`nama_lengkap`) "
                f"VALUES ('{nama_aktor}');"
            )
            final_lines.append(
                "INSERT IGNORE INTO `Peran` (`nama_aktor`,`judul_konten`,`peran`) "
                f"VALUES ('{nama_aktor}', '{judul}', '{karakter}');"
            )

        # Audio & Subtitle (dummy beberapa bahasa)
        audio_langs = random.sample(
            language_names, k=random.randint(1, min(3, len(language_names)))
        )
        sub_langs = random.sample(
            language_names, k=random.randint(1, min(4, len(language_names)))
        )
        for la in audio_langs:
            final_lines.append(
                "INSERT IGNORE INTO `Audio` (`judul_konten`,`bahasa_audio`) "
                f"VALUES ('{judul}', '{la}');"
            )
        for ls in sub_langs:
            final_lines.append(
                "INSERT IGNORE INTO `Subtitle` (`judul_konten`,`bahasa_subtitle`) "
                f"VALUES ('{judul}', '{ls}');"
            )

    print("=== SELESAI PROSES FILM ===\n")

    # ------------------------------------
    # 3. PROSES SERIAL TV
    # ------------------------------------
    print("=== MEMPROSES DETAIL SERIAL TV ===")
    for idx, tv in enumerate(tvshows, start=1):
        tv_id = tv.get("id")
        if not tv_id:
            continue

        detail = fetch_tv_detail(tv_id)
        if not detail:
            print(f"[WARN] Detail TV ID {tv_id} tidak berhasil diambil.")
            continue

        judul = escape_sql(detail.get("name") or "")
        if not judul:
            continue

        # Log progress
        if idx % LOG_EVERY_N_TV == 0 or idx == 1 or idx == len(tvshows):
            log(f"  [TV] Proses ke-{idx}/{len(tvshows)}: {judul}")

        sinopsis = escape_sql(detail.get("overview") or "")
        first_air_date = detail.get("first_air_date") or ""
        tahun_rilis = first_air_date[:4] if len(first_air_date) >= 4 else "NULL"
        certification = extract_certification_from_tv(detail)
        tipe = "Serial_TV"

        if tahun_rilis == "NULL":
            final_lines.append(
                "INSERT IGNORE INTO `Konten` "
                "(`judul`,`sinopsis`,`tahun_rilis`,`rating_usia`,`type`) "
                f"VALUES ('{judul}', '{sinopsis}', NULL, '{escape_sql(certification)}', '{tipe}');"
            )
        else:
            final_lines.append(
                "INSERT IGNORE INTO `Konten` "
                "(`judul`,`sinopsis`,`tahun_rilis`,`rating_usia`,`type`) "
                f"VALUES ('{judul}', '{sinopsis}', {tahun_rilis}, '{escape_sql(certification)}', '{tipe}');"
            )

        konten_judul_list.append(judul)

        total_season = detail.get("number_of_seasons")
        if isinstance(total_season, int) and total_season >= 0:
            total_season_sql = str(total_season)
        else:
            total_season_sql = "NULL"

        final_lines.append(
            "INSERT IGNORE INTO `Serial_TV` (`judul`,`total_season`) "
            f"VALUES ('{judul}', {total_season_sql});"
        )

        # Genre & Genre_Konten
        for g in detail.get("genres", []):
            nama_genre = escape_sql(g.get("name") or "")
            if not nama_genre:
                continue
            if nama_genre not in genre_map:
                genre_map[nama_genre] = next_genre_id
                final_lines.append(
                    "INSERT IGNORE INTO `Genre` (`genre_id`,`nama_genre`) "
                    f"VALUES ({next_genre_id}, '{nama_genre}');"
                )
                next_genre_id += 1
            gid = genre_map[nama_genre]
            final_lines.append(
                "INSERT IGNORE INTO `Genre_Konten` (`judul_konten`,`genre_id`) "
                f"VALUES ('{judul}', {gid});"
            )

        # Aktor & Peran
        credits = detail.get("credits") or {}
        cast = credits.get("cast", [])[:10]
        for c in cast:
            nama_aktor = escape_sql(c.get("name") or "")
            if not nama_aktor:
                continue
            karakter = escape_sql(c.get("character") or "")
            final_lines.append(
                "INSERT IGNORE INTO `Aktor` (`nama_lengkap`) "
                f"VALUES ('{nama_aktor}');"
            )
            final_lines.append(
                "INSERT IGNORE INTO `Peran` (`nama_aktor`,`judul_konten`,`peran`) "
                f"VALUES ('{nama_aktor}', '{judul}', '{karakter}');"
            )

        # Audio & Subtitle
        audio_langs = random.sample(
            language_names, k=random.randint(1, min(3, len(language_names)))
        )
        sub_langs = random.sample(
            language_names, k=random.randint(1, min(4, len(language_names)))
        )
        for la in audio_langs:
            final_lines.append(
                "INSERT IGNORE INTO `Audio` (`judul_konten`,`bahasa_audio`) "
                f"VALUES ('{judul}', '{la}');"
            )
        for ls in sub_langs:
            final_lines.append(
                "INSERT IGNORE INTO `Subtitle` (`judul_konten`,`bahasa_subtitle`) "
                f"VALUES ('{judul}', '{ls}');"
            )

        # Episode Season 1 (max 3 episode)
        season_detail = fetch_tv_season(tv_id, 1)
        if season_detail and "episodes" in season_detail:
            episodes = season_detail["episodes"][:3]
            for ep in episodes:
                nomor_ep = ep.get("episode_number") or 0
                judul_ep = escape_sql(ep.get("name") or f"Episode {nomor_ep}")
                sinopsis_ep = escape_sql(ep.get("overview") or "")
                durasi = ep.get("runtime")
                if not isinstance(durasi, int) or durasi <= 0:
                    # fallback: episode_run_time dari detail serial
                    runtimes = detail.get("episode_run_time") or [45]
                    durasi = runtimes[0] if runtimes else 45
                final_lines.append(
                    "INSERT IGNORE INTO `Episode` "
                    "(`judul_serial`,`nomor_season`,`nomor_urut_episode`,`judul_episode`,`sinopsis`,`durasi`) "
                    f"VALUES ('{judul}', 1, {nomor_ep}, '{judul_ep}', '{sinopsis_ep}', {durasi});"
                )

    print("=== SELESAI PROSES SERIAL TV ===\n")

    # ------------------------------------
    # 4. DATA PAKET LANGGANAN (REFERENSI)
    # ------------------------------------
    print("=== MENAMBAHKAN DATA PAKET LANGGANAN ===")
    final_lines.append("\n-- DATA PAKET LANGGANAN --")
    pakets = [
        ("Basic", 49000, "480p", 1),
        ("Standard", 79000, "720p", 2),
        ("Premium", 129000, "1080p", 4),
        ("Mobile", 39000, "480p", 1),
    ]
    for nama, harga, resolusi, maks_dev in pakets:
        log(f"  Paket: {nama}")
        final_lines.append(
            "INSERT IGNORE INTO `Paket_Langganan` "
            "(`nama_paket`,`harga_bulanan`,`maks_resolusi`,`maks_perangkat`) "
            f"VALUES ('{nama}', {harga:.2f}, '{resolusi}', {maks_dev});"
        )

    # ------------------------------------
    # 5. DATA OPERASIONAL (Pelanggan, etc.)
    # ------------------------------------
    print("=== MEMBANGUN DATA OPERASIONAL (Pelanggan, Profil, Menonton, Transaksi, Rating) ===")
    final_lines.append("\n-- DATA DUMMY OPERASIONAL --")

    first_names = [
        "Adi","Budi","Citra","Dewi","Eka","Fajar","Gita","Hadi","Indah","Joko",
        "Kiki","Lia","Maya","Nur","Oki","Putri","Rizky","Sari","Tono","Umar",
        "Vina","Wulan","Yuni","Zaki"
    ]
    last_names = [
        "Pratama","Wijaya","Saputra","Sari","Lestari","Hidayat","Nugroho",
        "Santoso","Kusuma","Firmansyah"
    ]
    domains = ["example.com","mail.com","test.id","student.id"]

    pelanggan_list = []   # (email, nama_lengkap, tgl_lahir, nama_paket)
    profil_list = []      # (email, nama_profil)

    # a) Kartu_Kredit + Pelanggan
    print(f"  -> Membuat {JUMLAH_PELANGGAN} pelanggan beserta kartu kredit...")
    for i in range(JUMLAH_PELANGGAN):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        email = f"{fname.lower()}.{lname.lower()}{i}@{random.choice(domains)}"
        nama_lengkap = f"{fname} {lname}"

        if (i + 1) % 50 == 0 or i == 0 or (i + 1) == JUMLAH_PELANGGAN:
            log(f"    [Pelanggan] ke-{i+1}/{JUMLAH_PELANGGAN}: {email}")

        # kartu kredit
        nomor_kartu = (
            f"{random.randint(4000,4999)}-"
            f"{random.randint(1000,9999)}-"
            f"{random.randint(1000,9999)}-"
            f"{random.randint(1000,9999)}"
        )
        empat_digit = nomor_kartu.split("-")[-1]
        tgl_kadaluwarsa = random_date(2026, 2030)

        final_lines.append(
            "INSERT IGNORE INTO `Kartu_Kredit` "
            "(`nomor_kartu`,`jenis`,`empat_digit_nomor`,`tanggal_kadaluarsa`) "
            f"VALUES ('{nomor_kartu}', 'Visa', '{empat_digit}', '{tgl_kadaluwarsa}');"
        )

        # pelanggan
        paket = random.choice(pakets)[0]
        tgl_lahir = random_date(1970, 2010)
        pelanggan_list.append((email, nama_lengkap, tgl_lahir, paket))

        final_lines.append(
            "INSERT IGNORE INTO `Pelanggan` "
            "(`email`,`nama_lengkap`,`tanggal_lahir`,`nama_paket`,`nomor_kartu`) "
            f"VALUES ('{email}', '{escape_sql(nama_lengkap)}', '{tgl_lahir}', '{paket}', '{nomor_kartu}');"
        )

    # b) Profil (1–3 per pelanggan)
    print("  -> Membuat profil untuk setiap pelanggan...")
    for idx, (email, nama_lengkap, tgl_lahir, paket) in enumerate(pelanggan_list, start=1):
        n_profil = random.randint(1, 3)
        if idx % 50 == 0 or idx == 1 or idx == len(pelanggan_list):
            log(f"    [Profil] Pelanggan ke-{idx}/{len(pelanggan_list)} ({email}), jumlah profil: {n_profil}")

        for j in range(n_profil):
            nama_profil = "Utama" if j == 0 else f"User{j+1}"
            kategori = get_age_category(tgl_lahir)
            profil_list.append((email, nama_profil))
            final_lines.append(
                "INSERT IGNORE INTO `Profil` "
                "(`email_pelanggan`,`nama`,`kategori_usia`) "
                f"VALUES ('{email}', '{nama_profil}', '{kategori}');"
            )

    # c) Menonton (3 tontonan random per profil)
    print("  -> Mengisi riwayat menonton (Menonton)...")
    if konten_judul_list:
        for idx, (email, nama_profil) in enumerate(profil_list, start=1):
            if idx % 100 == 0 or idx == 1 or idx == len(profil_list):
                log(f"    [Menonton] Profil ke-{idx}/{len(profil_list)}")

            for _ in range(3):
                judul_konten = escape_sql(random.choice(konten_judul_list))
                waktu = datetime.now() - timedelta(days=random.randint(0, 60))
                waktu_str = waktu.strftime("%Y-%m-%d %H:%M:%S")
                posisi = random.randint(5, 120)
                final_lines.append(
                    "INSERT IGNORE INTO `Menonton` "
                    "(`email_pelanggan`,`nama_profil`,`judul_konten`,`waktu_terakhir`,`posisi_terakhir`) "
                    f"VALUES ('{email}', '{nama_profil}', '{judul_konten}', '{waktu_str}', {posisi});"
                )

    # d) Transaksi (1–3 per pelanggan)
    print("  -> Membuat data transaksi (Transaksi)...")
    status_list = ["Berhasil", "Menunggu", "Gagal"]
    for idx, (email, nama_lengkap, tgl_lahir, paket) in enumerate(pelanggan_list, start=1):
        n_trx = random.randint(1, 3)
        if idx % 50 == 0 or idx == 1 or idx == len(pelanggan_list):
            log(f"    [Transaksi] Pelanggan ke-{idx}/{len(pelanggan_list)}, transaksi: {n_trx}")

        for _ in range(n_trx):
            tgl_bayar = random_date(2022, 2024)
            biaya = next((p[1] for p in pakets if p[0] == paket), 99000)
            status = random.choice(status_list)
            final_lines.append(
                "INSERT INTO `Transaksi` "
                "(`tanggal_pembayaran`,`biaya_tagihan`,`status`,`email_pelanggan`) "
                f"VALUES ('{tgl_bayar}', {biaya:.2f}, '{status}', '{email}');"
            )

    # e) Rating (1–2 rating per profil)
    print("  -> Membuat data rating (Rating)...")
    komentar_list = [
        "Seru banget!",
        "Lumayan menarik.",
        "Biasa saja.",
        "Kurang cocok sama selera saya.",
        "Wajib tonton!"
    ]
    if konten_judul_list:
        for idx, (email, nama_profil) in enumerate(profil_list, start=1):
            n_rating = random.randint(1, 2)
            if idx % 100 == 0 or idx == 1 or idx == len(profil_list):
                log(f"    [Rating] Profil ke-{idx}/{len(profil_list)}, rating: {n_rating}")

            for _ in range(n_rating):
                judul_konten = escape_sql(random.choice(konten_judul_list))
                skor = random.randint(1, 5)
                komentar = escape_sql(random.choice(komentar_list))
                final_lines.append(
                    "INSERT IGNORE INTO `Rating` "
                    "(`email_pelanggan`,`nama_profil`,`judul_konten`,`skor`,`komentar`) "
                    f"VALUES ('{email}', '{nama_profil}', '{judul_konten}', {skor}, '{komentar}');"
                )

    # ------------------------------------
    # 6. AKHIRI TRANSAKSI
    # ------------------------------------
    print("\n=== MENUTUP TRANSAKSI SQL ===")
    final_lines.append("COMMIT;")
    final_lines.append("SET FOREIGN_KEY_CHECKS = 1;")

    # TULIS KE FILE
    print(f"=== MENULIS FILE: {OUTPUT_FILE} ===")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(final_lines))

    print("\n✅ SELESAI!")
    print(f"File SQL real data tersimpan sebagai: {OUTPUT_FILE}")
    print("Silakan import ke MySQL (setelah schema dijalankan).")


if __name__ == "__main__":
    main()
