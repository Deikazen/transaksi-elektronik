from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

# ============================================================
# ENUM untuk role user (RBAC)
# ============================================================
class RoleEnum(str, enum.Enum):
    admin    = "admin"     # akses penuh
    kasir    = "kasir"     # bisa akses POS & inventory, ga bisa manage user
    manajer  = "manajer"   # bisa lihat semua, ga bisa ubah data

# ============================================================
# Model User
# ============================================================
class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String(100), unique=True, index=True, nullable=False)
    email      = Column(String(255), unique=True, index=True, nullable=False)
    hashed_pw  = Column(String(255), nullable=False)
    role       = Column(Enum(RoleEnum), default=RoleEnum.kasir, nullable=False)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # relasi ke transaksi (opsional, untuk audit trail)
    transaksi  = relationship("Transaksi", back_populates="kasir")

# ============================================================
# Model Produk (dipindah dari database.py ke sini biar rapi)
# ============================================================
class Produk(Base):
    __tablename__ = "produk"

    id          = Column(Integer, primary_key=True, index=True)
    nama_produk = Column(String(255), index=True, nullable=False)
    barcode     = Column(String(100), unique=True, index=True, nullable=True) # Barcode scanner support
    kategori    = Column(String(100), default="Umum")       # kategori produk
    harga       = Column(Integer, nullable=False)
    stok        = Column(Integer, default=0)
    is_active   = Column(Boolean, default=True)

# ============================================================
# Model Transaksi
# ============================================================
class Transaksi(Base):
    __tablename__ = "transaksi"

    id          = Column(Integer, primary_key=True, index=True)
    kode        = Column(String(20), unique=True, index=True)  # misal TRX001
    nama_klien  = Column(String(255), nullable=False)
    total       = Column(Integer, nullable=False)           # subtotal (sebelum pajak)
    diskon_persen  = Column(Integer, default=0)             # diskon persentase (0-100)
    diskon_nominal = Column(Integer, default=0)             # diskon dalam rupiah
    ppn         = Column(Integer, default=0)                # PPN 11%
    grand_total = Column(Integer, default=0)                # total - diskon + ppn
    status      = Column(String(50), default="lunas")
    metode_pembayaran = Column(String(50), default="tunai") # tunai, debit, e-wallet, qris
    jumlah_bayar = Column(Integer, default=0)
    kembalian   = Column(Integer, default=0)
    kasir_id    = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    kasir       = relationship("User", back_populates="transaksi")
    items       = relationship("ItemTransaksi", back_populates="transaksi")
    kontrak     = relationship("Kontrak", back_populates="transaksi", uselist=False)

# ============================================================
# Model Item Transaksi (detail per produk dalam 1 transaksi)
# ============================================================
class ItemTransaksi(Base):
    __tablename__ = "item_transaksi"

    id           = Column(Integer, primary_key=True, index=True)
    transaksi_id = Column(Integer, ForeignKey("transaksi.id"))
    produk_id    = Column(Integer, ForeignKey("produk.id"))
    nama_produk  = Column(String(255))   # snapshot nama saat transaksi
    harga        = Column(Integer)       # snapshot harga saat transaksi
    qty          = Column(Integer)

    transaksi    = relationship("Transaksi", back_populates="items")

# ============================================================
# Model Kontrak
# ============================================================
class Kontrak(Base):
    __tablename__ = "kontrak"

    id           = Column(Integer, primary_key=True, index=True)
    kode         = Column(String(20), unique=True)  # misal KTR001
    transaksi_id = Column(Integer, ForeignKey("transaksi.id"), unique=True)
    nama_klien   = Column(String(255))
    hash_doc     = Column(String(255))  # hash kriptografi dokumen
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    transaksi    = relationship("Transaksi", back_populates="kontrak")

# ============================================================
# Model I/O Log (Pencatatan real-time I/O sistem)
# ============================================================
class IOLog(Base):
    __tablename__ = "io_logs"

    id               = Column(Integer, primary_key=True, index=True)
    timestamp        = Column(DateTime(timezone=True), server_default=func.now())
    action           = Column(String(50))   # INPUT | PROCESS | OUTPUT | ERROR
    source           = Column(String(100))  # frontend | api | database | background
    target           = Column(String(100))  # api | database | background | frontend
    description      = Column(Text)
    transaction_kode = Column(String(20), index=True, nullable=True)
    status           = Column(String(20))   # success | error | pending
    data_size        = Column(String(50), nullable=True)
    is_manual        = Column(Boolean, default=False)
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=True)

    user             = relationship("User")