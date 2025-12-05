#!/usr/bin/env python3
"""
SQL to Excel Converter
Mengekstrak semua data INSERT dari file SQL dan mengekspornya ke file Excel
dengan sheet terpisah untuk setiap tabel.
"""

import re
import pandas as pd
from collections import defaultdict
import os

def parse_sql_file(filepath):
    """Parse SQL file dan ekstrak semua INSERT statements."""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Dictionary untuk menyimpan data per tabel
    tables_data = defaultdict(list)
    tables_columns = {}
    
    # Pattern untuk INSERT dengan kolom eksplisit
    # INSERT IGNORE INTO `table` (`col1`, `col2`, ...) VALUES (...)
    pattern_with_cols = re.compile(
        r"INSERT\s+IGNORE\s+INTO\s+`(\w+)`\s*\(([^)]+)\)\s*VALUES\s*\((.+?)\);",
        re.IGNORECASE | re.DOTALL
    )
    
    # Pattern untuk INSERT tanpa kolom (implicit)
    # INSERT IGNORE INTO `table` VALUES (...)
    pattern_no_cols = re.compile(
        r"INSERT\s+IGNORE\s+INTO\s+`(\w+)`\s+VALUES\s*\((.+?)\);",
        re.IGNORECASE | re.DOTALL
    )
    
    # Pattern untuk INSERT multi-row (Serial_TV style)
    pattern_multi_row = re.compile(
        r"INSERT\s+IGNORE\s+INTO\s+`(\w+)`\s+VALUES\s*(.+?);",
        re.IGNORECASE | re.DOTALL
    )
    
    # Definisi kolom untuk setiap tabel (berdasarkan schema basdat_movie_schema.sql)
    table_schemas = {
        'Paket_Langganan': ['nama_paket', 'harga_bulanan', 'maks_resolusi', 'maks_perangkat'],
        'Kartu_Kredit': ['nomor_kartu', 'jenis', 'empat_digit_nomor', 'tanggal_kadaluarsa'],
        'Pelanggan': ['email', 'nama_lengkap', 'tanggal_lahir', 'nama_paket', 'nomor_kartu'],
        'Profil': ['email_pelanggan', 'nama', 'kategori_usia'],
        'Genre': ['genre_id', 'nama_genre'],
        'Aktor': ['nama_lengkap', 'tanggal_lahir', 'negara_asal'],
        'Konten': ['judul', 'sinopsis', 'tahun_rilis', 'rating_usia', 'type'],
        'Film': ['judul', 'durasi', 'sutradara'],
        'Serial_TV': ['judul', 'total_season'],
        'Episode': ['judul', 'judul_episode', 'nomor_season', 'nomor_urut_episode', 'sinopsis', 'durasi'],
        'Genre_Konten': ['judul', 'genre_id'],
        'Peran': ['nama_aktor', 'judul', 'peran'],
        'Menonton': ['email_pelanggan', 'nama_profil', 'judul_konten', 'waktu_terakhir', 'posisi_terakhir'],
        'Subtitle': ['judul', 'bahasa_subtitle'],
        'Audio': ['judul', 'bahasa_audio'],
        'Transaksi': ['tanggal_pembayaran', 'biaya_tagihan', 'status', 'email_pelanggan'],
        'Rating': ['email_pelanggan', 'nama_profil', 'judul_konten', 'skor', 'komentar'],
    }
    
    def parse_values(values_str):
        """Parse value string menjadi list of values."""
        values = []
        current = ''
        in_string = False
        string_char = None
        paren_depth = 0
        i = 0
        
        while i < len(values_str):
            char = values_str[i]
            
            if not in_string:
                if char in ("'", '"'):
                    in_string = True
                    string_char = char
                    current += char
                elif char == '(':
                    paren_depth += 1
                    current += char
                elif char == ')':
                    paren_depth -= 1
                    current += char
                elif char == ',' and paren_depth == 0:
                    values.append(current.strip())
                    current = ''
                else:
                    current += char
            else:
                if char == string_char:
                    # Check for escaped quote
                    if i + 1 < len(values_str) and values_str[i + 1] == string_char:
                        current += char + string_char
                        i += 1
                    elif char == "'" and i > 0 and values_str[i-1] == '\\':
                        current += char
                    else:
                        in_string = False
                        current += char
                else:
                    current += char
            i += 1
        
        if current.strip():
            values.append(current.strip())
        
        # Clean up values
        cleaned = []
        for v in values:
            v = v.strip()
            if v.upper() == 'NULL':
                cleaned.append(None)
            elif v.upper() == 'NOW()':
                cleaned.append('NOW()')
            elif (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
                # Remove quotes dan unescape
                cleaned.append(v[1:-1].replace("\\'", "'").replace('\\"', '"').replace("''", "'"))
            else:
                # Numeric atau lainnya
                try:
                    if '.' in v:
                        cleaned.append(float(v))
                    else:
                        cleaned.append(int(v))
                except:
                    cleaned.append(v)
        
        return cleaned
    
    def parse_multi_row_values(values_str):
        """Parse multi-row values like ('a',1),('b',2)"""
        rows = []
        # Split by ),( pattern
        parts = re.split(r'\)\s*,\s*\(', values_str)
        for part in parts:
            # Clean up parentheses
            part = part.strip()
            if part.startswith('('):
                part = part[1:]
            if part.endswith(')'):
                part = part[:-1]
            if part:
                rows.append(parse_values(part))
        return rows
    
    # Process line by line untuk menangani berbagai format
    lines = content.split('\n')
    current_statement = ''
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('--'):
            continue
        
        current_statement += ' ' + line
        
        if ';' in line:
            stmt = current_statement.strip()
            current_statement = ''
            
            # Skip non-INSERT statements
            if not stmt.upper().startswith('INSERT'):
                continue
            
            # Try pattern with explicit columns first
            match = pattern_with_cols.search(stmt)
            if match:
                table_name = match.group(1)
                columns_str = match.group(2)
                values_str = match.group(3)
                
                # Parse columns
                columns = [c.strip().strip('`') for c in columns_str.split(',')]
                values = parse_values(values_str)
                
                if table_name not in tables_columns:
                    tables_columns[table_name] = columns
                
                tables_data[table_name].append(dict(zip(columns, values)))
                continue
            
            # Try pattern without columns (multi-row)
            match = pattern_multi_row.search(stmt)
            if match:
                table_name = match.group(1)
                values_section = match.group(2).strip()
                
                # Check if it's multi-row format
                if values_section.count('),(') > 0 or (values_section.startswith('(') and values_section.endswith(')')):
                    rows = parse_multi_row_values(values_section)
                    
                    # Get schema for this table
                    if table_name in table_schemas:
                        columns = table_schemas[table_name]
                    else:
                        columns = [f'col{i}' for i in range(len(rows[0]) if rows else 0)]
                    
                    for row in rows:
                        # Pad row if needed
                        while len(row) < len(columns):
                            row.append(None)
                        tables_data[table_name].append(dict(zip(columns[:len(row)], row)))
                else:
                    # Single row without parentheses wrapper
                    values = parse_values(values_section)
                    
                    if table_name in table_schemas:
                        columns = table_schemas[table_name]
                    else:
                        columns = [f'col{i}' for i in range(len(values))]
                    
                    while len(values) < len(columns):
                        values.append(None)
                    tables_data[table_name].append(dict(zip(columns[:len(values)], values)))
    
    return tables_data


def export_to_excel(tables_data, output_path):
    """Export data ke file Excel dengan sheet per tabel."""
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for table_name, rows in sorted(tables_data.items()):
            if rows:
                df = pd.DataFrame(rows)
                # Truncate sheet name if too long (Excel limit: 31 chars)
                sheet_name = table_name[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"✓ {table_name}: {len(rows)} rows exported")
            else:
                print(f"⚠ {table_name}: No data found")
    
    print(f"\n✅ File Excel berhasil dibuat: {output_path}")


def export_to_csv(tables_data, output_dir):
    """Export data ke file CSV terpisah per tabel."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    for table_name, rows in sorted(tables_data.items()):
        if rows:
            df = pd.DataFrame(rows)
            csv_path = os.path.join(output_dir, f"{table_name}.csv")
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"✓ {table_name}: {len(rows)} rows → {csv_path}")
    
    print(f"\n✅ File CSV berhasil dibuat di: {output_dir}")


def main():
    # Path file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(script_dir, 'IF2040_Milestone3_K1_G11.sql')
    excel_output = os.path.join(script_dir, 'basdat_movie_data.xlsx')
    csv_output_dir = os.path.join(script_dir, 'csv_output')
    
    print("=" * 60)
    print("SQL to Excel/CSV Converter")
    print("=" * 60)
    print(f"\nMembaca file: {sql_file}")
    
    # Parse SQL file
    tables_data = parse_sql_file(sql_file)
    
    print(f"\nDitemukan {len(tables_data)} tabel:")
    for table_name, rows in sorted(tables_data.items()):
        print(f"  • {table_name}: {len(rows)} rows")
    
    # Export ke Excel
    print("\n" + "-" * 60)
    print("Mengexport ke Excel...")
    print("-" * 60)
    export_to_excel(tables_data, excel_output)
    
    # Export ke CSV
    print("\n" + "-" * 60)
    print("Mengexport ke CSV...")
    print("-" * 60)
    export_to_csv(tables_data, csv_output_dir)
    
    print("\n" + "=" * 60)
    print("SELESAI!")
    print("=" * 60)
    print(f"\n📊 File Excel: {excel_output}")
    print(f"📁 Folder CSV: {csv_output_dir}")
    print("\nAnda bisa membuka file Excel di Google Sheets:")
    print("1. Buka Google Drive")
    print("2. Upload file basdat_movie_data.xlsx")
    print("3. Klik kanan → Open with → Google Sheets")


if __name__ == '__main__':
    main()
