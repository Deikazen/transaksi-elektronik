from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db, Transaksi, Produk

router = APIRouter(prefix="/transaction", tags=["Transaction"])

class TransaksiCreate(BaseModel):
    produk_id: int
    jumlah: int

class TransaksiUpdate(BaseModel):
    jumlah: Optional[int] = None

@router.get("/")
def get_transactions(db: Session = Depends(get_db)):
    transactions = db.query(Transaksi).all()
    return {"status": "success", "data": transactions}

@router.get("/{transaction_id}")
def get_transaction_by_id(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(Transaksi).filter(Transaksi.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    return {"status": "success", "data": transaction}

@router.post('/')
def create_transaction(transaction: TransaksiCreate, db: Session = Depends(get_db)):
    produk = db.query(Produk).filter(Produk.id == transaction.produk_id).first()
    if not produk:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
        
    if produk.stok < transaction.jumlah:
        raise HTTPException(status_code=400, detail="Stok produk tidak mencukupi")
        
    total_harga = produk.harga * transaction.jumlah
    
    # Kurangi stok
    produk.stok -= transaction.jumlah
    
    new_transaction = Transaksi(
        produk_id=transaction.produk_id,
        jumlah=transaction.jumlah,
        total_harga=total_harga
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return {"status": "success", "data": new_transaction}

@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(Transaksi).filter(Transaksi.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
        
    # Opsional: Kembalikan stok produk jika transaksi dihapus
    produk = db.query(Produk).filter(Produk.id == transaction.produk_id).first()
    if produk:
        produk.stok += transaction.jumlah
        
    db.delete(transaction)
    db.commit()
    return {"status": "success", "message": "Transaksi berhasil dihapus"}