"""
routers/kontrak_b2b.py
Endpoint untuk Kontrak Elektronik Antar Perusahaan (B2B)
Mendukung: pembuatan kontrak, generate PDF profesional, verifikasi hash SHA-256
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import hashlib
import io
import os
import logging

from backend.database import get_db
from backend.models import KontrakB2B, User
from backend.core.deps import get_current_user

router = APIRouter(prefix="/kontrak-b2b", tags=["Kontrak B2B"])
logger = logging.getLogger(__name__)

PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "contracts_b2b")


# ── Pydantic Schemas ─────────────────────────────────────────

class PihakInfo(BaseModel):
    nama: str
    alamat: Optional[str] = None
    npwp: Optional[str] = None
    pic: Optional[str] = None


class KontrakB2BCreate(BaseModel):
    pihak_pertama: PihakInfo
    pihak_kedua: PihakInfo
    judul_kontrak: str
    deskripsi: Optional[str] = None
    nilai_kontrak: int = 0
    tanggal_mulai: Optional[datetime] = None
    tanggal_selesai: Optional[datetime] = None


class KontrakB2BUpdate(BaseModel):
    status: Optional[str] = None
    deskripsi: Optional[str] = None
    nilai_kontrak: Optional[int] = None
    tanggal_mulai: Optional[datetime] = None
    tanggal_selesai: Optional[datetime] = None


class KontrakB2BResponse(BaseModel):
    id: int
    kode: str
    pihak_pertama_nama: str
    pihak_pertama_alamat: Optional[str]
    pihak_pertama_npwp: Optional[str]
    pihak_pertama_pic: Optional[str]
    pihak_kedua_nama: str
    pihak_kedua_alamat: Optional[str]
    pihak_kedua_npwp: Optional[str]
    pihak_kedua_pic: Optional[str]
    judul_kontrak: str
    deskripsi: Optional[str]
    nilai_kontrak: int
    tanggal_mulai: Optional[datetime]
    tanggal_selesai: Optional[datetime]
    status: str
    hash_doc: Optional[str]
    created_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Helpers ──────────────────────────────────────────────────

_HARI_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
_BULAN_ID = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

_SATUAN = [
    "", "satu", "dua", "tiga", "empat", "lima",
    "enam", "tujuh", "delapan", "sembilan", "sepuluh",
    "sebelas", "dua belas", "tiga belas", "empat belas", "lima belas",
    "enam belas", "tujuh belas", "delapan belas", "sembilan belas",
]


def _terbilang(n: int) -> str:
    """Konversi angka ke kata dalam Bahasa Indonesia."""
    if n == 0:
        return "nol"
    if n < 0:
        return "minus " + _terbilang(-n)
    if n < 20:
        return _SATUAN[n]
    if n < 100:
        return _SATUAN[n // 10 * 10 // 10 + 9] if False else (
            ("" if n // 10 == 1 else _SATUAN[n // 10]) +
            " puluh" +
            ("" if n % 10 == 0 else " " + _SATUAN[n % 10])
        )
    if n < 1000:
        prefix = "seratus" if n // 100 == 1 else _SATUAN[n // 100] + " ratus"
        rem = n % 100
        return prefix + ("" if rem == 0 else " " + _terbilang(rem))
    if n < 1_000_000:
        prefix = "seribu" if n // 1000 == 1 else _terbilang(n // 1000) + " ribu"
        rem = n % 1000
        return prefix + ("" if rem == 0 else " " + _terbilang(rem))
    if n < 1_000_000_000:
        prefix = _terbilang(n // 1_000_000) + " juta"
        rem = n % 1_000_000
        return prefix + ("" if rem == 0 else " " + _terbilang(rem))
    if n < 1_000_000_000_000:
        prefix = _terbilang(n // 1_000_000_000) + " miliar"
        rem = n % 1_000_000_000
        return prefix + ("" if rem == 0 else " " + _terbilang(rem))
    return str(n)


def _format_tanggal_id(dt: datetime) -> str:
    if not dt:
        return "—"
    return f"{dt.day} {_BULAN_ID[dt.month]} {dt.year}"


def _hari_id(dt: datetime) -> str:
    if not dt:
        return "—"
    return _HARI_ID[dt.weekday()]


def _parse_pic(pic_str: str):
    """Pisahkan 'Nama, Jabatan' → (nama, jabatan)."""
    if not pic_str:
        return ("—", "—")
    parts = pic_str.split(",", 1)
    nama = parts[0].strip()
    jabatan = parts[1].strip() if len(parts) > 1 else "—"
    return nama, jabatan


# ── PDF Builder ──────────────────────────────────────────────

def _build_b2b_pdf(kontrak: KontrakB2B, pembuat_username: str) -> bytes:
    """Generate formal Surat Perjanjian Kerja Sama (PKS) PDF using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    # ── Setup ─────────────────────────────────────────────────
    buf = io.BytesIO()
    W, H = A4
    ML = 25 * mm          # margin kiri
    MR = W - 25 * mm      # margin kanan
    MB = 20 * mm          # margin bawah
    TW = MR - ML          # lebar teks tersedia

    c = canvas.Canvas(buf, pagesize=A4)

    # ── State halaman ─────────────────────────────────────────
    page_num = [1]
    y = [H - 20 * mm]     # posisi Y saat ini (list agar bisa dimodifikasi di closure)

    # ── Data kontrak ─────────────────────────────────────────
    tgl_buat    = kontrak.created_at or datetime.now()
    hari_buat   = _hari_id(tgl_buat)
    tanggal_buat = _format_tanggal_id(tgl_buat)

    p1_nama   = kontrak.pihak_pertama_nama or "—"
    p1_alamat = kontrak.pihak_pertama_alamat or "—"
    p1_npwp   = kontrak.pihak_pertama_npwp or "—"
    p1_pic_nm, p1_pic_jb = _parse_pic(kontrak.pihak_pertama_pic)

    p2_nama   = kontrak.pihak_kedua_nama or "—"
    p2_alamat = kontrak.pihak_kedua_alamat or "—"
    p2_npwp   = kontrak.pihak_kedua_npwp or "—"
    p2_pic_nm, p2_pic_jb = _parse_pic(kontrak.pihak_kedua_pic)

    judul     = kontrak.judul_kontrak or "Perjanjian Kerjasama"
    deskripsi = kontrak.deskripsi or "layanan/produk sesuai kesepakatan"
    nilai     = kontrak.nilai_kontrak or 0
    nilai_rp  = f"Rp {nilai:,}".replace(",", ".") if nilai else "Sesuai Kesepakatan"
    nilai_tb  = _terbilang(nilai).title() + " Rupiah" if nilai else "sesuai kesepakatan"

    tgl_mulai  = _format_tanggal_id(kontrak.tanggal_mulai)
    tgl_selesai = _format_tanggal_id(kontrak.tanggal_selesai)

    # Hitung durasi tahun jika ada tanggal
    durasi_str = "—"
    if kontrak.tanggal_mulai and kontrak.tanggal_selesai:
        delta = kontrak.tanggal_selesai - kontrak.tanggal_mulai
        tahun = round(delta.days / 365, 1)
        if tahun == int(tahun):
            n = int(tahun)
            tb = "satu" if n == 1 else _terbilang(n)
            durasi_str = f"{n} ({tb})"
        else:
            durasi_str = f"±{tahun}"

    # Kota (ambil kata terakhir dari alamat pihak 1 sebelum koma terakhir)
    try:
        kota = p1_alamat.split(",")[-2].strip().split()[-1]
    except Exception:
        kota = "Bandung"

    # ── Helper: footer setiap halaman ────────────────────────
    def draw_footer():
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.setLineWidth(0.5)
        c.line(ML, MB - 2*mm, MR, MB - 2*mm)
        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawString(ML, MB - 6*mm,
                     f"Dokumen dihasilkan secara elektronik oleh sistem SecureTransact  |  {kontrak.kode}")
        c.drawRightString(MR, MB - 6*mm, f"Halaman {page_num[0]}")

    # ── Helper: mulai halaman baru ────────────────────────────
    def new_page():
        draw_footer()
        c.showPage()
        page_num[0] += 1
        y[0] = H - 20 * mm

    # ── Helper: pastikan cukup ruang ─────────────────────────
    def ensure(need_pt):
        if y[0] - need_pt < MB + 5*mm:
            new_page()

    # ── Helper: cetak teks dengan word-wrap ──────────────────
    def draw_paragraph(text: str, font="Helvetica", size=10, indent=0,
                        gap_after=4, color=(0, 0, 0), line_spacing=5.5):
        c.setFont(font, size)
        c.setFillColorRGB(*color)
        words = text.split()
        line = ""
        x0 = ML + indent
        avail = TW - indent
        # approx char width
        avg_char_w = size * 0.52
        max_chars = int(avail / avg_char_w)
        for word in words:
            test = (line + " " + word).strip()
            if len(test) > max_chars and line:
                ensure(line_spacing + 1)
                c.drawString(x0, y[0], line)
                y[0] -= line_spacing
                line = word
            else:
                line = test
        if line:
            ensure(line_spacing + 1)
            c.drawString(x0, y[0], line)
            y[0] -= line_spacing
        y[0] -= gap_after

    # ── Helper: section header (PASAL) ───────────────────────
    def draw_section(title: str):
        ensure(14)
        y[0] -= 4
        c.setFont("Helvetica-Bold", 10.5)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(W / 2, y[0], title)
        y[0] -= 6

    # ── Helper: baris kiri-kanan (label: nilai) ──────────────
    def draw_kv(label: str, value: str, indent=5*mm):
        ensure(7)
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(ML + indent, y[0], label)
        c.setFont("Helvetica", 10)
        c.drawString(ML + indent + 45*mm, y[0], f": {value}")
        y[0] -= 5.5

    # ══════════════════════════════════════════════════════════
    # HALAMAN 1: HEADER SURAT
    # ══════════════════════════════════════════════════════════

    # Garis atas
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(2)
    c.line(ML, y[0], MR, y[0])
    y[0] -= 6

    # Judul utama
    c.setFont("Helvetica-Bold", 13)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(W / 2, y[0], "SURAT PERJANJIAN KERJA SAMA")
    y[0] -= 6
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W / 2, y[0], judul.upper())
    y[0] -= 5

    # Garis bawah header
    c.setLineWidth(2)
    c.line(ML, y[0], MR, y[0])
    c.setLineWidth(0.5)
    c.line(ML, y[0] - 1.5, MR, y[0] - 1.5)
    y[0] -= 8

    # Nomor surat
    # Format romawi untuk bulan
    ROMAWI = ["", "I", "II", "III", "IV", "V", "VI",
              "VII", "VIII", "IX", "X", "XI", "XII"]
    nomor_surat = f"{kontrak.kode}/PKS-B2B/{ROMAWI[tgl_buat.month]}/{tgl_buat.year}"
    c.setFont("Helvetica", 10)
    c.drawCentredString(W / 2, y[0], f"Nomor: {nomor_surat}")
    y[0] -= 10

    # ── Pembuka ───────────────────────────────────────────────
    draw_paragraph(
        f"Pada hari ini, {hari_buat}, tanggal {tanggal_buat}, bertempat di {kota}, "
        f"telah dibuat dan ditandatangani Perjanjian Kerja Sama (selanjutnya disebut "
        f"\"Perjanjian\") oleh dan antara pihak-pihak berikut:",
        size=10, gap_after=8
    )

    # ── PIHAK PERTAMA ─────────────────────────────────────────
    ensure(50)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(ML, y[0], "1.")
    draw_paragraph(f"Nama Perusahaan  : {p1_nama}", font="Helvetica-Bold", size=10, indent=7*mm, gap_after=1)
    draw_kv("Alamat", p1_alamat, indent=7*mm)
    if p1_npwp and p1_npwp != "—":
        draw_kv("NPWP", p1_npwp, indent=7*mm)
    draw_kv("Diwakili oleh", f"{p1_pic_nm}, selaku {p1_pic_jb}", indent=7*mm)
    draw_paragraph(
        f"Dalam hal ini bertindak untuk dan atas nama {p1_nama}, "
        f"selanjutnya disebut sebagai PIHAK PERTAMA.",
        size=10, indent=7*mm, gap_after=8
    )

    # ── PIHAK KEDUA ───────────────────────────────────────────
    ensure(50)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(ML, y[0], "2.")
    draw_paragraph(f"Nama Perusahaan  : {p2_nama}", font="Helvetica-Bold", size=10, indent=7*mm, gap_after=1)
    draw_kv("Alamat", p2_alamat, indent=7*mm)
    if p2_npwp and p2_npwp != "—":
        draw_kv("NPWP", p2_npwp, indent=7*mm)
    draw_kv("Diwakili oleh", f"{p2_pic_nm}, selaku {p2_pic_jb}", indent=7*mm)
    draw_paragraph(
        f"Dalam hal ini bertindak untuk dan atas nama {p2_nama}, "
        f"selanjutnya disebut sebagai PIHAK KEDUA.",
        size=10, indent=7*mm, gap_after=8
    )

    # ── Kalimat penghubung ─────────────────────────────────────
    draw_paragraph(
        "PIHAK PERTAMA dan PIHAK KEDUA secara bersama-sama disebut sebagai PARA PIHAK. "
        "PARA PIHAK dengan ini menerangkan dan menyatakan telah sepakat untuk mengadakan "
        "Perjanjian Kerja Sama dengan ketentuan-ketentuan sebagai berikut:",
        size=10, gap_after=10
    )

    # ══════════════════════════════════════════════════════════
    # PASAL-PASAL
    # ══════════════════════════════════════════════════════════

    # ── PASAL 1 ───────────────────────────────────────────────
    draw_section("PASAL 1")
    draw_section("RUANG LINGKUP DAN TUJUAN")

    draw_paragraph(
        f"1. PIHAK PERTAMA menunjuk PIHAK KEDUA dan PIHAK KEDUA menerima penunjukan tersebut "
        f"untuk menyediakan {deskripsi}.",
        size=10, gap_after=4
    )
    draw_paragraph(
        "2. Pelaksanaan ruang lingkup kerja sama akan dijabarkan lebih lanjut dalam Lampiran / "
        "Purchase Order (PO) yang merupakan satu kesatuan yang tidak terpisahkan dari Perjanjian ini.",
        size=10, gap_after=10
    )

    # ── PASAL 2 ───────────────────────────────────────────────
    draw_section("PASAL 2")
    draw_section("HAK DAN KEWAJIBAN")

    draw_paragraph("1. Hak dan Kewajiban PIHAK PERTAMA:", font="Helvetica-Bold", size=10, gap_after=2)
    draw_paragraph(
        "a. Berkewajiban melakukan pembayaran atas layanan/produk sesuai dengan ketentuan Pasal 4.",
        size=10, indent=8*mm, gap_after=2
    )
    draw_paragraph(
        "b. Berhak mendapatkan laporan berkala atas progres/pengiriman barang dari PIHAK KEDUA.",
        size=10, indent=8*mm, gap_after=6
    )
    draw_paragraph("2. Hak dan Kewajiban PIHAK KEDUA:", font="Helvetica-Bold", size=10, gap_after=2)
    draw_paragraph(
        "a. Berkewajiban menyediakan produk/layanan sesuai dengan standar kualitas (SLA) yang telah disepakati.",
        size=10, indent=8*mm, gap_after=2
    )
    draw_paragraph(
        "b. Berhak menerima pembayaran dari PIHAK PERTAMA sesuai dengan tagihan yang sah.",
        size=10, indent=8*mm, gap_after=10
    )

    # ── PASAL 3 ───────────────────────────────────────────────
    draw_section("PASAL 3")
    draw_section("JANGKA WAKTU")

    draw_paragraph(
        f"1. Perjanjian ini berlaku untuk jangka waktu {durasi_str} tahun, terhitung sejak "
        f"tanggal {tgl_mulai} sampai dengan tanggal {tgl_selesai}.",
        size=10, gap_after=4
    )
    draw_paragraph(
        "2. Apabila PARA PIHAK bermaksud untuk memperpanjang jangka waktu Perjanjian, maka "
        "pemberitahuan tertulis harus disampaikan selambat-lambatnya 30 (tiga puluh) hari "
        "kalender sebelum masa Perjanjian berakhir.",
        size=10, gap_after=10
    )

    # ── PASAL 4 ───────────────────────────────────────────────
    draw_section("PASAL 4")
    draw_section("KETENTUAN HARGA DAN PEMBAYARAN")

    draw_paragraph(
        f"1. Total biaya atas pengadaan barang/jasa ini adalah sebesar {nilai_rp} "
        f"({nilai_tb}), sudah termasuk pajak yang berlaku.",
        size=10, gap_after=4
    )
    draw_paragraph(
        f"2. Pembayaran akan dilakukan oleh PIHAK PERTAMA melalui transfer bank ke rekening "
        f"yang ditunjuk secara resmi oleh PIHAK KEDUA.",
        size=10, gap_after=4
    )
    draw_paragraph(
        "3. Pembayaran dilunasi dalam jangka waktu 14 (empat belas) hari kalender setelah "
        "dokumen penagihan (Invoice dan Faktur Pajak) diterima dengan lengkap oleh PIHAK PERTAMA.",
        size=10, gap_after=10
    )

    # ── PASAL 5 ───────────────────────────────────────────────
    draw_section("PASAL 5")
    draw_section("KERAHASIAAN (CONFIDENTIALITY)")

    draw_paragraph(
        "PARA PIHAK wajib menjaga kerahasiaan seluruh data, informasi, dokumen, dan rahasia "
        "dagang milik pihak lainnya, dan dilarang memberikannya kepada pihak ketiga mana pun "
        "tanpa persetujuan tertulis terlebih dahulu, kecuali diwajibkan oleh hukum yang berlaku.",
        size=10, gap_after=10
    )

    # ── PASAL 6 ───────────────────────────────────────────────
    draw_section("PASAL 6")
    draw_section("PENYELESAIAN SENGKETA")

    draw_paragraph(
        "1. Setiap perselisihan atau perbedaan pendapat yang timbul sehubungan dengan Perjanjian "
        "ini akan diselesaikan terlebih dahulu secara musyawarah untuk mufakat.",
        size=10, gap_after=4
    )
    draw_paragraph(
        f"2. Apabila musyawarah tidak mencapai mufakat, maka PARA PIHAK sepakat untuk menyelesaikan "
        f"sengketa tersebut melalui Badan Arbitrase Nasional Indonesia (BANI) atau Kepaniteraan "
        f"Pengadilan Negeri {kota}.",
        size=10, gap_after=10
    )

    # ── PASAL 7 ───────────────────────────────────────────────
    draw_section("PASAL 7")
    draw_section("KEADAAN KAHAR (FORCE MAJEURE)")

    draw_paragraph(
        "1. Keadaan Kahar meliputi peristiwa bencana alam, kebakaran, pemogokan massal, perang, "
        "kebijakan pemerintah yang membatasi operasional, wabah penyakit, dan kejadian lain di "
        "luar kekuasaan PARA PIHAK.",
        size=10, gap_after=4
    )
    draw_paragraph(
        "2. Pihak yang mengalami Keadaan Kahar harus memberitahukan secara tertulis kepada pihak "
        "lainnya paling lambat 7 (tujuh) hari kalender sejak terjadinya peristiwa tersebut.",
        size=10, gap_after=10
    )

    # ── PASAL 8 ───────────────────────────────────────────────
    draw_section("PASAL 8")
    draw_section("PENUTUP")

    draw_paragraph(
        "Demikian Perjanjian ini dibuat dalam rangkap 2 (dua) yang masing-masing bermaterai cukup "
        "dan mempunyai kekuatan hukum yang sama, ditandatangani oleh PARA PIHAK dalam keadaan "
        "sadar dan tanpa ada unsur paksaan dari pihak mana pun.",
        size=10, gap_after=12
    )

    # ── TANDA TANGAN ──────────────────────────────────────────
    ensure(80)
    sig_w = (TW - 10*mm) / 2
    sig_l = ML
    sig_r = ML + sig_w + 10*mm

    # Label pihak
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(sig_l + sig_w / 2, y[0], "PIHAK PERTAMA")
    c.drawCentredString(sig_r + sig_w / 2, y[0], "PIHAK KEDUA")
    y[0] -= 5

    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(sig_l + sig_w / 2, y[0], p1_nama[:32])
    c.drawCentredString(sig_r + sig_w / 2, y[0], p2_nama[:32])
    y[0] -= 4

    # Kotak tanda tangan
    box_h = 28 * mm
    c.setStrokeColorRGB(0.4, 0.4, 0.4)
    c.setLineWidth(0.7)
    c.rect(sig_l, y[0] - box_h, sig_w, box_h)
    c.rect(sig_r, y[0] - box_h, sig_w, box_h)

    # Label dalam kotak
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.55, 0.55, 0.55)
    c.drawCentredString(sig_l + sig_w / 2, y[0] - box_h / 2, "(Tanda Tangan & Stempel Perusahaan)")
    c.drawCentredString(sig_r + sig_w / 2, y[0] - box_h / 2, "(Tanda Tangan & Stempel Perusahaan)")
    y[0] -= box_h + 5

    # Nama & jabatan di bawah kotak
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(sig_l + sig_w / 2, y[0], p1_pic_nm)
    c.drawCentredString(sig_r + sig_w / 2, y[0], p2_pic_nm)
    y[0] -= 5
    c.setFont("Helvetica", 9)
    c.drawCentredString(sig_l + sig_w / 2, y[0], p1_pic_jb)
    c.drawCentredString(sig_r + sig_w / 2, y[0], p2_pic_jb)
    y[0] -= 14

    # ── Info verifikasi kriptografi ───────────────────────────
    ensure(20)
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.setLineWidth(0.5)
    c.line(ML, y[0], MR, y[0])
    y[0] -= 6
    c.setFont("Helvetica", 7.5)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(ML, y[0], f"Dokumen ini ditandatangani secara elektronik dan dilindungi dengan kriptografi SHA-256.")
    y[0] -= 5
    c.drawString(ML, y[0], f"ID Kontrak: {kontrak.kode}  |  Dibuat oleh: {pembuat_username}  |  "
                            f"Tanggal: {tanggal_buat}")

    # ── Footer halaman terakhir ───────────────────────────────
    draw_footer()
    c.save()
    return buf.getvalue()







@router.get("/", summary="Daftar semua kontrak B2B")
def list_b2b(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = db.query(KontrakB2B).order_by(KontrakB2B.id.desc()).all()
    return {"status": "success", "data": [KontrakB2BResponse.model_validate(k) for k in items]}


@router.get("/{kontrak_id}", summary="Detail kontrak B2B")
def get_b2b(
    kontrak_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    k = db.query(KontrakB2B).filter(KontrakB2B.id == kontrak_id).first()
    if not k:
        raise HTTPException(status_code=404, detail="Kontrak B2B tidak ditemukan.")
    return {"status": "success", "data": KontrakB2BResponse.model_validate(k)}


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Buat kontrak B2B baru")
def create_b2b(
    payload: KontrakB2BCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Buat record dulu untuk dapat ID → kode
    k = KontrakB2B(
        kode="__placeholder__",
        pihak_pertama_nama=payload.pihak_pertama.nama,
        pihak_pertama_alamat=payload.pihak_pertama.alamat,
        pihak_pertama_npwp=payload.pihak_pertama.npwp,
        pihak_pertama_pic=payload.pihak_pertama.pic,
        pihak_kedua_nama=payload.pihak_kedua.nama,
        pihak_kedua_alamat=payload.pihak_kedua.alamat,
        pihak_kedua_npwp=payload.pihak_kedua.npwp,
        pihak_kedua_pic=payload.pihak_kedua.pic,
        judul_kontrak=payload.judul_kontrak,
        deskripsi=payload.deskripsi,
        nilai_kontrak=payload.nilai_kontrak,
        tanggal_mulai=payload.tanggal_mulai,
        tanggal_selesai=payload.tanggal_selesai,
        status="draft",
        created_by=current_user.id,
    )
    db.add(k)
    db.flush()
    k.kode = f"B2B{k.id:03d}"

    # Generate hash awal dari metadata
    raw = f"{k.kode}|{k.pihak_pertama_nama}|{k.pihak_kedua_nama}|{k.judul_kontrak}"
    k.hash_doc = hashlib.sha256(raw.encode()).hexdigest()

    db.commit()
    db.refresh(k)
    return {
        "status": "success",
        "message": f"Kontrak B2B '{k.kode}' berhasil dibuat.",
        "data": KontrakB2BResponse.model_validate(k)
    }


@router.put("/{kontrak_id}", summary="Update status/detail kontrak B2B")
def update_b2b(
    kontrak_id: int,
    payload: KontrakB2BUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    k = db.query(KontrakB2B).filter(KontrakB2B.id == kontrak_id).first()
    if not k:
        raise HTTPException(status_code=404, detail="Kontrak B2B tidak ditemukan.")

    valid_statuses = {"draft", "aktif", "selesai", "batal"}
    if payload.status and payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status tidak valid. Pilih: {valid_statuses}")

    if payload.status is not None:
        k.status = payload.status
    if payload.deskripsi is not None:
        k.deskripsi = payload.deskripsi
    if payload.nilai_kontrak is not None:
        k.nilai_kontrak = payload.nilai_kontrak
    if payload.tanggal_mulai is not None:
        k.tanggal_mulai = payload.tanggal_mulai
    if payload.tanggal_selesai is not None:
        k.tanggal_selesai = payload.tanggal_selesai

    db.commit()
    db.refresh(k)
    return {"status": "success", "message": "Kontrak B2B diperbarui.", "data": KontrakB2BResponse.model_validate(k)}


@router.delete("/{kontrak_id}", summary="Hapus kontrak B2B")
def delete_b2b(
    kontrak_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    k = db.query(KontrakB2B).filter(KontrakB2B.id == kontrak_id).first()
    if not k:
        raise HTTPException(status_code=404, detail="Kontrak B2B tidak ditemukan.")
    db.delete(k)
    db.commit()
    return {"status": "success", "message": f"Kontrak B2B '{k.kode}' dihapus."}


@router.post("/{kontrak_id}/generate-pdf", summary="Generate PDF kontrak B2B")
def generate_b2b_pdf(
    kontrak_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    k = db.query(KontrakB2B).filter(KontrakB2B.id == kontrak_id).first()
    if not k:
        raise HTTPException(status_code=404, detail="Kontrak B2B tidak ditemukan.")

    pembuat = db.query(User).filter(User.id == k.created_by).first()
    pembuat_name = pembuat.username if pembuat else current_user.username

    pdf_bytes = _build_b2b_pdf(k, pembuat_name)
    hash_doc = hashlib.sha256(pdf_bytes).hexdigest()
    k.hash_doc = hash_doc

    os.makedirs(PDF_DIR, exist_ok=True)
    pdf_path = os.path.join(PDF_DIR, f"{k.kode}.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    db.commit()
    return {
        "status": "success",
        "message": f"PDF kontrak B2B '{k.kode}' berhasil digenerate.",
        "data": {"kode": k.kode, "hash_doc": hash_doc, "pdf_size_bytes": len(pdf_bytes)}
    }


@router.get("/{kontrak_id}/pdf", summary="Lihat/unduh PDF kontrak B2B")
def get_b2b_pdf(
    kontrak_id: int,
    download: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    k = db.query(KontrakB2B).filter(KontrakB2B.id == kontrak_id).first()
    if not k:
        raise HTTPException(status_code=404, detail="Kontrak B2B tidak ditemukan.")

    pdf_path = os.path.join(PDF_DIR, f"{k.kode}.pdf")
    if not os.path.exists(pdf_path):
        # Auto-generate jika belum ada
        pembuat = db.query(User).filter(User.id == k.created_by).first()
        pembuat_name = pembuat.username if pembuat else current_user.username
        pdf_bytes = _build_b2b_pdf(k, pembuat_name)
        hash_doc = hashlib.sha256(pdf_bytes).hexdigest()
        k.hash_doc = hash_doc
        os.makedirs(PDF_DIR, exist_ok=True)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        db.commit()

    disposition = "attachment" if download else "inline"
    return FileResponse(
        path=pdf_path,
        filename=f"KontrakB2B_{k.kode}.pdf",
        media_type="application/pdf",
        headers={"Content-Disposition": f"{disposition}; filename=KontrakB2B_{k.kode}.pdf"}
    )


@router.post("/{kontrak_id}/verify", summary="Verifikasi integritas kontrak B2B")
def verify_b2b(
    kontrak_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    k = db.query(KontrakB2B).filter(KontrakB2B.id == kontrak_id).first()
    if not k:
        raise HTTPException(status_code=404, detail="Kontrak B2B tidak ditemukan.")

    pdf_path = os.path.join(PDF_DIR, f"{k.kode}.pdf")
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            computed = hashlib.sha256(f.read()).hexdigest()
        pdf_exists = True
    else:
        raw = f"{k.kode}|{k.pihak_pertama_nama}|{k.pihak_kedua_nama}|{k.judul_kontrak}"
        computed = hashlib.sha256(raw.encode()).hexdigest()
        pdf_exists = False

    is_valid = computed == k.hash_doc
    return {
        "status": "success",
        "data": {
            "id": k.id,
            "kode": k.kode,
            "is_valid": is_valid,
            "pdf_exists": pdf_exists,
            "hash_stored": k.hash_doc,
            "hash_computed": computed,
            "verified_at": datetime.now()
        }
    }
