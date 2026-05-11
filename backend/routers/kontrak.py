"""
routers/kontrak.py
Endpoint untuk digital contracts dengan SHA-256 verification
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import hashlib
import os

from database import get_db
from models import Kontrak, Transaksi, User
from core.deps import get_current_user

router = APIRouter(prefix="/kontrak", tags=["Kontrak"])

# ── Schema request/response ──────────────────────────────────
class KontrakCreate(BaseModel):
    transaksi_id: int
    nama_klien: str

class KontrakResponse(BaseModel):
    id: int
    kode: str
    transaksi_id: int
    nama_klien: str
    hash_doc: str
    created_at: datetime

    class Config:
        from_attributes = True

# ── Helper function to generate contract hash ──
def generate_contract_hash(kode: str, nama_klien: str, transaksi_id: int) -> str:
    """Generate SHA-256 hash for contract document"""
    content = f"{kode}|{nama_klien}|{transaksi_id}"
    return hashlib.sha256(content.encode()).hexdigest()

# ── Endpoint GET semua kontrak ────────────────────────────
@router.get("/")
def list_contracts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ambil semua kontrak yang sudah dibuat"""
    contracts = db.query(Kontrak).all()
    return {
        "status": "success",
        "data": [KontrakResponse.model_validate(c) for c in contracts]
    }

# ── Endpoint GET kontrak by ID ────────────────────────────
@router.get("/{kontrak_id}")
def get_contract(
    kontrak_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ambil detail kontrak berdasarkan ID"""
    contract = db.query(Kontrak).filter(Kontrak.id == kontrak_id).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kontrak tidak ditemukan."
        )
    
    # Get related transaksi
    transaksi = db.query(Transaksi).filter(Transaksi.id == contract.transaksi_id).first()
    
    return {
        "status": "success",
        "data": {
            **KontrakResponse.model_validate(contract).model_dump(),
            "transaksi": {
                "id": transaksi.id,
                "kode": transaksi.kode,
                "total": transaksi.total,
                "status": transaksi.status,
                "created_at": transaksi.created_at
            } if transaksi else None
        }
        }
    

# ── Endpoint GET PDF kontrak ────────────────────────────
@router.get("/{kontrak_id}/pdf")
def get_contract_pdf(
    kontrak_id: int,
    download: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ambil file PDF kontrak"""
    contract = db.query(Kontrak).filter(Kontrak.id == kontrak_id).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kontrak tidak ditemukan."
        )
    
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "contracts", f"{contract.kode}.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File PDF tidak ditemukan atau belum digenerate."
        )
        
    disposition = "attachment" if download else "inline"
    return FileResponse(
        path=pdf_path,
        filename=f"Kontrak_{contract.kode}.pdf",
        media_type="application/pdf",
        headers={"Content-Disposition": f"{disposition}; filename=Kontrak_{contract.kode}.pdf"}
    )

# ── Endpoint POST create kontrak ──────────────────────────
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_contract(
    payload: KontrakCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Buat kontrak baru untuk transaksi"""
    # Validasi transaksi exists
    transaksi = db.query(Transaksi).filter(Transaksi.id == payload.transaksi_id).first()
    if not transaksi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaksi tidak ditemukan."
        )
    
    # Generate kode kontrak (KTR001, KTR002, dst)
    last_kontrak = db.query(Kontrak).order_by(Kontrak.id.desc()).first()
    kode_number = (last_kontrak.id + 1) if last_kontrak else 1
    kode = f"KTR{kode_number:03d}"
    
    # Generate hash dokumen
    hash_doc = generate_contract_hash(kode, payload.nama_klien, payload.transaksi_id)
    
    # Create kontrak
    kontrak = Kontrak(
        kode=kode,
        transaksi_id=payload.transaksi_id,
        nama_klien=payload.nama_klien,
        hash_doc=hash_doc
    )
    db.add(kontrak)
    db.commit()
    db.refresh(kontrak)
    
    return {
        "status": "success",
        "message": f"Kontrak '{kode}' berhasil dibuat.",
        "data": KontrakResponse.model_validate(kontrak)
    }

# ── Endpoint untuk verify kontrak ────────────────────────
@router.post("/{kontrak_id}/verify")
def verify_contract(
    kontrak_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verifikasi kontrak dengan regenerasi hash"""
    contract = db.query(Kontrak).filter(Kontrak.id == kontrak_id).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kontrak tidak ditemukan."
        )
    
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "contracts", f"{contract.kode}.pdf")
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        expected_hash = hashlib.sha256(pdf_bytes).hexdigest()
    else:
        expected_hash = generate_contract_hash(contract.kode, contract.nama_klien, contract.transaksi_id)
        
    is_valid = expected_hash == contract.hash_doc
    
    return {
        "status": "success",
        "data": {
            "id": contract.id,
            "kode": contract.kode,
            "is_valid": is_valid,
            "pdf_exists": os.path.exists(pdf_path),
            "hash_stored": contract.hash_doc,
            "hash_computed": expected_hash,
            "verified_at": datetime.now()
        }
    }


# ── Endpoint generate/regenerate PDF kontrak ─────────────
@router.post("/{kontrak_id}/generate-pdf", status_code=status.HTTP_200_OK)
def generate_contract_pdf_manual(
    kontrak_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate atau regenerate PDF kontrak secara manual (sinkron)."""
    import io as _io
    contract = db.query(Kontrak).filter(Kontrak.id == kontrak_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Kontrak tidak ditemukan.")

    transaksi = db.query(Transaksi).filter(Transaksi.id == contract.transaksi_id).first()
    if not transaksi:
        raise HTTPException(status_code=404, detail="Transaksi terkait tidak ditemukan.")

    from models import User as UserModel, ItemTransaksi
    kasir = db.query(UserModel).filter(UserModel.id == transaksi.kasir_id).first()
    kasir_name = kasir.username if kasir else "Unknown"
    items = db.query(ItemTransaksi).filter(ItemTransaksi.transaksi_id == transaksi.id).all()

    # Import helper dari transaction router
    try:
        from routers.transaction import _build_contract_pdf
    except ImportError:
        raise HTTPException(status_code=500, detail="Modul PDF builder tidak ditemukan.")

    pdf_bytes  = _build_contract_pdf(transaksi, kasir_name, items, contract.kode)
    hash_doc   = hashlib.sha256(pdf_bytes).hexdigest()

    # Simpan PDF ke disk
    pdf_dir  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "contracts")
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, f"{contract.kode}.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    # Update hash di DB
    contract.hash_doc = hash_doc
    db.commit()

    return {
        "status": "success",
        "message": f"PDF kontrak {contract.kode} berhasil digenerate.",
        "data": {
            "kode": contract.kode,
            "hash_doc": hash_doc,
            "pdf_size_bytes": len(pdf_bytes),
        }
    }


# ── Endpoint generate PDF dari transaksi (tanpa kontrak) ──
@router.post("/generate-for-transaction/{transaksi_id}", status_code=status.HTTP_201_CREATED)
def generate_pdf_for_transaction(
    transaksi_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate kontrak + PDF untuk transaksi yang belum punya kontrak."""
    transaksi = db.query(Transaksi).filter(Transaksi.id == transaksi_id).first()
    if not transaksi:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan.")

    existing = db.query(Kontrak).filter(Kontrak.transaksi_id == transaksi_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Kontrak sudah ada: {existing.kode}. Gunakan endpoint generate-pdf untuk regenerate.")

    from models import User as UserModel, ItemTransaksi
    kasir = db.query(UserModel).filter(UserModel.id == transaksi.kasir_id).first()
    kasir_name = kasir.username if kasir else "Unknown"
    items = db.query(ItemTransaksi).filter(ItemTransaksi.transaksi_id == transaksi_id).all()

    try:
        from routers.transaction import _build_contract_pdf
    except ImportError:
        raise HTTPException(status_code=500, detail="Modul PDF builder tidak ditemukan.")

    # Buat record kontrak dulu (butuh ID untuk kode)
    kontrak = Kontrak(
        transaksi_id=transaksi_id,
        nama_klien=transaksi.nama_klien,
        hash_doc="__pending__",
        kode="__placeholder__"
    )
    db.add(kontrak)
    db.flush()
    kontrak.kode = f"KTR{kontrak.id:03d}"

    pdf_bytes = _build_contract_pdf(transaksi, kasir_name, items, kontrak.kode)
    hash_doc  = hashlib.sha256(pdf_bytes).hexdigest()
    kontrak.hash_doc = hash_doc

    pdf_dir  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "contracts")
    os.makedirs(pdf_dir, exist_ok=True)
    with open(os.path.join(pdf_dir, f"{kontrak.kode}.pdf"), "wb") as f:
        f.write(pdf_bytes)

    db.commit()
    db.refresh(kontrak)

    return {
        "status": "success",
        "message": f"Kontrak {kontrak.kode} berhasil digenerate.",
        "data": KontrakResponse.model_validate(kontrak)
    }
