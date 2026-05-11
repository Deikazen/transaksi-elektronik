"""
routers/midtrans_payment.py
Payment Gateway Midtrans — SecureTransact

Endpoint untuk integrasi pembayaran melalui Midtrans Snap:
  - POST /payment/create-snap-token  → Buat Snap Token untuk payment popup
  - POST /payment/notification       → Webhook notification dari Midtrans
  - GET  /payment/status/{order_id}  → Cek status pembayaran
  - GET  /payment/history            → Riwayat pembayaran
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import hashlib
import json
import logging
import os

from database import get_db
from models import Transaksi, User
from core.deps import get_current_user

router = APIRouter(prefix="/payment", tags=["Payment Gateway"])
logger = logging.getLogger(__name__)

# ── Midtrans Config ──────────────────────────────────────────
# Gunakan Sandbox keys untuk testing
# Ganti ke Production keys saat deploy
MIDTRANS_SERVER_KEY = os.getenv("MIDTRANS_SERVER_KEY", "SB-Mid-server-DEMO_KEY_REPLACE_ME")
MIDTRANS_CLIENT_KEY = os.getenv("MIDTRANS_CLIENT_KEY", "SB-Mid-client-DEMO_KEY_REPLACE_ME")
MIDTRANS_IS_PRODUCTION = os.getenv("MIDTRANS_IS_PRODUCTION", "false").lower() == "true"
MIDTRANS_SNAP_URL = "https://app.midtrans.com/snap/v1/transactions" if MIDTRANS_IS_PRODUCTION else "https://app.sandbox.midtrans.com/snap/v1/transactions"
MIDTRANS_STATUS_URL = "https://api.midtrans.com/v2" if MIDTRANS_IS_PRODUCTION else "https://api.sandbox.midtrans.com/v2"

# ── In-memory payment records (untuk demo, bisa pindah ke DB) ──
_payment_records: list = []
_payment_counter = 0


# ══════════════════════════════════════════════════════════════
#  Schemas
# ══════════════════════════════════════════════════════════════

class PaymentCreateRequest(BaseModel):
    transaksi_id: int
    payment_type: str = "snap"  # snap | direct

class PaymentCreateResponse(BaseModel):
    snap_token: str
    redirect_url: str
    order_id: str
    gross_amount: int
    client_key: str

class PaymentRecord(BaseModel):
    id: int
    order_id: str
    transaksi_id: int
    transaksi_kode: str
    nama_klien: str
    gross_amount: int
    payment_type: str
    payment_status: str  # pending | settlement | capture | deny | cancel | expire | refund
    snap_token: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    midtrans_response: Optional[dict] = None


# ══════════════════════════════════════════════════════════════
#  Helper: Generate Snap Token (Simulasi + Real)
# ══════════════════════════════════════════════════════════════

def _generate_order_id(transaksi_kode: str) -> str:
    """Generate unique order ID for Midtrans."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"ST-{transaksi_kode}-{timestamp}"


async def _create_snap_token_real(order_id: str, gross_amount: int, customer_name: str, items: list) -> dict:
    """
    Buat Snap Token via Midtrans API.
    Requires: pip install httpx
    """
    try:
        import httpx
        import base64
        
        auth_string = base64.b64encode(f"{MIDTRANS_SERVER_KEY}:".encode()).decode()
        
        payload = {
            "transaction_details": {
                "order_id": order_id,
                "gross_amount": gross_amount
            },
            "customer_details": {
                "first_name": customer_name,
            },
            "item_details": items,
            "enabled_payments": [
                "credit_card", "bca_va", "bni_va", "bri_va", "permata_va",
                "echannel", "gopay", "shopeepay", "qris", "dana",
                "indomaret", "alfamart"
            ],
            "credit_card": {
                "secure": True
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                MIDTRANS_SNAP_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Basic {auth_string}"
                },
                timeout=30.0
            )
            
            if response.status_code == 201:
                data = response.json()
                return {
                    "success": True,
                    "snap_token": data.get("token", ""),
                    "redirect_url": data.get("redirect_url", "")
                }
            else:
                logger.error(f"Midtrans API error: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}
                
    except ImportError:
        return {"success": False, "error": "httpx not installed"}
    except Exception as e:
        logger.error(f"Midtrans request failed: {e}")
        return {"success": False, "error": str(e)}


def _create_snap_token_demo(order_id: str, gross_amount: int) -> dict:
    """Simulasi Snap Token untuk mode demo (tanpa koneksi ke Midtrans)."""
    # Generate a demo token
    token_raw = f"{order_id}-{gross_amount}-{datetime.utcnow().isoformat()}"
    demo_token = hashlib.md5(token_raw.encode()).hexdigest()
    
    return {
        "success": True,
        "snap_token": f"demo-{demo_token[:24]}",
        "redirect_url": f"https://app.sandbox.midtrans.com/snap/v3/redirection/{demo_token[:24]}"
    }


# ══════════════════════════════════════════════════════════════
#  POST /payment/create-snap-token
# ══════════════════════════════════════════════════════════════

@router.post("/create-snap-token")
async def create_snap_token(
    payload: PaymentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Buat Snap Token Midtrans untuk membuka payment popup."""
    global _payment_counter
    
    # Get transaction
    transaksi = db.query(Transaksi).filter(Transaksi.id == payload.transaksi_id).first()
    if not transaksi:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan.")
    
    # Generate order ID
    order_id = _generate_order_id(transaksi.kode)
    gross_amount = transaksi.grand_total
    
    # Build item details
    items = []
    for item in transaksi.items:
        items.append({
            "id": str(item.produk_id),
            "name": item.nama_produk[:50],  # Midtrans max 50 chars
            "price": item.harga,
            "quantity": item.qty
        })
    # Add PPN as separate item
    if transaksi.ppn > 0:
        items.append({
            "id": "PPN",
            "name": "PPN 11%",
            "price": transaksi.ppn,
            "quantity": 1
        })
    
    # Try real Midtrans first, fallback to demo
    result = await _create_snap_token_real(order_id, gross_amount, transaksi.nama_klien, items)
    
    is_demo = False
    if not result["success"]:
        # Fallback to demo mode
        result = _create_snap_token_demo(order_id, gross_amount)
        is_demo = True
    
    # Save payment record
    _payment_counter += 1
    record = {
        "id": _payment_counter,
        "order_id": order_id,
        "transaksi_id": transaksi.id,
        "transaksi_kode": transaksi.kode,
        "nama_klien": transaksi.nama_klien,
        "gross_amount": gross_amount,
        "payment_type": "snap",
        "payment_status": "pending",
        "snap_token": result["snap_token"],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": None,
        "is_demo": is_demo
    }
    _payment_records.append(record)
    
    return {
        "status": "success",
        "data": {
            "snap_token": result["snap_token"],
            "redirect_url": result.get("redirect_url", ""),
            "order_id": order_id,
            "gross_amount": gross_amount,
            "client_key": MIDTRANS_CLIENT_KEY,
            "is_demo": is_demo,
            "is_production": MIDTRANS_IS_PRODUCTION
        }
    }


# ══════════════════════════════════════════════════════════════
#  POST /payment/notification — Webhook dari Midtrans
# ══════════════════════════════════════════════════════════════

@router.post("/notification")
async def payment_notification(request: Request, db: Session = Depends(get_db)):
    """
    Webhook endpoint yang dipanggil oleh Midtrans setelah pembayaran.
    Midtrans mengirim notifikasi setiap ada perubahan status pembayaran.
    """
    try:
        body = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    
    order_id = body.get("order_id", "")
    transaction_status = body.get("transaction_status", "")
    fraud_status = body.get("fraud_status", "")
    payment_type = body.get("payment_type", "")
    
    logger.info(f"[Midtrans] Notification: order={order_id}, status={transaction_status}, fraud={fraud_status}")
    
    # Verify signature
    signature_key = body.get("signature_key", "")
    status_code = body.get("status_code", "")
    gross_amount = body.get("gross_amount", "")
    expected_sig = hashlib.sha512(
        f"{order_id}{status_code}{gross_amount}{MIDTRANS_SERVER_KEY}".encode()
    ).hexdigest()
    
    if signature_key and signature_key != expected_sig:
        logger.warning(f"[Midtrans] Invalid signature for order {order_id}")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Determine payment status
    if transaction_status in ["capture", "settlement"]:
        if fraud_status == "accept" or not fraud_status:
            final_status = "settlement"
        else:
            final_status = "deny"
    elif transaction_status == "pending":
        final_status = "pending"
    elif transaction_status in ["deny", "cancel", "expire"]:
        final_status = transaction_status
    else:
        final_status = transaction_status
    
    # Update payment record
    record = next((r for r in _payment_records if r["order_id"] == order_id), None)
    if record:
        record["payment_status"] = final_status
        record["payment_type"] = payment_type
        record["updated_at"] = datetime.utcnow().isoformat()
        record["midtrans_response"] = body
    
    # Update transaction status in DB
    if final_status == "settlement":
        # Extract transaksi_kode from order_id: ST-TRX001-20260509...
        parts = order_id.split("-")
        if len(parts) >= 3:
            trx_kode = parts[1]
            trx = db.query(Transaksi).filter(Transaksi.kode == trx_kode).first()
            if trx:
                trx.status = "lunas"
                trx.metode_pembayaran = payment_type or "midtrans"
                db.commit()
    
    return {"status": "ok"}


# ══════════════════════════════════════════════════════════════
#  GET /payment/status/{order_id} — Cek status pembayaran
# ══════════════════════════════════════════════════════════════

@router.get("/status/{order_id}")
async def get_payment_status(
    order_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cek status pembayaran berdasarkan order_id."""
    record = next((r for r in _payment_records if r["order_id"] == order_id), None)
    if not record:
        raise HTTPException(status_code=404, detail="Payment record tidak ditemukan.")
    
    # Try to check real status from Midtrans
    if not record.get("is_demo", False):
        try:
            import httpx
            import base64
            
            auth_string = base64.b64encode(f"{MIDTRANS_SERVER_KEY}:".encode()).decode()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{MIDTRANS_STATUS_URL}/{order_id}/status",
                    headers={"Authorization": f"Basic {auth_string}"},
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    record["payment_status"] = data.get("transaction_status", record["payment_status"])
                    record["midtrans_response"] = data
        except:
            pass
    
    return {"status": "success", "data": record}


# ══════════════════════════════════════════════════════════════
#  GET /payment/history — Riwayat pembayaran
# ══════════════════════════════════════════════════════════════

@router.get("/history")
def get_payment_history(current_user: User = Depends(get_current_user)):
    """Ambil semua riwayat pembayaran."""
    return {
        "status": "success",
        "data": list(reversed(_payment_records))
    }


# ══════════════════════════════════════════════════════════════
#  POST /payment/simulate-success — Simulasi pembayaran berhasil (demo)
# ══════════════════════════════════════════════════════════════

class SimulatePaymentRequest(BaseModel):
    order_id: str

@router.post("/simulate-success")
def simulate_payment_success(
    payload: SimulatePaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Simulasi callback pembayaran berhasil (untuk testing/demo)."""
    record = next((r for r in _payment_records if r["order_id"] == payload.order_id), None)
    if not record:
        raise HTTPException(status_code=404, detail="Payment record tidak ditemukan.")
    
    record["payment_status"] = "settlement"
    record["payment_type"] = "demo_simulation"
    record["updated_at"] = datetime.utcnow().isoformat()
    
    # Update transaksi status
    trx = db.query(Transaksi).filter(Transaksi.id == record["transaksi_id"]).first()
    if trx:
        trx.status = "lunas"
        trx.metode_pembayaran = "midtrans"
        db.commit()
    
    return {
        "status": "success",
        "message": f"Payment {payload.order_id} berhasil disimulasikan.",
        "data": record
    }


# ══════════════════════════════════════════════════════════════
#  GET /payment/config — Get client config for frontend
# ══════════════════════════════════════════════════════════════

@router.get("/config")
def get_payment_config(current_user: User = Depends(get_current_user)):
    """Return Midtrans client configuration for frontend."""
    return {
        "status": "success",
        "data": {
            "client_key": MIDTRANS_CLIENT_KEY,
            "is_production": MIDTRANS_IS_PRODUCTION,
            "snap_url": "https://app.midtrans.com/snap/snap.js" if MIDTRANS_IS_PRODUCTION else "https://app.sandbox.midtrans.com/snap/snap.js",
            "enabled_payments": [
                "credit_card", "bca_va", "bni_va", "bri_va", "permata_va",
                "gopay", "shopeepay", "qris", "dana", "indomaret", "alfamart"
            ]
        }
    }
