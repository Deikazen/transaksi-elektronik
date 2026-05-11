"""
routers/laporan.py
Laporan & Export — SecureTransact POS

Endpoint:
  - GET /laporan/ringkasan     → Ringkasan penjualan (hari/minggu/bulan)
  - GET /laporan/export/csv    → Export transaksi ke CSV
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Optional
import csv, io

from database import get_db
from models import Transaksi, ItemTransaksi, Produk, User
from core.deps import get_current_user

router = APIRouter(prefix="/laporan", tags=["Laporan"])


@router.get("/ringkasan")
def get_ringkasan(
    periode: str = Query("bulan", description="hari|minggu|bulan|semua"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ringkasan penjualan berdasarkan periode."""
    now = datetime.utcnow()
    
    if periode == "hari":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periode == "minggu":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periode == "bulan":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start = datetime(2000, 1, 1)

    txs = db.query(Transaksi).filter(Transaksi.created_at >= start).all()
    
    total_tx = len(txs)
    total_pendapatan = sum(t.grand_total for t in txs)
    total_diskon = sum(t.diskon_nominal or 0 for t in txs)
    total_ppn = sum(t.ppn for t in txs)
    rata_rata = round(total_pendapatan / total_tx) if total_tx > 0 else 0
    
    # Metode pembayaran breakdown
    metode_count = {}
    for t in txs:
        m = t.metode_pembayaran or "tunai"
        metode_count[m] = metode_count.get(m, 0) + 1
    
    # Produk terlaris
    items_q = db.query(
        ItemTransaksi.nama_produk,
        func.sum(ItemTransaksi.qty).label("total_qty"),
        func.sum(ItemTransaksi.harga * ItemTransaksi.qty).label("total_revenue")
    ).join(Transaksi).filter(
        Transaksi.created_at >= start
    ).group_by(ItemTransaksi.nama_produk).order_by(desc("total_qty")).limit(10).all()
    
    produk_terlaris = [
        {"nama": r[0], "qty": int(r[1]), "revenue": int(r[2])} 
        for r in items_q
    ]
    
    # Penjualan per hari (untuk chart)
    chart_data = []
    if periode == "bulan":
        for day in range(1, now.day + 1):
            d_start = start.replace(day=day)
            d_end = d_start + timedelta(days=1)
            day_txs = [t for t in txs if d_start <= t.created_at < d_end]
            chart_data.append({
                "label": f"{day:02d}",
                "transaksi": len(day_txs),
                "pendapatan": sum(t.grand_total for t in day_txs)
            })
    elif periode == "minggu":
        hari = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
        for i in range(7):
            d_start = start + timedelta(days=i)
            d_end = d_start + timedelta(days=1)
            day_txs = [t for t in txs if d_start <= t.created_at < d_end]
            chart_data.append({
                "label": hari[i],
                "transaksi": len(day_txs),
                "pendapatan": sum(t.grand_total for t in day_txs)
            })
    else:
        for h in range(24):
            h_start = start.replace(hour=h, minute=0, second=0, microsecond=0) if periode == "hari" else now - timedelta(hours=23-h)
            h_end = h_start + timedelta(hours=1)
            h_txs = [t for t in txs if h_start <= t.created_at < h_end]
            chart_data.append({
                "label": f"{h:02d}:00",
                "transaksi": len(h_txs),
                "pendapatan": sum(t.grand_total for t in h_txs)
            })
    
    return {
        "status": "success",
        "data": {
            "periode": periode,
            "total_transaksi": total_tx,
            "total_pendapatan": total_pendapatan,
            "total_diskon": total_diskon,
            "total_ppn": total_ppn,
            "rata_rata_per_tx": rata_rata,
            "metode_pembayaran": metode_count,
            "produk_terlaris": produk_terlaris,
            "chart": chart_data
        }
    }


@router.get("/export/csv")
def export_csv(
    periode: str = Query("bulan"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export data transaksi ke CSV."""
    now = datetime.utcnow()
    
    if periode == "hari":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periode == "minggu":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periode == "bulan":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start = datetime(2000, 1, 1)
    
    txs = db.query(Transaksi).filter(
        Transaksi.created_at >= start
    ).order_by(Transaksi.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Kode", "Tanggal", "Klien", "Subtotal", "Diskon(%)", "Diskon(Rp)",
        "PPN", "Grand Total", "Metode", "Status", "Kasir ID"
    ])
    
    for t in txs:
        writer.writerow([
            t.kode,
            t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else "",
            t.nama_klien,
            t.total,
            t.diskon_persen or 0,
            t.diskon_nominal or 0,
            t.ppn,
            t.grand_total,
            t.metode_pembayaran,
            t.status,
            t.kasir_id
        ])
    
    output.seek(0)
    filename = f"laporan_{periode}_{now.strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
