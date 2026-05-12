# 🚀 SecureTransact - Sistem Transaksi Elektronik & POS

SecureTransact adalah aplikasi web komprehensif untuk mengelola **Sistem Transaksi Elektronik** dan **Point of Sale (POS)**. Aplikasi ini dirancang dengan pendekatan *Secure by Design*, memiliki berbagai modul lanjutan seperti pembuatan kontrak otomatis, integrasi Payment Gateway Midtrans, serta Computer Vision untuk mendeteksi keaslian fisik uang tunai.

Dibangun menggunakan arsitektur modern: **FastAPI (Python)** sebagai Backend dan **Vue 3 + Vite** sebagai Frontend.

---

## ✨ Fitur Utama

- 🛒 **Point of Sale (POS)** - Proses transaksi kasir yang cepat, kalkulasi pajak (PPN), dan diskon.
- 📦 **Manajemen Inventaris** - Kelola stok barang dengan pencarian barcode.
- 📜 **Generate Kontrak Digital** - Pembuatan otomatis PDF Kontrak dengan algoritma hashing `SHA-256` (*ReportLab*).
- 💳 **Payment Gateway Midtrans** - Dukungan multi-payment: E-Wallet (Gopay, OVO, Dana), QRIS, Virtual Account, dan Kartu Kredit.
- 👁️ **Computer Vision** - Modul AI berbasis OpenCV untuk memeriksa keaslian dan nominal uang kertas.
- 🛡️ **Keamanan (Secure by Design)** - Autentikasi JWT, password hashing (*bcrypt*), Role-Based Access Control (RBAC), dan *input validation*.
- 📊 **Pelaporan & Export** - Analytics penjualan dan fitur export data ke CSV.

---

## 🏗️ Struktur Proyek

- `/backend` - Logika *server-side* berbasis Python (FastAPI).
- `/frontend` - Tampilan *client-side* berbasis Vue 3 (Vite).

---

## ⚙️ Persyaratan Sistem

Pastikan environment Anda telah terinstal perangkat lunak berikut:
- **Python 3.10+**
- **Node.js 18+** & npm / yarn
- **Database** (SQLite bawaan, MySQL, atau PostgreSQL)

---

## 🚀 Panduan Instalasi & Menjalankan Aplikasi

### 1. Setup Backend

Buka terminal baru dan masuk ke direktori backend:

```bash
cd backend
```

**Buat & Aktifkan Virtual Environment:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

**Install Dependensi:**
```bash
pip install -r requirements.txt
```

**Konfigurasi Environment (`.env`):**
Buat file `.env` di dalam folder `backend/` dan sesuaikan nilainya:
```ini
# Database Config (Gunakan sqlite untuk testing cepat)
DATABASE_URL=sqlite:///./pos.db
# Atau MySQL: DATABASE_URL=mysql+pymysql://user:pass@localhost/namadb

# JWT Secret Key (Ubah dengan string acak yang aman)
SECRET_KEY="GANTI_DENGAN_KUNCI_RAHASIA_ANDA"

# Midtrans Configuration (Untuk Payment Gateway)
MIDTRANS_SERVER_KEY="SB-Mid-server-xxxxxxxxxxxxxxxx"
MIDTRANS_CLIENT_KEY="SB-Mid-client-xxxxxxxxxxxxxxxx"
MIDTRANS_IS_PRODUCTION=false
```

**Jalankan Backend Server:**
```bash
uvicorn main:app --reload --port 8000
```
*Backend akan berjalan di: `http://localhost:8000` (Swagger UI: `http://localhost:8000/docs`)*

---

### 2. Setup Frontend

Buka terminal terpisah dan masuk ke direktori frontend:

```bash
cd frontend
```

**Install Dependensi Node Modules:**
```bash
npm install
```

**Jalankan Frontend Server:**
```bash
npm run dev
```
*Frontend akan berjalan di: `http://localhost:5173`*

---

## 🔐 Akun Default (Login)
Saat aplikasi pertama kali dijalankan, sistem secara otomatis men-generate akun berikut jika menggunakan `sqlite`:
- **Admin**: `admin` / `admin123`
- **Manajer**: `manajer1` / `manajer123`
- **Kasir**: `kasir1` / `kasir123`

---

## 📚 Stack Teknologi
**Backend:**
- `FastAPI` (Web Framework)
- `SQLAlchemy` (ORM)
- `Pydantic` (Data Validation)
- `ReportLab` (PDF Generator)
- `OpenCV` (Computer Vision)
- `Passlib` & `Jose` (Security)

**Frontend:**
- `Vue 3` (Composition API)
- `Vite` (Build Tool)
- `Lucide-Vue-Next` (Icons)
- `Vanilla CSS` (Custom Styling - *Glassmorphism & Dark Mode*)
