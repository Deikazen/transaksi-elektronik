from backend.database import SessionLocal
from backend.models import Produk

db = SessionLocal()

# Buat data baru
produk_baru = Produk(nama_produk="Kopi Hitam", harga=5000, stok=10)

# Simpan ke database
db.add(produk_baru)
db.commit()
db.refresh(produk_baru)

print(f"Berhasil tambah produk dengan ID: {produk_baru.id}")
db.close()
