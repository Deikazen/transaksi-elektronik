import os
import sys
import asyncio

# Set up relative paths to import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.database import SessionLocal
from backend.models import Transaksi, Kontrak
from backend.routers.transaction import generate_pdf_receipt

def fix_missing_pdfs():
    db = SessionLocal()
    try:
        # Find transactions that have contracts
        transaksis = db.query(Transaksi).all()
        for trx in transaksis:
            kontrak = db.query(Kontrak).filter(Kontrak.transaksi_id == trx.id).first()
            if kontrak:
                pdf_path = os.path.join(os.path.dirname(__file__), "backend", "data", "contracts", f"{kontrak.kode}.pdf")
                if not os.path.exists(pdf_path):
                    print(f"[*] PDF hilang untuk {kontrak.kode} (Trx {trx.kode}). Menghapus kontrak lama dan meregenerasi...")
                    db.delete(kontrak)
                    db.commit()
                    # Generate ulang
                    generate_pdf_receipt(trx.id)
                    print(f"[+] Berhasil meregenerasi PDF untuk {trx.kode}.")
                else:
                    print(f"[OK] PDF sudah ada untuk {kontrak.kode}.")
    finally:
        db.close()

if __name__ == "__main__":
    fix_missing_pdfs()
