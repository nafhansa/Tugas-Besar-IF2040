import requests
import mysql.connector
import time
import os

# ============================================
# KONFIGURASI
# ============================================

# TMDB API Key v3 (bukan Bearer token v4)
API_KEY = "f25e8035a509c59ccc243f96b5237829"

TMDB_BASE = "https://api.themoviedb.org/3"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "renjana",
    "database": "basdat_movie",
}


# Nama file SQL yang mau dipatch
SQL_FILE_PATH = "basdat_movie.sql"

# Jeda antar request ke TMDB (detik) supaya aman dari rate limit
SLEEP_BETWEEN_REQUESTS = 0.3

# ============================================
# HELPER
# ============================================

def escape_sql(value: str) -> str:
    """Escape tanda petik tunggal agar aman untuk dimasukkan ke SQL literal."""
    if value is None:
        return ""
    return str(value).replace("'", "''")


def tmdb_get(endpoint, params=None):
    """Request GET ke TMDB dengan error handling dasar."""
    params = params or {}
    params["api_key"] = API_KEY

    url = f"{TMDB_BASE}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"[WARN] Gagal request ke {endpoint}: {e}")
        return None

    if resp.status_code != 200:
        print(f"[WARN] HTTP {resp.status_code} saat akses {endpoint}")
        return None

    try:
        return resp.json()
    except ValueError as e:
        print(f"[WARN] Gagal parse JSON dari {endpoint}: {e}")
        return None


def search_person_by_name(name: str):
    """
    Cari aktor di TMDB berdasarkan nama.
    Return: person_id (int) atau None kalau tidak ketemu.
    """
    data = tmdb_get("search/person", {
        "query": name,
        "language": "en-US",
        "include_adult": "false",
        "page": 1,
    })
    if not data or "results" not in data or not data["results"]:
        print(f"  [INFO] Tidak ketemu di TMDB untuk nama: {name}")
        return None

    # Ambil hasil pertama saja
    result = data["results"][0]
    return result.get("id")


def fetch_person_detail(person_id: int):
    """
    Ambil detail person TMDB.
    Return: (birthday_str, country_str) -> bisa (None, None) kalau tidak ada.
    """
    data = tmdb_get(f"person/{person_id}", {"language": "en-US"})
    if not data:
        return None, None

    birthday = data.get("birthday")          # format 'YYYY-MM-DD' atau None
    pob = data.get("place_of_birth")         # e.g. "Victoria Peak, Hong Kong" atau None

    if pob:
        # Ambil bagian terakhir setelah koma -> kira-kira negara / wilayah
        parts = [p.strip() for p in pob.split(",") if p.strip()]
        country = parts[-1] if parts else None
    else:
        country = None

    return birthday, country


# ============================================
# MAIN
# ============================================

def main():
    print("========================================================")
    print("  PATCH basdat_movie.sql DENGAN DETAIL AKTOR DARI TMDB  ")
    print("========================================================\n")

    # 0. Cek file ada
    if not os.path.exists(SQL_FILE_PATH):
        print(f"[ERROR] File SQL tidak ditemukan: {SQL_FILE_PATH}")
        return

    # 1. Baca file SQL untuk ambil list INSERT aktor yang ada
    print(f"[INFO] Membaca file SQL: {SQL_FILE_PATH}")
    if not os.path.exists(SQL_FILE_PATH):
        print(f"[ERROR] File SQL tidak ditemukan: {SQL_FILE_PATH}")
        return

    with open(SQL_FILE_PATH, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Extract nama aktor dari INSERT IGNORE INTO Aktor
    import re
    pattern = r"INSERT IGNORE INTO `?Aktor`?\s*\(`?nama_lengkap`?\)\s*VALUES\s*\('([^']+)'\)"
    matches = re.findall(pattern, sql_content, re.IGNORECASE)
    
    if not matches:
        print("[INFO] Tidak ada INSERT Aktor yang ditemukan di file SQL.")
        return

    actor_names = sorted(set(matches))  # unique + sort
    print(f"[INFO] Jumlah aktor yang akan dicari di TMDB: {len(actor_names)}\n")

    # BACKUP file original sebelum mulai
    backup_path = SQL_FILE_PATH + ".backup_before_tmdb_patch"
    if not os.path.exists(backup_path):
        print(f"[INFO] Membuat backup file lama: {backup_path}")
        with open(backup_path, "w", encoding="utf-8") as bf:
            bf.write(sql_content)
    else:
        print("  [WARN] Backup sudah ada, tidak ditimpa.")

    updated_count = 0
    not_found_count = 0
    no_detail_count = 0
    
    # Mapping nama aktor -> (tanggal_lahir, negara_asal) dari TMDB
    aktor_data = {}

    # 2. Loop setiap aktor -> TMDB fetch -> simpan data
    for idx, name in enumerate(actor_names, start=1):
        print(f"[{idx}/{len(actor_names)}] Fetch TMDB: {name}")

        person_id = search_person_by_name(name)
        if not person_id:
            not_found_count += 1
            print(f"  [SKIP] Tidak ditemukan di TMDB")
            continue

        birthday, country = fetch_person_detail(person_id)
        time.sleep(SLEEP_BETWEEN_REQUESTS)

        if not birthday and not country:
            print("  [INFO] Tidak ada data birthday/place_of_birth, dilewati.")
            no_detail_count += 1
            continue

        aktor_data[name] = (birthday, country)
        updated_count += 1

        print(f"  [OK] Data: birthday={birthday}, negara={country}")
        time.sleep(SLEEP_BETWEEN_REQUESTS)

    if not aktor_data:
        print("[INFO] Tidak ada data aktor yang ditemukan dari TMDB. File SQL tidak diubah.")
        return

    # 3. Replace INSERT lama dengan INSERT baru (dengan data dari TMDB)
    print(f"\n[INFO] Merekonstruksi INSERT statement dengan data TMDB...")
    
    new_insert_lines = []
    
    for name in actor_names:
        if name in aktor_data:
            birthday, country = aktor_data[name]
            birthday_val = f"'{birthday}'" if birthday else "NULL"
            country_val = f"'{escape_sql(country)}'" if country else "NULL"
        else:
            birthday_val = "NULL"
            country_val = "NULL"
        
        name_val = escape_sql(name)
        insert_stmt = (
            f"INSERT IGNORE INTO `Aktor` "
            f"(`nama_lengkap`, `tanggal_lahir`, `negara_asal`) "
            f"VALUES ('{name_val}', {birthday_val}, {country_val});"
        )
        new_insert_lines.append(insert_stmt)
    
    # Ganti semua INSERT Aktor lama dengan yang baru
    # Cari range INSERT Aktor (dari yang pertama sampai yang terakhir)
    aktor_insert_pattern = r"INSERT IGNORE INTO `?Aktor`?.*?VALUES\s*\([^)]+\);"
    aktor_inserts = list(re.finditer(aktor_insert_pattern, sql_content, re.IGNORECASE | re.DOTALL))
    
    if aktor_inserts:
        first_insert = aktor_inserts[0].start()
        last_insert = aktor_inserts[-1].end()
        
        # Buat content baru dengan INSERT yang sudah diupdate
        content_before_inserts = sql_content[:first_insert]
        
        # Cari content setelah semua INSERT Aktor (bisa INSERT tabel lain)
        content_after_inserts = sql_content[last_insert:]
        
        new_insert_block = "\n".join(new_insert_lines) + "\n"
        new_content = content_before_inserts + new_insert_block + content_after_inserts
    else:
        print("[ERROR] Tidak bisa menemukan range INSERT Aktor di file SQL")
        return

    # 4. Tulis file baru
    print(f"[INFO] Menulis ulang file SQL: {SQL_FILE_PATH}")
    with open(SQL_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    # 5. Ringkasan
    print("\n================ HASIL AKHIR ================")
    print(f"Total aktor ditemukan      : {len(actor_names)}")
    print(f"Data dari TMDB berhasil    : {updated_count}")
    print(f"Tidak ditemukan di TMDB    : {not_found_count}")
    print(f"Tanpa detail cukup di TMDB : {no_detail_count}")
    print(f"File SQL diperbarui        : {SQL_FILE_PATH}")
    print(f"Backup tersimpan sebagai   : {backup_path}")
    print("=============================================\n")


if __name__ == "__main__":
    main()
