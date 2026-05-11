"""
seed.py
Jalankan sekali untuk:
  1. Buat semua tabel di database
  2. Isi user default (admin, kasir, manajer)

Cara pakai:
    cd ..
    python -m backend.seed
"""
from database import init_db, SessionLocal
from models import User, RoleEnum, Produk
from core.security import hash_password

def seed():
    print("⏳ Membuat tabel...")
    init_db()
    print("✓  Tabel berhasil dibuat.\n")

    db = SessionLocal()

    # ── Default users ──────────────────────────────────────────
    default_users = [
        {"username": "admin",    "email": "admin@securetransact.local",    "password": "admin123",    "role": RoleEnum.admin},
        {"username": "kasir1",   "email": "kasir1@securetransact.local",   "password": "kasir123",   "role": RoleEnum.kasir},
        {"username": "manajer1", "email": "manajer1@securetransact.local", "password": "manajer123", "role": RoleEnum.manajer},
    ]

    print("👤 Membuat user default...")
    for u in default_users:
        existing = db.query(User).filter(User.username == u["username"]).first()
        if existing:
            print(f"   skip  → {u['username']} (sudah ada)")
            continue
        user = User(
            username  = u["username"],
            email     = u["email"],
            hashed_pw = hash_password(u["password"]),
            role      = u["role"],
        )
        db.add(user)
        print(f"   ✓     → {u['username']} [{u['role']}]")

    # ── Sample produk ──────────────────────────────────────────
    sample_produk = [
        {"nama_produk": "Laptop Gaming ASUS ROG",       "harga": 14500000, "stok": 8},
        {"nama_produk": "Monitor LG 27\" IPS",          "harga": 4200000,  "stok": 12},
        {"nama_produk": "Keyboard Mechanical Keychron", "harga": 1250000,  "stok": 20},
        {"nama_produk": "Mouse Logitech MX Master",     "harga": 850000,   "stok": 5},
        {"nama_produk": "Headset Sony WH-1000XM5",      "harga": 4999000,  "stok": 6},
        {"nama_produk": "SSD Samsung 1TB NVMe",         "harga": 1350000,  "stok": 15},
    ]

    print("\n📦 Mengisi sample produk...")
    existing_count = db.query(Produk).count()
    if existing_count > 0:
        print(f"   skip  → produk sudah ada ({existing_count} item)")
    else:
        for p in sample_produk:
            db.add(Produk(**p))
            print(f"   ✓     → {p['nama_produk']}")

    db.commit()
    db.close()

    print("\n✅ Seeding selesai!")
    print("\nCredential login:")
    print("  admin    / admin123    (role: admin)")
    print("  kasir1   / kasir123    (role: kasir)")
    print("  manajer1 / manajer123  (role: manajer)")

if __name__ == "__main__":
    seed()