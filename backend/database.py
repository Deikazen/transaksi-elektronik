from sqlalchemy import create_engine
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
    import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# tabel database
class Produk(Base):
    __tablename__ = "produk"
    id = Column(Integer, primary_key=True, index=True)
    nama_produk = Column(String(255), index=True)
    harga = Column(Integer)
    stok = Column(Integer)


if __name__ == "__main__":
    init_db()
    print("Database & semua tabel berhasil dibuat!")
