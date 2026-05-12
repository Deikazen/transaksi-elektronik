# Arsitektur Proyek SecureTransact

Dokumen ini menjelaskan struktur desain dan arsitektur dari aplikasi SecureTransact. Arsitektur didesain dengan konsep **Monolithic Terpisah** (Backend API dan Frontend Client berjalan secara independen) untuk mempermudah _scaling_ dan pemeliharaan.

---

## 1. High-Level Architecture (C4 Model - System Context)

Diagram ini menunjukkan gambaran besar bagaimana komponen sistem berinteraksi dengan dunia luar (User dan layanan pihak ketiga seperti Midtrans).

```mermaid
graph TD
    classDef frontend fill:#41B883,stroke:#35495E,stroke-width:2px,color:white;
    classDef backend fill:#059669,stroke:#047857,stroke-width:2px,color:white;
    classDef external fill:#F59E0B,stroke:#D97706,stroke-width:2px,color:white;
    classDef db fill:#3B82F6,stroke:#2563EB,stroke-width:2px,color:white;
    classDef actor fill:#8B5CF6,stroke:#7C3AED,stroke-width:2px,color:white;

    User(("Kasir / Admin")):::actor

    subgraph System ["SecureTransact System"]
        SPA["Frontend Application<br>(Vue 3 + Vite)"]:::frontend
        API["Backend API Gateway<br>(FastAPI / Python)"]:::backend
        DB[("Database<br>(SQLite / MySQL)")]:::db
        PDFSys["PDF Generation<br>(ReportLab)"]:::backend
        CVSys["Computer Vision<br>(OpenCV)"]:::backend
    end

    Midtrans["Midtrans API<br>(Payment Gateway)"]:::external

    User <-->|"Berinteraksi (UI)"| SPA
    SPA <-->|"REST API"| API
    
    API <-->|"SQLAlchemy ORM"| DB
    API -->|"Generate File"| PDFSys
    API -->|"Analyze Image"| CVSys
    
    API -->|"Request Token"| Midtrans
    Midtrans -.->|"Webhook Notification"| API
    Midtrans <-->|"Popup Payment"| SPA
```

> **Alur Kerja Utama:** Frontend SPA berinteraksi dengan API FastAPI. API ini kemudian bertugas melakukan operasi ke Database, memanggil AI Vision untuk deteksi uang, membuat dokumen PDF (Kontrak), serta berkoordinasi dengan Midtrans untuk pembuatan Token Pembayaran.

---

## 2. Entity Relationship Diagram (ERD)

Struktur tabel relasional di dalam Database (SQLite/MySQL). Tabel didesain untuk mencatat siapa yang melakukan transaksi, item apa saja yang dibeli, dan kontrak digital mana yang terikat pada transaksi tersebut.

```mermaid
erDiagram
    USERS ||--o{ TRANSAKSI : "melayani"
    USERS {
        int id PK
        string username
        string email
        string hashed_pw
        string role "admin|manajer|kasir"
        boolean is_active
    }

    PRODUK ||--o{ ITEM_TRANSAKSI : "dibeli dalam"
    PRODUK {
        int id PK
        string nama_produk
        int harga
        int stok
        string barcode
    }

    TRANSAKSI ||--o{ ITEM_TRANSAKSI : "memiliki"
    TRANSAKSI ||--o| KONTRAK : "diikat oleh"
    TRANSAKSI {
        int id PK
        string kode "TRX..."
        string nama_klien
        int total
        int diskon_persen
        int diskon_nominal
        int ppn
        int grand_total
        string metode_pembayaran
        string status "pending|lunas|batal"
        int kasir_id FK
    }

    ITEM_TRANSAKSI {
        int id PK
        int transaksi_id FK
        int produk_id FK
        string nama_produk
        int qty
        int harga
    }

    KONTRAK {
        int id PK
        string kode "KTR..."
        int transaksi_id FK
        string nama_klien
        string hash_doc "SHA-256"
        datetime created_at
    }
```

> Hubungan `TRANSAKSI` ke `KONTRAK` adalah *One-to-One* (Satu transaksi memiliki maksimal satu kontrak digital PDF yang di-hash).

---

## 3. Workflow Sequence: Transaksi & Payment Gateway

Proses krusial dari saat pengguna melakukan checkout di Frontend, menampilkan Midtrans, hingga dokumen kontrak selesai di-generate oleh sistem.

```mermaid
sequenceDiagram
    autonumber
    actor Kasir
    participant Frontend as Vue Frontend
    participant Backend as FastAPI
    participant Database as Database
    participant Midtrans as Midtrans API

    Kasir->>Frontend: Klik "Checkout" (Pilih E-Wallet)
    Frontend->>Backend: POST /transaction (Kirim Items & Klien)
    
    Backend->>Database: Insert Transaksi (Status: pending)
    Database-->>Backend: Transaksi ID
    Backend-->>Frontend: Transaksi Created
    
    Frontend->>Backend: POST /payment/create-snap-token
    Backend->>Midtrans: Request Snap Token (Kirim Harga & Items)
    Midtrans-->>Backend: Return Snap Token
    Backend-->>Frontend: Return Snap Token
    
    Frontend->>Frontend: Execute window.snap.pay(Token)
    Frontend->>Midtrans: Munculkan Popup Midtrans
    Kasir->>Midtrans: Scan QRIS / Konfirmasi Bayar
    
    Midtrans-->>Frontend: onSuccess Callback
    Frontend->>Backend: GET /transaction (Check)
    
    %% Async Webhook Process
    par Proses Asinkron (Webhook)
        Midtrans-)Backend: Webhook POST /payment/notification
        Backend->>Database: Update Status Transaksi = "lunas"
        Backend->>Backend: [Background Task] Generate PDF Kontrak
        Backend->>Database: Insert Kontrak (SHA-256 Hash)
    end
    
    Backend-->>Frontend: Status Transaksi: Lunas & Info Hash
    Frontend-->>Kasir: Tampilkan Struk & Hash Kontrak Digital
```

> Sistem sengaja mendesain *Pembuatan PDF Kontrak* sebagai **Background Task** (`BackgroundTasks` di FastAPI) agar API respon tidak melambat atau terblokir saat sistem sibuk me-render dokumen PDF.

---

## 4. Mengapa Arsitektur Ini Disebut "Secure by Design"?

Proyek ini dibangun dari awal dengan mengintegrasikan konsep keamanan di setiap lapisannya (Defense in Depth). Berikut adalah implementasi *Secure by Design* pada arsitektur di atas:

### A. Layered Security Model (Diagram)

```mermaid
flowchart TD
    classDef secure fill:#1E293B,stroke:#3B82F6,stroke-width:2px,color:white;
    classDef core fill:#0F172A,stroke:#10B981,stroke-width:2px,color:white;
    classDef warning fill:#7F1D1D,stroke:#DC2626,stroke-width:2px,color:white;
    
    Client((User Frontend)) -->|"1. Bearer JWT"| Auth[Lapisan Autentikasi]:::secure
    Auth -->|"2. Cek Role (RBAC)"| RBAC[Lapisan Otorisasi]:::secure
    RBAC -->|"3. Filter Tipe Data"| Pydantic[Lapisan Validasi Pydantic]:::secure
    Pydantic -->|"4. SQL Params"| ORM[Lapisan SQLAlchemy]:::core
    ORM --> Database[(Database)]:::core
    
    Hacker((Malicious Payload)):::warning -.->|"Gagal Validasi"| Pydantic
    Hacker -.->|"SQL Injection Blocked"| ORM
    
    Webhook((Webhook Pembayaran)) -->|"5. Cek SHA-512 Signature"| Signature[Validasi Signature Midtrans]:::secure
    Signature --> ORM
```

### B. Prinsip Keamanan yang Diterapkan

1. **Pemisahan Logika (Separation of Concerns)**
   *Frontend* sama sekali tidak memiliki akses langsung ke *Database*. Akses hanya terjadi via REST API, yang mana mengurangi risiko jika *Frontend* disusupi.

2. **Validasi Input Ketat (Pydantic & FastAPI)**
   Semua data yang dikirim (*Payload JSON*) disaring dengan ketat secara tipe data dan strukturnya oleh `Pydantic`. Data yang aneh/berbahaya akan otomatis ditolak dengan kode `422 Unprocessable Entity` sebelum menyentuh logika bisnis. Ini menangkal ancaman seperti *SQL Injection* atau eksploitasi parameter.

3. **Autentikasi Stateless (JWT) & Enkripsi Kredensial**
   Password tidak pernah disimpan secara teks mentah (plaintext), melainkan di-hash menggunakan algoritma `Bcrypt` (library *Passlib*). Sesi dipertahankan menggunakan JWT yang tidak bisa dimanipulasi (*Tamper-proof*) karena memiliki signature dari server.

4. **Role-Based Access Control (RBAC)**
   Adanya aturan ketat: Kasir tidak bisa mendaftarkan user baru atau menghapus transaksi. Modul `/users` hanya bisa diakses oleh token dengan role `admin`. Hal ini menerapkan prinsip *Principle of Least Privilege*.

5. **Integritas Dokumen Kriptografi (SHA-256 Kontrak)**
   Sistem Kontrak Digital tidak hanya menghasilkan PDF, tetapi menciptakan jejak *Hash SHA-256* atas PDF tersebut ke database. Jika ada pihak yang memanipulasi file PDF di masa depan, Hash-nya tidak akan sama dengan yang dicatat oleh database. Ini memastikan hukum **Non-repudiation** (tidak bisa disangkal).

6. **Keamanan Eksternal (Webhook Anti-Spoofing)**
   Tidak sembarang orang bisa menebak *URL Webhook Midtrans* dan memalsukan pembayaran. Endpoint `/payment/notification` secara ketat memverifikasi `Signature Key` (menggunakan algoritma hashing `SHA-512` dengan menggabungkan ID Order, Harga, dan Server Key). Jika signature tidak cocok, request ditolak.
