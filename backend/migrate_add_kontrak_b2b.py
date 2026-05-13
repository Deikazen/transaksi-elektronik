"""
migrate_add_kontrak_b2b.py
Script untuk membuat tabel kontrak_b2b di database.
Jalankan: python backend/migrate_add_kontrak_b2b.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import Base, engine
from backend.models import KontrakB2B  # noqa: F401 – pastikan model ter-import

print("Membuat tabel kontrak_b2b...")
Base.metadata.create_all(bind=engine)
print("✅ Tabel kontrak_b2b berhasil dibuat (atau sudah ada).")
