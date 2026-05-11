import os
from sqlalchemy import text
from database import engine

def migrate():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE transaksi ADD COLUMN metode_pembayaran VARCHAR(50) DEFAULT 'tunai'"))
            print("Added metode_pembayaran")
        except Exception as e:
            print("Skipped metode_pembayaran:", e)

        try:
            conn.execute(text("ALTER TABLE transaksi ADD COLUMN jumlah_bayar INTEGER DEFAULT 0"))
            print("Added jumlah_bayar")
        except Exception as e:
            print("Skipped jumlah_bayar:", e)

        try:
            conn.execute(text("ALTER TABLE transaksi ADD COLUMN kembalian INTEGER DEFAULT 0"))
            print("Added kembalian")
        except Exception as e:
            print("Skipped kembalian:", e)
        conn.commit()

if __name__ == "__main__":
    migrate()
