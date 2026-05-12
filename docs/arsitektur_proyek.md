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
