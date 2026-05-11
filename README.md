# Transaksi Elektronik

Aplikasi website untuk backend FastAPI dan frontend Vue 3 yang digunakan sebagai sistem transaksi elektronik.

## Struktur Proyek

- `backend/` - kode backend Python dengan FastAPI, SQLAlchemy, dan integrasi database.
- `frontend/` - aplikasi frontend Vue 3 yang dibangun dengan Vite.
- `test.db` - database SQLite contoh (jika digunakan untuk testing).

## Teknologi

- Backend: Python, FastAPI, SQLAlchemy, Uvicorn
- Frontend: Vue 3, Vite
- Database: MySQL / PostgreSQL / SQLite (tergantung konfigurasi `DATABASE_URL`)

## Prasyarat

- Python 3.10+ atau versi yang kompatibel dengan dependensi `backend/requirements.txt`
- Node.js 18+ dan npm/yarn untuk frontend
- Database MySQL atau PostgreSQL yang tersedia jika menggunakan `DATABASE_URL` di `.env`

## Setup Backend

1. Buka terminal dan masuk ke folder backend:

```bash
cd backend
```

2. Buat virtual environment dan aktifkan:

```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependensi:

```bash
pip install -r requirements.txt
```

4. Buat file `.env` di dalam folder `backend/` dengan variabel berikut:

```env
DATABASE_URL=mysql+pymysql://username:password@localhost/nama_database
```

Atau untuk PostgreSQL:

```env
DATABASE_URL=postgresql://username:password@localhost/nama_database
```

5. Inisialisasi database (opsional, jika ada script migrasi / pembuatan tabel):

```bash
python database.py
```

6. Jalankan backend:

```bash
uvicorn main:app --reload 
```

Backend akan tersedia di:

- `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Setup Frontend

1. Buka terminal dan masuk ke folder frontend:

```bash
cd frontend
```

2. Install dependensi frontend:

```bash
npm install
```

3. Jalankan frontend development server:

```bash
npm run dev
```

Secara default, frontend akan berjalan di `http://localhost:5173`.

## Notes

- Backend sudah mengizinkan CORS untuk `http://localhost:5173` dan `http://localhost:5174`.
- Pastikan backend dan frontend dijalankan secara terpisah di dua terminal berbeda.
- Jika menggunakan database lokal, pastikan service database sudah berjalan dan kredensial di `.env` sesuai.

## Router & Fitur Utama Backend

Backend menggabungkan beberapa router API:

- `auth` - autentikasi dan otorisasi pengguna
- `inventory` - manajemen inventaris
- `transaction` - transaksi penjualan
- `kontrak` - pembuatan dan manajemen kontrak
- `io_system` - sistem input/output terkait file atau dokumen
- `deteksi_uang` - modul deteksi uang palsu
- `midtrans_payment` - integrasi pembayaran Midtrans
- `laporan` - laporan sistem

## Testing

Sistem ini belum memiliki suite testing resmi, tetapi ada contoh skrip validasi sederhana di root:

```bash
python test_auth.py
```

Skrip ini mengecek model request untuk autentikasi di backend.

## Deployment

Untuk menjalankan backend di lingkungan produksi, jangan gunakan `--reload`.
Gunakan perintah seperti berikut:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Jika ingin menjalankan frontend untuk produksi, build lalu preview:

```bash
cd frontend
npm run build
npm run preview
```

> Untuk produksi, disarankan menggunakan reverse proxy seperti Nginx dan database yang terkonfigurasi dengan benar.

## Cara Menggunakan

1. Jalankan backend dahulu.
2. Jalankan frontend.
3. Buka browser ke alamat frontend dan gunakan aplikasi.

Jika Anda ingin bantuan lebih lanjut untuk konfigurasi `.env` atau database, beri tahu saya.
