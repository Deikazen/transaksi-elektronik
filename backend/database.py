from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import os
from dotenv import load_dotenv

load_dotenv()

# Ganti dengan URL database Anda
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency untuk mendapatkan session database
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
    
    transaksi = relationship("Transaksi", back_populates="produk")

class Transaksi(Base):
    __tablename__ = "transaksi"
    id = Column(Integer, primary_key=True, index=True)
    produk_id = Column(Integer, ForeignKey("produk.id"))
    jumlah = Column(Integer)
    total_harga = Column(Integer)
    
    produk = relationship("Produk", back_populates="transaksi")



if __name__ == "__main__":
    init_db() 