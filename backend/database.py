from sqlalchemy import create_engine
# Tambahkan tipe data lain jika perlu
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

# Load .env from the backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(backend_dir, '.env'))

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    # Import semua model dulu sebelum create_all dipanggil
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    import models

    print("Mendaftarkan tabel secara eksplisit...")

    # Cara paksa: Ambil metadata langsung dari objek yang ada di models
    target_metadata = models.Base.metadata

    print(
        f"Tabel terdaftar di Metadata Models: {target_metadata.tables.keys()}")

    # Jalankan create_all menggunakan metadata dari models
    target_metadata.create_all(bind=engine)

    # Verifikasi fisik ke MySQL (Pastikan Laragon SUDAH START)
    from sqlalchemy import inspect
    inspector = inspect(engine)
    print(
        f"Tabel fisik di MySQL ({engine.url.database}): {inspector.get_table_names()}")
