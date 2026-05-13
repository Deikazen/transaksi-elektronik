"""
migrate_add_ppn.py
Alembic-free migration script untuk menambah kolom ppn dan grand_total
ke tabel transaksi pada database yang sudah existing.

Usage:
    cd backend
    python -m backend.migrate_add_ppn

Atau langsung:
    python migrate_add_ppn.py

Script ini AMAN dijalankan berulang kali (idempotent) —
akan skip jika kolom sudah ada.
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# ── Load environment ──────────────────────────────────────
backend_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(backend_dir, '.env'))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("X DATABASE_URL tidak ditemukan di .env")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

def run_migration():
    """Tambah kolom ppn dan grand_total ke tabel transaksi."""
    inspector = inspect(engine)

    # Cek apakah tabel transaksi ada
    if "transaksi" not in inspector.get_table_names():
        print("! Tabel 'transaksi' belum ada. Jalankan init_db() dulu.")
        print("  Membuat semua tabel dari models.py ...")
        from database import Base
        import models  # noqa: F401 — import supaya semua model ter-register
        Base.metadata.create_all(bind=engine)
        print("OK Semua tabel berhasil dibuat (termasuk kolom ppn & grand_total).")
        return

    # Cek kolom yang sudah ada
    existing_columns = [col["name"] for col in inspector.get_columns("transaksi")]
    print(f"Info: Kolom existing di 'transaksi': {existing_columns}")

    # ── Detect dialect (MySQL vs PostgreSQL vs SQLite) ──
    dialect = engine.dialect.name  # 'mysql', 'postgresql', 'sqlite'
    print(f"Info: Database dialect: {dialect}")

    with engine.begin() as conn:
        # ── Tambah kolom ppn ──
        if "ppn" not in existing_columns:
            if dialect == "sqlite":
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN ppn INTEGER DEFAULT 0"))
            else:
                # MySQL / PostgreSQL
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN ppn INTEGER DEFAULT 0"))
            print("OK Kolom 'ppn' berhasil ditambahkan.")
        else:
            print("Info: Kolom 'ppn' sudah ada, skip.")

        # ── Tambah kolom grand_total ──
        if "grand_total" not in existing_columns:
            if dialect == "sqlite":
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN grand_total INTEGER DEFAULT 0"))
            else:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN grand_total INTEGER DEFAULT 0"))
            print("OK Kolom 'grand_total' berhasil ditambahkan.")
        else:
            print("Info: Kolom 'grand_total' sudah ada, skip.")

        # ── Backfill existing data ──
        # Untuk data lama: kolom `total` dulunya menyimpan grand_total,
        # jadi kita set grand_total = total, lalu hitung ulang ppn & subtotal
        result = conn.execute(text(
            "SELECT COUNT(*) FROM transaksi WHERE grand_total = 0 OR grand_total IS NULL"
        ))
        count = result.scalar()

        if count > 0:
            print(f"Info: Backfilling {count} baris data lama...")

            # total lama = grand_total (harga sudah termasuk pajak)
            # Hitung balik: subtotal = round(grand_total / 1.11)
            #                ppn     = grand_total - subtotal
            if dialect == "sqlite":
                conn.execute(text("""
                    UPDATE transaksi
                    SET grand_total = total,
                        ppn = total - CAST(ROUND(total / 1.11) AS INTEGER)
                    WHERE grand_total = 0 OR grand_total IS NULL
                """))
            elif dialect == "mysql":
                conn.execute(text("""
                    UPDATE transaksi
                    SET grand_total = total,
                        ppn = total - ROUND(total / 1.11)
                    WHERE grand_total = 0 OR grand_total IS NULL
                """))
            else:
                # PostgreSQL
                conn.execute(text("""
                    UPDATE transaksi
                    SET grand_total = total,
                        ppn = total - ROUND(total / 1.11)
                    WHERE grand_total = 0 OR grand_total IS NULL
                """))

            print("OK Backfill selesai. Data lama sudah disesuaikan.")
        else:
            print("Info: Tidak ada data yang perlu di-backfill.")

    print("\nMigrasi selesai!")


if __name__ == "__main__":
    run_migration()
