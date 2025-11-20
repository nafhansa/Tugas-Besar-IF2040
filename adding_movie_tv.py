import requests
import random

# ============================================
# KONFIGURASI UTAMA
# ============================================
API_KEY = "f25e8035a509c59ccc243f96b5237829"
OUTPUT_FILE = "basdat_movie_scraped.sql"
DB_NAME = "basdat_movie"

LIMIT_MOVIES = 250   # ambil agak banyak biar yang tembus ke DB >=150
LIMIT_TV = 250

VERBOSE = True
LOG_EVERY_N = 10

# ============================================
# UTIL
# ============================================

def log(msg):
    if VERBOSE:
        print(msg)

def escape_sql(s):
    if not s:
        return ""
    return s.replace("'", "''")

BASE = "https://api.themoviedb.org/3"

def fetch(endpoint, params=None):
    """Wrapper request ke TMDB yang tahan error jaringan."""
    params = params or {}
    params["api_key"] = API_KEY
    try:
        r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"[WARN] Error request ke {endpoint}: {e}")
        return None

    if r.status_code != 200:
        print(f"[WARN] Gagal fetch {endpoint}: HTTP {r.status_code}")
        return None
    try:
        return r.json()
    except ValueError as e:
        print(f"[WARN] Response JSON invalid dari {endpoint}: {e}")
        return None

# ============================================
# FETCH LIST POPULAR MOVIES / TV
# ============================================

def fetch_movies(limit):
    print(f"\n=== FETCH {limit} MOVIES ===")
    page = 1
    out = []
    while len(out) < limit:
        data = fetch("movie/popular", {"page": page, "language": "en-US"})
        if not data or "results" not in data:
            break
        for m in data["results"]:
            if len(out) >= limit:
                break
            out.append(m)
        log(f"  Page {page} -> total {len(out)}")
        page += 1
    return out

def fetch_tv(limit):
    print(f"\n=== FETCH {limit} TV SHOWS ===")
    page = 1
    out = []
    while len(out) < limit:
        data = fetch("tv/popular", {"page": page, "language": "en-US"})
        if not data or "results" not in data:
            break
        for t in data["results"]:
            if len(out) >= limit:
                break
            out.append(t)
        log(f"  Page {page} -> total {len(out)}")
        page += 1
    return out

# ============================================
# RATING USIA
# ============================================

def extract_movie_cert(detail):
    arr = detail.get("release_dates", {}).get("results", [])
    for cc in ["ID", "US"]:
        for r in arr:
            if r.get("iso_3166_1") == cc:
                for x in r.get("release_dates", []):
                    if x.get("certification"):
                        return x["certification"]
    return "NR"

def extract_tv_cert(detail):
    arr = detail.get("content_ratings", {}).get("results", [])
    for cc in ["ID", "US"]:
        for r in arr:
            if r.get("iso_3166_1") == cc:
                if r.get("rating"):
                    return r["rating"]
    return "NR"

# ============================================
# MAIN
# ============================================

def main():
    print("\n============================================")
    print("   GENERATE SCRAPED MOVIE + TV DATA ONLY    ")
    print("============================================\n")

    sql = []
    sql.append(f"USE `{DB_NAME}`;")
    sql.append("SET FOREIGN_KEY_CHECKS = 0;")
    sql.append("START TRANSACTION;")

    # fetch list
    movies = fetch_movies(LIMIT_MOVIES)
    tvshows = fetch_tv(LIMIT_TV)

    if not movies:
        print("[ERROR] Tidak ada movie yang berhasil di-fetch. Cek API_KEY / koneksi.")
        return
    if not tvshows:
        print("[ERROR] Tidak ada TV show yang berhasil di-fetch. Cek API_KEY / koneksi.")
        return

    genre_map = {}
    next_genre_id = 1

    # =====================================
    # PROSES MOVIES
    # =====================================
    print("\n=== PROSES DETAIL MOVIE ===")

    for idx, m in enumerate(movies, start=1):
        detail = fetch(f"movie/{m['id']}", {
            "language": "en-US",
            "append_to_response": "credits,release_dates"
        })
        if not detail:
            continue

        title = escape_sql(detail.get("title"))
        if not title:
            continue

        if idx % LOG_EVERY_N == 0 or idx == 1:
            log(f"[MOVIE] {idx}/{len(movies)} : {title}")

        sinopsis = escape_sql(detail.get("overview", ""))
        release = detail.get("release_date", "")
        tahun = release[:4] if release else "NULL"
        rating_usia = escape_sql(extract_movie_cert(detail))

        # Konten
        sql.append(
            f"INSERT IGNORE INTO Konten VALUES ('{title}', '{sinopsis}', "
            f"{tahun if tahun!='NULL' else 'NULL'}, '{rating_usia}', 'Film');"
        )

        # Film
        runtime = detail.get("runtime")
        durasi_sql = runtime if isinstance(runtime, int) else "NULL"

        # sutradara
        director = "NULL"
        for c in detail.get("credits", {}).get("crew", []):
            if c.get("job") == "Director":
                director = f"'{escape_sql(c.get('name',''))}'"
                break

        sql.append(
            f"INSERT IGNORE INTO Film VALUES ('{title}', {durasi_sql}, {director});"
        )

        # GENRE
        for g in detail.get("genres", []):
            gname = escape_sql(g["name"])
            if gname not in genre_map:
                genre_map[gname] = next_genre_id
                sql.append(
                    f"INSERT IGNORE INTO Genre VALUES ({next_genre_id}, '{gname}');"
                )
                next_genre_id += 1

            gid = genre_map[gname]
            sql.append(
                f"INSERT IGNORE INTO Genre_Konten VALUES ('{title}', {gid});"
            )

        # CAST
        cast = detail.get("credits", {}).get("cast", [])[:10]
        for c in cast:
            actor = escape_sql(c.get("name"))
            peran = escape_sql(c.get("character", ""))

            sql.append(
                f"INSERT IGNORE INTO Aktor (`nama_lengkap`) VALUES ('{actor}');"
            )

            sql.append(
                f"INSERT IGNORE INTO Peran VALUES ('{actor}', '{title}', '{peran}');"
            )

        # audio & subtitle dummy
        langs = ["Inggris", "Indonesia", "Spanyol", "Korea", "Jepang"]
        aud = random.sample(langs, k=random.randint(1, 3))
        sub = random.sample(langs, k=random.randint(1, 4))

        for a in aud:
            sql.append(f"INSERT IGNORE INTO Audio VALUES ('{title}', '{a}');")
        for s in sub:
            sql.append(f"INSERT IGNORE INTO Subtitle VALUES ('{title}', '{s}');")

    # =====================================
    # PROSES TV SHOW
    # =====================================
    print("\n=== PROSES DETAIL TV ===")

    for idx, tv in enumerate(tvshows, start=1):
        detail = fetch(f"tv/{tv['id']}", {
            "language": "en-US",
            "append_to_response": "credits,content_ratings"
        })
        if not detail:
            continue

        title = escape_sql(detail.get("name"))
        if not title:
            continue

        if idx % LOG_EVERY_N == 0 or idx == 1:
            log(f"[TV] {idx}/{len(tvshows)} : {title}")

        sinopsis = escape_sql(detail.get("overview", ""))
        first_air = detail.get("first_air_date", "")
        tahun = first_air[:4] if first_air else "NULL"
        rating_usia = escape_sql(extract_tv_cert(detail))

        # Konten
        sql.append(
            f"INSERT IGNORE INTO Konten VALUES ('{title}', '{sinopsis}', "
            f"{tahun if tahun!='NULL' else 'NULL'}, '{rating_usia}', 'Serial_TV');"
        )

        # Serial_TV
        total_season = detail.get("number_of_seasons")
        val = total_season if isinstance(total_season, int) else "NULL"
        sql.append(
            f"INSERT IGNORE INTO Serial_TV VALUES ('{title}', {val});"
        )

        # GENRE
        for g in detail.get("genres", []):
            gname = escape_sql(g["name"])
            if gname not in genre_map:
                genre_map[gname] = next_genre_id
                sql.append(f"INSERT IGNORE INTO Genre VALUES ({next_genre_id}, '{gname}');")
                next_genre_id += 1

            gid = genre_map[gname]
            sql.append(
                f"INSERT IGNORE INTO Genre_Konten VALUES ('{title}', {gid});"
            )

        # CAST
        cast = detail.get("credits", {}).get("cast", [])[:10]
        for c in cast:
            actor = escape_sql(c.get("name"))
            role = escape_sql(c.get("character", ""))

            sql.append(
                f"INSERT IGNORE INTO Aktor (`nama_lengkap`) VALUES ('{actor}');"
            )

            sql.append(
                f"INSERT IGNORE INTO Peran VALUES ('{actor}', '{title}', '{role}');"
            )

        # EPISODE (season 1 max 3 ep)
        season = fetch(f"tv/{tv['id']}/season/1", {"language": "en-US"})
        if season and "episodes" in season:
            eps = season["episodes"][:3]
            for ep in eps:
                epnum = ep.get("episode_number", 0)
                ep_title = escape_sql(ep.get("name", f"Episode {epnum}"))
                ep_sin = escape_sql(ep.get("overview", ""))
                runtime = ep.get("runtime") or (detail.get("episode_run_time") or [45])[0]

                sql.append(
                    f"INSERT IGNORE INTO Episode VALUES "
                    f"('{title}', 1, {epnum}, '{ep_title}', '{ep_sin}', {runtime});"
                )

        # audio & subtitle dummy
        langs = ["Inggris", "Indonesia", "Spanyol", "Korea", "Jepang"]
        aud = random.sample(langs, k=random.randint(1, 3))
        sub = random.sample(langs, k=random.randint(1, 4))
        for a in aud:
            sql.append(f"INSERT IGNORE INTO Audio VALUES ('{title}', '{a}');")
        for s in sub:
            sql.append(f"INSERT IGNORE INTO Subtitle VALUES ('{title}', '{s}');")

    # END SQL
    sql.append("COMMIT;")
    sql.append("SET FOREIGN_KEY_CHECKS = 1;")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sql))

    print("\n============================================")
    print("  ✅ DONE — FILE HAS BEEN GENERATED")
    print("  Saved as:", OUTPUT_FILE)
    print("============================================\n")


if __name__ == "__main__":
    main()
