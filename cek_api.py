import requests

# Ganti dengan API KEY kamu yang tadi
API_KEY = 'f25e8035a509c59ccc243f96b5237829' 

print("Mengecek API Key...")
try:
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}&language=en-US&page=1"
    response = requests.get(url)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ SUKSES! API Key valid.")
        print(f"Contoh data: {data['results'][0]['title']}")
    else:
        print("❌ GAGAL! Pesan error dari TMDB:")
        print(response.json())
        print("\nSOLUSI: Cek kembali API Key di website TMDB > Settings > API.")
        
except Exception as e:
    print(f"❌ ERROR PROGRAM: {e}")
    print("Pastikan internet nyala dan sudah 'pip install requests'")