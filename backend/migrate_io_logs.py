import os
import sys
from sqlalchemy.orm import Session
from datetime import timedelta

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import SessionLocal
from models import Transaksi, ItemTransaksi, Kontrak, IOLog

def migrate():
    db = SessionLocal()
    try:
        txs = db.query(Transaksi).all()
        print(f"Found {len(txs)} transactions to migrate logs for.")
        
        for tx in txs:
            # Check if logs already exist for this transaction
            exists = db.query(IOLog).filter(IOLog.transaction_kode == tx.kode).first()
            if exists:
                print(f"Logs for {tx.kode} already exist, skipping.")
                continue
            
            items = db.query(ItemTransaksi).filter(ItemTransaksi.transaksi_id == tx.id).all()
            kontrak = db.query(Kontrak).filter(Kontrak.transaksi_id == tx.id).first()
            
            base_time = tx.created_at
            
            logs = [
                IOLog(
                    timestamp=base_time, action="INPUT", source="frontend", target="api",
                    description=f"POST /transaction/ — Klien: '{tx.nama_klien}', Items: {len(items)}",
                    transaction_kode=tx.kode, status="success", data_size=f"{len(tx.nama_klien)*2 + len(items)*20} B"
                ),
                IOLog(
                    timestamp=base_time + timedelta(milliseconds=15), action="PROCESS", source="api", target="database",
                    description=f"Validasi stok & harga untuk {len(items)} produk",
                    transaction_kode=tx.kode, status="success"
                ),
                IOLog(
                    timestamp=base_time + timedelta(milliseconds=42), action="PROCESS", source="api", target="database",
                    description=f"INSERT {tx.kode} + {len(items)} items — Atomic commit",
                    transaction_kode=tx.kode, status="success"
                ),
                IOLog(
                    timestamp=base_time + timedelta(milliseconds=55), action="OUTPUT", source="api", target="frontend",
                    description=f"201 Created — Transaksi {tx.kode} berhasil diproses",
                    transaction_kode=tx.kode, status="success", data_size="512 B"
                )
            ]
            
            if kontrak:
                logs.append(IOLog(
                    timestamp=base_time + timedelta(milliseconds=60), action="PROCESS", source="background", target="api",
                    description=f"BackgroundTask: Memulai pembuatan PDF struk untuk {tx.kode}",
                    transaction_kode=tx.kode, status="success"
                ))
                logs.append(IOLog(
                    timestamp=base_time + timedelta(milliseconds=120), action="OUTPUT", source="background", target="database",
                    description=f"Kontrak {kontrak.kode} berhasil dibuat & diarsip. Hash: {kontrak.hash_doc[:16]}...",
                    transaction_kode=tx.kode, status="success"
                ))
            
            db.add_all(logs)
            print(f"Migrated logs for {tx.kode}")
            
        db.commit()
        print("Migration complete!")
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
