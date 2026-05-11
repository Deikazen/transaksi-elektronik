
"""
routers/transaction.py
Endpoint transaksi POS — SecureTransact (IFB-352, Grup C10 ITENAS)

Changelog vs versi sebelumnya:
  - CHANGED: Semua operasi DB dibungkus try/except + db.rollback()
  - NEW:     PPN 11% dan grand_total dihitung & dikembalikan di response
  - NEW:     BackgroundTasks untuk generate PDF struk via ReportLab
  - CHANGED: Kode transaksi pakai f"TRX{transaksi.id:03d}" setelah flush()
  - NEW:     GET /transaction/{id}/receipt endpoint
  - CHANGED: TransaksiResponse schema ditambah ppn & grand_total
"""

# ← CHANGED: tambah BackgroundTasks
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import hashlib  # ← NEW: untuk SHA-256 hash PDF
import io       # ← NEW: untuk BytesIO buffer PDF
import logging  # ← NEW: logging untuk background task

from backend.database import get_db, SessionLocal
from backend.models import Transaksi, ItemTransaksi, Produk, User, Kontrak, IOLog
from backend.core.deps import get_current_user, require_kasir
import os

router = APIRouter(prefix="/transaction", tags=["Transaction"])
logger = logging.getLogger(__name__)  # ← NEW

# ── Schema ────────────────────────────────────────────────


class ItemTransaksiCreate(BaseModel):
    produk_id: int
    qty: int


class TransaksiCreate(BaseModel):
    nama_klien: str
    metode_pembayaran: str = "tunai"
    jumlah_bayar: int = 0
    diskon_persen: int = 0       # diskon 0-100%
    items: List[ItemTransaksiCreate]


class ItemTransaksiResponse(BaseModel):
    id: int
    produk_id: int
    nama_produk: str
    harga: int
    qty: int

    class Config:
        from_attributes = True


class TransaksiResponse(BaseModel):
    id: int
    kode: str
    nama_klien: str
    total: int              # subtotal sebelum pajak
    diskon_persen: int = 0
    diskon_nominal: int = 0
    ppn: int
    grand_total: int
    status: str
    metode_pembayaran: str
    jumlah_bayar: int
    kembalian: int
    kasir_id: Optional[int]
    created_at: datetime
    items: List[ItemTransaksiResponse]

    class Config:
        from_attributes = True

# ── Receipt detail response (untuk endpoint /receipt) ─────  # ← NEW


class KontrakInfo(BaseModel):
    id: int
    kode: str
    hash_doc: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReceiptResponse(BaseModel):  # ← NEW
    transaksi: TransaksiResponse
    kontrak: Optional[KontrakInfo] = None
    kasir_username: Optional[str] = None

# ══════════════════════════════════════════════════════════
#  Background task: Generate PDF struk & simpan Kontrak
# ══════════════════════════════════════════════════════════


def _build_contract_pdf(transaksi, kasir_name: str, items, kontrak_kode: str = None) -> bytes:
    """
    Helper: build professional contract PDF bytes using ReportLab.
    Returns raw PDF bytes.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    margin_l = 20 * mm
    margin_r = W - 20 * mm
    y = H - 15 * mm

    # ── Background header bar ────────────────────────────────
    c.setFillColorRGB(0.07, 0.09, 0.18)   # dark navy
    c.rect(0, H - 42 * mm, W, 42 * mm, fill=1, stroke=0)

    # Company name
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin_l, H - 18 * mm, "SecureTransact")
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.6, 0.7, 0.9)
    c.drawString(margin_l, H - 25 * mm,
                 "Sistem Transaksi Elektronik Terverifikasi  |  IFB-352 Grup C10 ITENAS")

    # KONTRAK DIGITAL label (top-right)
    c.setFillColorRGB(0.38, 0.68, 1.0)
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(margin_r, H - 18 * mm, "KONTRAK DIGITAL")
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.6, 0.7, 0.9)
    kode_label = kontrak_kode if kontrak_kode else "(dalam proses)"
    c.drawRightString(margin_r, H - 25 * mm, f"No. {kode_label}")

    y = H - 50 * mm

    # ── Info block ──────────────────────────────────────────
    c.setFillColorRGB(0.13, 0.15, 0.25)
    c.roundRect(margin_l, y - 28 * mm, W - 40 * mm,
                28 * mm, 3 * mm, fill=1, stroke=0)

    info_x1 = margin_l + 5 * mm
    info_x2 = W / 2 + 5 * mm
    info_y = y - 7 * mm

    c.setFillColorRGB(0.5, 0.6, 0.8)
    c.setFont("Helvetica", 8)
    c.drawString(info_x1, info_y, "NOMOR TRANSAKSI")
    c.drawString(info_x2, info_y, "TANGGAL")
    info_y -= 5 * mm
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(info_x1, info_y, transaksi.kode)
    ts = transaksi.created_at.strftime(
        "%d %B %Y, %H:%M WIB") if transaksi.created_at else "-"
    c.drawString(info_x2, info_y, ts)

    info_y -= 8 * mm
    c.setFillColorRGB(0.5, 0.6, 0.8)
    c.setFont("Helvetica", 8)
    c.drawString(info_x1, info_y, "PIHAK KEDUA (PEMBELI)")
    c.drawString(info_x2, info_y, "KASIR / PETUGAS")
    info_y -= 5 * mm
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(info_x1, info_y, transaksi.nama_klien)
    c.drawString(info_x2, info_y, kasir_name)

    y -= 36 * mm

    # ── Section: Rincian Pembelian ──────────────────────────
    c.setFillColorRGB(0.07, 0.09, 0.18)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_l, y, "RINCIAN PEMBELIAN")
    c.setStrokeColorRGB(0.38, 0.68, 1.0)
    c.setLineWidth(1.5)
    c.line(margin_l, y - 2 * mm, margin_r, y - 2 * mm)
    y -= 8 * mm

    # Table header
    col_produk = margin_l
    col_qty = margin_l + 90 * mm
    col_harga = margin_l + 110 * mm
    col_subtotal = margin_r - 25 * mm

    c.setFillColorRGB(0.07, 0.09, 0.18)
    c.rect(col_produk, y - 5 * mm, W - 40 * mm, 7 * mm, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_produk + 2 * mm, y - 2 * mm, "Nama Produk")
    c.drawString(col_qty,             y - 2 * mm, "Qty")
    c.drawString(col_harga,           y - 2 * mm, "Harga Satuan")
    c.drawString(col_subtotal,        y - 2 * mm, "Subtotal")
    y -= 8 * mm

    # Table rows
    subtotal_all = 0
    row_bg = [0.97, 0.97, 1.0]
    for i, item in enumerate(items):
        item_sub = item.harga * item.qty
        subtotal_all += item_sub
        if i % 2 == 0:
            c.setFillColorRGB(*row_bg)
            c.rect(margin_l, y - 4 * mm, W - 40 * mm, 6 * mm, fill=1, stroke=0)
        c.setFillColorRGB(0.1, 0.1, 0.2)
        c.setFont("Helvetica", 9)
        c.drawString(col_produk + 2 * mm, y - 0.5 *
                     mm, str(item.nama_produk)[:38])
        c.drawString(col_qty,             y - 0.5 * mm, str(item.qty))
        c.drawString(col_harga,           y - 0.5 * mm,
                     f"Rp {item.harga:,}".replace(",", "."))
        c.drawString(col_subtotal,        y - 0.5 * mm,
                     f"Rp {item_sub:,}".replace(",", "."))
        y -= 6 * mm

    y -= 3 * mm
    c.setStrokeColorRGB(0.8, 0.85, 0.95)
    c.setLineWidth(0.5)
    c.line(margin_l, y, margin_r, y)
    y -= 6 * mm

    # ── Totals ──────────────────────────────────────────────
    diskon_nominal = transaksi.diskon_nominal if hasattr(
        transaksi, 'diskon_nominal') and transaksi.diskon_nominal else 0
    diskon_persen = transaksi.diskon_persen if hasattr(
        transaksi, 'diskon_persen') and transaksi.diskon_persen else 0
    setelah_diskon = subtotal_all - diskon_nominal
    ppn = transaksi.ppn if transaksi.ppn else round(setelah_diskon * 0.11)
    grand_total = transaksi.grand_total if transaksi.grand_total else (
        setelah_diskon + ppn)

    def draw_sum_row(label, amount, bold=False, highlight=False, color_green=False):
        nonlocal y
        if highlight:
            c.setFillColorRGB(0.07, 0.09, 0.18)
            c.rect(col_harga - 2 * mm, y - 4 * mm, margin_r -
                   col_harga + 2 * mm, 7 * mm, fill=1, stroke=0)
            c.setFillColorRGB(0.38, 0.68, 1.0)
        elif color_green:
            c.setFillColorRGB(0.06, 0.72, 0.5)
        else:
            c.setFillColorRGB(0.2, 0.2, 0.35)
        fnt = "Helvetica-Bold" if (bold or highlight) else "Helvetica"
        sz = 10 if highlight else 9
        c.setFont(fnt, sz)
        c.drawRightString(col_subtotal - 5 * mm, y - 0.5 * mm, label)
        prefix = "-" if color_green else ""
        c.drawString(col_subtotal, y - 0.5 * mm,
                     f"{prefix}Rp {abs(amount):,}".replace(",", "."))
        y -= 7 * mm

    draw_sum_row("Subtotal",  subtotal_all)
    if diskon_nominal > 0:
        draw_sum_row(f"Diskon ({diskon_persen}%)",
                     diskon_nominal, color_green=True)
    draw_sum_row("PPN 11%",   ppn)
    draw_sum_row("TOTAL PEMBAYARAN", grand_total, bold=True, highlight=True)

    y -= 3 * mm
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.3, 0.3, 0.4)
    c.drawRightString(col_subtotal - 5 * mm, y,
                      f"Metode Pembayaran: {transaksi.metode_pembayaran.upper()}")
    y -= 5 * mm
    if transaksi.metode_pembayaran == "tunai":
        c.drawRightString(col_subtotal - 5 * mm, y, "Jumlah Bayar:")
        c.drawString(col_subtotal, y,
                     f"Rp {transaksi.jumlah_bayar:,}".replace(",", "."))
        y -= 5 * mm
        c.drawRightString(col_subtotal - 5 * mm, y, "Kembalian:")
        c.drawString(col_subtotal, y,
                     f"Rp {transaksi.kembalian:,}".replace(",", "."))
        y -= 5 * mm
    y -= 5 * mm

    # ── Section: Verifikasi Digital ─────────────────────────
    c.setFillColorRGB(0.07, 0.09, 0.18)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_l, y, "VERIFIKASI KRIPTOGRAFI")
    c.setStrokeColorRGB(0.38, 0.68, 1.0)
    c.setLineWidth(1.5)
    c.line(margin_l, y - 2 * mm, margin_r, y - 2 * mm)
    y -= 10 * mm

    c.setFillColorRGB(0.93, 0.95, 1.0)
    c.roundRect(margin_l, y - 18 * mm, W - 40 * mm,
                18 * mm, 3 * mm, fill=1, stroke=0)
    c.setFillColorRGB(0.4, 0.5, 0.7)
    c.setFont("Helvetica", 7.5)
    c.drawString(margin_l + 4 * mm, y - 5 * mm, "Algoritma  : SHA-256")
    c.drawString(margin_l + 4 * mm, y - 10 * mm,
                 "Hash SHA-256 dokumen ini akan dihitung dan disimpan di database setelah PDF digenerate.")
    c.drawString(margin_l + 4 * mm, y - 15 * mm,
                 "Hash dapat diverifikasi kapan saja melalui dashboard SecureTransact untuk membuktikan keaslian dokumen.")
    y -= 24 * mm

    # ── Section: Syarat & Ketentuan ─────────────────────────
    c.setFillColorRGB(0.07, 0.09, 0.18)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_l, y, "SYARAT & KETENTUAN")
    c.setStrokeColorRGB(0.38, 0.68, 1.0)
    c.setLineWidth(1.5)
    c.line(margin_l, y - 2 * mm, margin_r, y - 2 * mm)
    y -= 9 * mm

    terms = [
        "1. Kontrak ini mengikat kedua belah pihak secara hukum sesuai peraturan perundang-undangan yang berlaku di Indonesia.",
        "2. Tanda tangan digital dilindungi dengan teknologi hash kriptografi SHA-256 yang tidak dapat dipalsukan.",
        "3. Dokumen ini tidak dapat diubah setelah ditandatangani; setiap perubahan akan menghasilkan hash yang berbeda.",
        "4. Sengketa yang timbul diselesaikan secara musyawarah, atau melalui jalur hukum sesuai yurisdiksi Indonesia.",
    ]
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.3, 0.3, 0.4)
    for t in terms:
        c.drawString(margin_l, y, t)
        y -= 5.5 * mm

    y -= 5 * mm

    # ── Section: Tanda Tangan ───────────────────────────────
    c.setStrokeColorRGB(0.75, 0.8, 0.9)
    c.setLineWidth(0.5)
    sig_w = (W - 50 * mm) / 2
    sig_l = margin_l
    sig_r = margin_r - sig_w

    c.setFillColorRGB(0.95, 0.96, 1.0)
    c.roundRect(sig_l, y - 22 * mm, sig_w, 22 * mm, 2 * mm, fill=1, stroke=0)
    c.roundRect(sig_r, y - 22 * mm, sig_w, 22 * mm, 2 * mm, fill=1, stroke=0)

    c.setFillColorRGB(0.4, 0.5, 0.7)
    c.setFont("Helvetica", 8)
    c.drawCentredString(sig_l + sig_w / 2, y - 5 * mm,  "Pihak Pertama")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColorRGB(0.1, 0.1, 0.25)
    c.drawCentredString(sig_l + sig_w / 2, y - 10 * mm, "PT SecureTransact")
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.4, 0.5, 0.7)
    c.drawCentredString(sig_l + sig_w / 2, y - 19 * mm, "(Tanda Tangan & Cap)")

    c.setFillColorRGB(0.4, 0.5, 0.7)
    c.setFont("Helvetica", 8)
    c.drawCentredString(sig_r + sig_w / 2, y - 5 * mm,  "Pihak Kedua")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColorRGB(0.1, 0.1, 0.25)
    c.drawCentredString(sig_r + sig_w / 2, y - 10 * mm, transaksi.nama_klien)
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.4, 0.5, 0.7)
    c.drawCentredString(sig_r + sig_w / 2, y - 19 * mm, "(Tanda Tangan)")

    # ── Footer bar ──────────────────────────────────────────
    c.setFillColorRGB(0.07, 0.09, 0.18)
    c.rect(0, 0, W, 14 * mm, fill=1, stroke=0)
    c.setFillColorRGB(0.5, 0.6, 0.8)
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(
        W / 2, 9 * mm, "Dokumen ini digenerate secara otomatis oleh sistem SecureTransact dan sah tanpa tanda tangan basah.")
    c.drawCentredString(
        W / 2, 5 * mm, f"SecureTransact  |  IFB-352 Grup C10 ITENAS  |  {transaksi.kode}")

    c.save()
    return buf.getvalue()


def generate_pdf_receipt(transaksi_id: int):
    """
    Background task yang:
    1. Generate PDF kontrak digital profesional menggunakan ReportLab
    2. Hitung SHA-256 hash dari PDF bytes
    3. Simpan file PDF ke disk & hash ke tabel Kontrak
    """
    db = SessionLocal()
    try:
        transaksi = db.query(Transaksi).filter(
            Transaksi.id == transaksi_id).first()
        if not transaksi:
            logger.error(f"[PDF] Transaksi ID {transaksi_id} tidak ditemukan.")
            return

        kasir = db.query(User).filter(User.id == transaksi.kasir_id).first()
        kasir_name = kasir.username if kasir else "Unknown"
        items = db.query(ItemTransaksi).filter(
            ItemTransaksi.transaksi_id == transaksi_id).all()

        # LOG: Start PDF generation (PROCESS)
        log_pdf_start = IOLog(
            action="PROCESS", source="background", target="api",
            description=f"BackgroundTask: Memulai pembuatan PDF struk untuk {transaksi.kode}",
            transaction_kode=transaksi.kode, status="success", data_size="0 B"
        )
        db.add(log_pdf_start)
        db.flush()

        # Cek kontrak sudah ada
        existing = db.query(Kontrak).filter(
            Kontrak.transaksi_id == transaksi_id).first()
        if existing:
            logger.info(
                f"[PDF] Kontrak sudah ada untuk TRX ID {transaksi_id}, skip.")
            return

        # Buat placeholder dulu supaya dapat kode
        kontrak = Kontrak(
            transaksi_id=transaksi_id,
            nama_klien=transaksi.nama_klien,
            hash_doc="__pending__",
            kode="__placeholder__"
        )
        db.add(kontrak)
        db.flush()
        kontrak.kode = f"KTR{kontrak.id:03d}"

        # Generate PDF dengan kode kontrak sudah diketahui
        pdf_bytes = _build_contract_pdf(
            transaksi, kasir_name, items, kontrak.kode)
        hash_doc = hashlib.sha256(pdf_bytes).hexdigest()
        kontrak.hash_doc = hash_doc

        # Simpan file PDF ke disk
        pdf_dir = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "..", "data", "contracts")
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, f"{kontrak.kode}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

        # LOG: PDF Success (OUTPUT)
        log_pdf_ok = IOLog(
            action="OUTPUT", source="background", target="database",
            description=f"Kontrak {kontrak.kode} berhasil dibuat & diarsip. Hash: {hash_doc[:16]}...",
            transaction_kode=transaksi.kode, status="success", data_size=f"{len(pdf_bytes)//1024} KB"
        )
        db.add(log_pdf_ok)

        db.commit()
        logger.info(
            f"[PDF] Kontrak {kontrak.kode} berhasil untuk {transaksi.kode} (hash: {hash_doc[:16]}...)")

    except Exception as e:
        db.rollback()
        logger.error(
            f"[PDF] Gagal generate PDF untuk TRX ID {transaksi_id}: {e}")
    finally:
        db.close()

# ── Endpoints ─────────────────────────────────────────────


@router.get("/")
def get_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transactions = db.query(Transaksi).order_by(
        Transaksi.created_at.desc()).all()
    return {
        "status": "success",
        "data": [TransaksiResponse.model_validate(t) for t in transactions]
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransaksiCreate,
    # ← NEW: BackgroundTasks parameter
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_kasir)
):
    # LOG: Input received (INPUT)
    log_input = IOLog(
        action="INPUT", source="frontend", target="api",
        description=f"POST /transaction/ — Klien: '{payload.nama_klien}', Items: {len(payload.items)}",
        status="success", data_size=f"{len(payload.nama_klien)*2 + len(payload.items)*20} B"
    )
    db.add(log_input)
    db.flush()

    try:
        # LOG: Validation (PROCESS)
        log_val = IOLog(
            action="PROCESS", source="api", target="database",
            description=f"Validasi stok & harga untuk {len(payload.items)} produk",
            status="success"
        )
        db.add(log_val)

        total_harga = 0
        items_to_create = []

        # Verifikasi stok dan hitung total
        for item in payload.items:
            produk = db.query(Produk).filter(
                Produk.id == item.produk_id).first()
            if not produk:
                raise HTTPException(
                    status_code=404,
                    detail=f"Produk ID {item.produk_id} tidak ditemukan."
                )
            if produk.stok < item.qty:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stok produk '{produk.nama_produk}' tidak mencukupi (sisa: {produk.stok})."
                )

            subtotal = produk.harga * item.qty
            total_harga += subtotal

            # Kurangi stok produk (belum commit, bisa rollback)
            produk.stok -= item.qty

            # Siapkan item transaksi
            items_to_create.append(
                ItemTransaksi(
                    produk_id=produk.id,
                    nama_produk=produk.nama_produk,
                    harga=produk.harga,
                    qty=item.qty
                )
            )

        # ── Calculate Diskon ──────────────────────────────
        diskon_persen = max(0, min(100, payload.diskon_persen))
        diskon_nominal = round(total_harga * diskon_persen / 100)
        setelah_diskon = total_harga - diskon_nominal

        # ── Calculate PPN (11%) ──────────────────────────
        ppn = round(setelah_diskon * 0.11)
        grand_total = setelah_diskon + ppn

        kembalian = 0
        if payload.metode_pembayaran == "tunai":
            if payload.jumlah_bayar < grand_total:
                raise HTTPException(
                    status_code=400, detail="Jumlah uang tunai kurang dari total pembayaran.")
            kembalian = payload.jumlah_bayar - grand_total
        else:
            payload.jumlah_bayar = grand_total
            kembalian = 0

        # Simpan transaksi
        transaksi = Transaksi(
            kode="__pending__",
            nama_klien=payload.nama_klien,
            total=total_harga,
            diskon_persen=diskon_persen,
            diskon_nominal=diskon_nominal,
            ppn=ppn,
            grand_total=grand_total,
            status="lunas",
            metode_pembayaran=payload.metode_pembayaran,
            jumlah_bayar=payload.jumlah_bayar,
            kembalian=kembalian,
            kasir_id=current_user.id
        )
        db.add(transaksi)
        db.flush()  # ← CHANGED: flush dulu supaya transaksi.id terisi

        # ── CHANGED: Generate kode transaksi setelah flush (fix race condition) ──
        transaksi.kode = f"TRX{transaksi.id:03d}"

        # Link log input ke kode transaksi yang baru didapat
        log_input.transaction_kode = transaksi.kode
        log_val.transaction_kode = transaksi.kode

        # LOG: Commit DB (PROCESS)
        log_db = IOLog(
            action="PROCESS", source="api", target="database",
            description=f"INSERT {transaksi.kode} + {len(items_to_create)} items — Atomic commit",
            transaction_kode=transaksi.kode, status="success"
        )
        db.add(log_db)

        # Tambahkan items
        for item in items_to_create:
            item.transaksi_id = transaksi.id
            db.add(item)

        db.commit()   # ← Semua perubahan (stok, transaksi, items) di-commit atomik
        db.refresh(transaksi)

    except HTTPException:
        db.rollback()  # ← CHANGED: rollback jika ada HTTPException (stok kurang, dll)
        raise          # re-raise agar FastAPI tetap kembalikan error response yang benar
    except Exception as e:
        db.rollback()  # ← CHANGED: rollback untuk error tak terduga
        logger.error(f"[TRX] Gagal buat transaksi: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan server saat memproses transaksi: {str(e)}"
        )

    # ── NEW: Trigger background task untuk generate PDF + Kontrak ──
    background_tasks.add_task(generate_pdf_receipt, transaksi.id)

    # LOG: Response sent (OUTPUT)
    log_out = IOLog(
        action="OUTPUT", source="api", target="frontend",
        description=f"201 Created — Transaksi {transaksi.kode} berhasil diproses",
        transaction_kode=transaksi.kode, status="success", data_size="512 B"
    )
    db.add(log_out)
    db.commit()

    return {
        "status": "success",
        "message": f"Transaksi '{transaksi.kode}' berhasil.",
        "data": TransaksiResponse.model_validate(transaksi)
    }


@router.get("/{transaksi_id}")
def get_transaction(
    transaksi_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transaksi = db.query(Transaksi).filter(
        Transaksi.id == transaksi_id).first()
    if not transaksi:
        raise HTTPException(
            status_code=404, detail="Transaksi tidak ditemukan.")

    return {
        "status": "success",
        "data": TransaksiResponse.model_validate(transaksi)
    }

# ══════════════════════════════════════════════════════════
#  NEW ENDPOINT: GET /transaction/{id}/receipt
#  Return detail transaksi + info kontrak (hash, kode)
# ══════════════════════════════════════════════════════════


@router.get("/{transaksi_id}/receipt")  # ← NEW (entire endpoint)
def get_receipt(
    transaksi_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ambil detail struk transaksi beserta info kontrak digital."""
    transaksi = db.query(Transaksi).filter(
        Transaksi.id == transaksi_id).first()
    if not transaksi:
        raise HTTPException(
            status_code=404, detail="Transaksi tidak ditemukan.")

    # Ambil nama kasir
    kasir = db.query(User).filter(User.id == transaksi.kasir_id).first()

    # Ambil kontrak terkait (jika sudah di-generate oleh background task)
    kontrak = db.query(Kontrak).filter(
        Kontrak.transaksi_id == transaksi_id).first()

    return {
        "status": "success",
        "data": ReceiptResponse(
            transaksi=TransaksiResponse.model_validate(transaksi),
            kontrak=KontrakInfo.model_validate(kontrak) if kontrak else None,
            kasir_username=kasir.username if kasir else None
        )
    }

