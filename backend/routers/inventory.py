from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db, Produk

router = APIRouter(prefix="/inventory", tags=["Inventory"])

class ProdukCreate(BaseModel):
    nama_produk: str
    harga: int
    stok: int

class ProdukUpdate(BaseModel):
    nama_produk: Optional[str] = None
    harga: Optional[int] = None
    stok: Optional[int] = None

@router.get("/")
def get_inventory(db: Session = Depends(get_db)):
    items = db.query(Produk).all()
    return {"status": "success", "data": items}

@router.get("/{item_id}")
def get_inventory_by_id(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Produk).filter(Produk.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    return {"status": "success", "data": item}

@router.post('/')
def create_inventory(item: ProdukCreate, db: Session = Depends(get_db)):
    new_produk = Produk(
        nama_produk=item.nama_produk,
        harga=item.harga,
        stok=item.stok
    )

    db.add(new_produk)
    db.commit()
    db.refresh(new_produk)

    return {"status": "success", "data": new_produk }

@router.put("/{item_id}")
def update_inventory(item_id: int, item_data: ProdukUpdate, db: Session = Depends(get_db)):
    item = db.query(Produk).filter(Produk.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    
    if item_data.nama_produk is not None:
        item.nama_produk = item_data.nama_produk
    if item_data.harga is not None:
        item.harga = item_data.harga
    if item_data.stok is not None:
        item.stok = item_data.stok
        
    db.commit()
    db.refresh(item)
    return {"status": "success", "data": item}

@router.delete("/{item_id}")
def delete_inventory(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Produk).filter(Produk.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
        
    db.delete(item)
    db.commit()
    return {"status": "success", "message": "Produk berhasil dihapus"}