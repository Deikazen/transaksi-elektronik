"""
Router: Deteksi Uang Palsu
Menganalisis gambar uang rupiah dari kamera menggunakan OpenCV
untuk mendeteksi ciri-ciri keaslian berdasarkan fitur visual.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import numpy as np
import io
import time
import math

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

router = APIRouter(prefix="/deteksi-uang", tags=["Deteksi Uang Palsu"])


def analyze_money_image(img_array: np.ndarray) -> dict:
    """
    Analisis gambar uang dengan berbagai teknik computer vision.
    Mengembalikan skor dan detail tiap indikator keaslian.
    """
    results = {}
    scores = []

    h, w = img_array.shape[:2]
    if h == 0 or w == 0:
        raise ValueError("Gambar tidak valid")

    # ── 1. ANALISIS WARNA & SATURASI ──────────────────────────────────────────
    # Uang asli memiliki warna yang kaya dan konsisten (tidak terlalu pucat/jenuh)
    hsv = cv2.cvtColor(img_array, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    avg_sat = float(np.mean(saturation))
    sat_std = float(np.std(saturation))

    # Uang asli: saturation 60–160, variasi cukup (bukan foto putih polos / terlalu colorful)
    if 50 <= avg_sat <= 170 and sat_std > 15:
        color_score = min(100, int(50 + avg_sat / 3))
        color_status = "Baik"
        color_detail = f"Saturasi rata-rata: {avg_sat:.1f} (normal)"
    elif avg_sat < 30:
        color_score = 25
        color_status = "Mencurigakan"
        color_detail = f"Gambar terlalu pucat/putih (sat: {avg_sat:.1f})"
    else:
        color_score = 60
        color_status = "Perlu Pemeriksaan"
        color_detail = f"Saturasi: {avg_sat:.1f}, variasi: {sat_std:.1f}"
    results["analisis_warna"] = {"skor": color_score, "status": color_status, "detail": color_detail}
    scores.append(color_score)

    # ── 2. DETEKSI TEPI & KETAJAMAN (Laplacian Variance) ──────────────────────
    # Uang asli: cetak intaglio menghasilkan detail tepi yang tajam dan banyak
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    sharpness = float(laplacian.var())

    if sharpness > 300:
        sharp_score = min(100, int(50 + math.log(sharpness) * 5))
        sharp_status = "Sangat Tajam"
        sharp_detail = f"Var. Laplacian: {sharpness:.1f} — Detail cetak baik"
    elif sharpness > 80:
        sharp_score = 65
        sharp_status = "Cukup Tajam"
        sharp_detail = f"Var. Laplacian: {sharpness:.1f} — Kualitas sedang"
    elif sharpness > 20:
        sharp_score = 40
        sharp_status = "Blur"
        sharp_detail = f"Var. Laplacian: {sharpness:.1f} — Foto buram, sulit dianalisis"
    else:
        sharp_score = 15
        sharp_status = "Sangat Blur"
        sharp_detail = f"Var. Laplacian: {sharpness:.1f} — Gambar terlalu buram"
    results["ketajaman_cetak"] = {"skor": sharp_score, "status": sharp_status, "detail": sharp_detail}
    scores.append(sharp_score)

    # ── 3. ANALISIS TEKSTUR (Local Binary Pattern via Gradient) ──────────────
    # Uang asli memiliki tekstur halus dan konsisten dari proses cetak khusus
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_mag = np.sqrt(sobelx**2 + sobely**2)
    texture_mean = float(np.mean(gradient_mag))
    texture_std = float(np.std(gradient_mag))

    # Tekstur seragam dengan variasi sedang = cetak berkualitas
    if 20 <= texture_mean <= 120 and texture_std > 10:
        texture_score = min(100, int(55 + texture_mean / 2))
        texture_status = "Tekstur Konsisten"
        texture_detail = f"Mean gradient: {texture_mean:.1f}, Std: {texture_std:.1f}"
    elif texture_mean < 10:
        texture_score = 20
        texture_status = "Terlalu Halus"
        texture_detail = f"Tidak ada detail cetak terdeteksi (gradient: {texture_mean:.1f})"
    else:
        texture_score = 50
        texture_status = "Variasi Tekstur Tinggi"
        texture_detail = f"Mean gradient: {texture_mean:.1f} — Mungkin permukaan kasar/rusak"
    results["tekstur_cetak"] = {"skor": texture_score, "status": texture_status, "detail": texture_detail}
    scores.append(texture_score)

    # ── 4. RASIO ASPEK (untuk mendeteksi gambar yang terpotong/terdistorsi) ──
    aspect = w / h if h > 0 else 0
    # Uang kertas umumnya 2:1 hingga 3:1 (landscape)
    if 1.5 <= aspect <= 4.0:
        aspect_score = 85
        aspect_status = "Proporsi Normal"
        aspect_detail = f"Rasio {w}×{h} = {aspect:.2f}:1 (landscape)"
    elif 0.25 <= aspect < 1.5:
        aspect_score = 55
        aspect_status = "Orientasi Portrait"
        aspect_detail = f"Rasio {w}×{h} = {aspect:.2f}:1 (putar gambar 90°)"
    else:
        aspect_score = 40
        aspect_status = "Proporsi Tidak Umum"
        aspect_detail = f"Rasio {w}×{h} = {aspect:.2f}:1 — kemungkinan terpotong"
    results["proporsi_ukuran"] = {"skor": aspect_score, "status": aspect_status, "detail": aspect_detail}
    scores.append(aspect_score)

    # ── 5. ANALISIS HISTOGRAM KECERAHAN ──────────────────────────────────────
    # Uang asli: distribusi histogram tidak terlalu ekstrim (bukan putih/hitam total)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist_normalized = hist.flatten() / hist.sum()
    # Cek apakah ada puncak ekstrim di ujung (overexposed / underexposed)
    dark_pct = float(hist_normalized[:30].sum()) * 100
    bright_pct = float(hist_normalized[225:].sum()) * 100
    mid_pct = 100 - dark_pct - bright_pct

    if mid_pct > 60 and dark_pct < 20 and bright_pct < 20:
        hist_score = 88
        hist_status = "Eksposur Baik"
        hist_detail = f"Distribusi merata: gelap {dark_pct:.1f}%, tengah {mid_pct:.1f}%, terang {bright_pct:.1f}%"
    elif bright_pct > 40:
        hist_score = 35
        hist_status = "Overexposed"
        hist_detail = f"Terlalu terang: {bright_pct:.1f}% piksel mendekati putih — foto ulang"
    elif dark_pct > 40:
        hist_score = 35
        hist_status = "Underexposed"
        hist_detail = f"Terlalu gelap: {dark_pct:.1f}% piksel mendekati hitam — foto ulang"
    else:
        hist_score = 65
        hist_status = "Perlu Penyesuaian"
        hist_detail = f"Gelap: {dark_pct:.1f}%, Tengah: {mid_pct:.1f}%, Terang: {bright_pct:.1f}%"
    results["eksposur_cahaya"] = {"skor": hist_score, "status": hist_status, "detail": hist_detail}
    scores.append(hist_score)

    # ── 6. DETEKSI KONTUR (Tepi Uang) ─────────────────────────────────────────
    # Uang asli memiliki tepi yang jelas dan lurus
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.mean(edges > 0)) * 100

    if 3 <= edge_density <= 25:
        edge_score = 80
        edge_status = "Tepi Normal"
        edge_detail = f"Kepadatan tepi: {edge_density:.1f}% — pola cetak terdeteksi"
    elif edge_density > 25:
        edge_score = 50
        edge_status = "Terlalu Banyak Tepi"
        edge_detail = f"Kepadatan tepi: {edge_density:.1f}% — mungkin ada noise/keriput"
    else:
        edge_score = 30
        edge_status = "Sedikit Detail"
        edge_detail = f"Kepadatan tepi: {edge_density:.1f}% — detail cetak tidak terdeteksi"
    results["deteksi_pola"] = {"skor": edge_score, "status": edge_status, "detail": edge_detail}
    scores.append(edge_score)

    # ── HITUNG SKOR KESELURUHAN ────────────────────────────────────────────────
    weights = [1.5, 2.0, 1.5, 0.8, 1.2, 1.0]  # ketajaman paling penting
    weighted_sum = sum(s * w for s, w in zip(scores, weights))
    weight_total = sum(weights)
    overall_score = int(weighted_sum / weight_total)

    return {
        "skor_keseluruhan": overall_score,
        "indikator": results,
        "resolusi": {"lebar": w, "tinggi": h, "piksel": w * h},
    }


def get_verdict(score: int) -> dict:
    """Tentukan verdict akhir berdasarkan skor keseluruhan."""
    if score >= 75:
        return {
            "verdict": "KEMUNGKINAN ASLI",
            "level": "aman",
            "emoji": "✅",
            "warna": "#10b981",
            "pesan": "Ciri-ciri visual uang ini sesuai dengan uang asli. Namun verifikasi manual tetap disarankan.",
            "rekomendasi": [
                "Periksa benang pengaman (hologram bergeser saat dimiringkan)",
                "Rasakan tekstur timbul pada angka nominal",
                "Periksa watermark dengan menerawang ke cahaya",
            ]
        }
    elif score >= 50:
        return {
            "verdict": "PERLU PEMERIKSAAN LANJUT",
            "level": "waspada",
            "emoji": "⚠️",
            "warna": "#f59e0b",
            "pesan": "Beberapa indikator visual tidak optimal. Foto ulang dengan pencahayaan lebih baik atau periksa secara manual.",
            "rekomendasi": [
                "Foto ulang dengan pencahayaan yang merata",
                "Pastikan seluruh permukaan uang terlihat jelas",
                "Gunakan alat UV/sinar ultraviolet untuk verifikasi",
            ]
        }
    else:
        return {
            "verdict": "MENCURIGAKAN / PERLU VERIFIKASI",
            "level": "bahaya",
            "emoji": "🚨",
            "warna": "#ef4444",
            "pesan": "Beberapa ciri visual tidak sesuai standar uang asli. Jangan gunakan hingga diverifikasi pihak berwenang.",
            "rekomendasi": [
                "Jangan gunakan atau menerima uang ini",
                "Bawa ke bank atau kantor Bank Indonesia terdekat",
                "Laporkan ke pihak berwajib jika diperlukan",
            ]
        }


@router.post("/analisis")
async def analisis_uang(file: UploadFile = File(...)):
    """
    Analisis gambar uang untuk mendeteksi keaslian.
    Terima file gambar (JPEG/PNG) dan kembalikan hasil analisis visual.
    """
    if not CV2_AVAILABLE:
        # Fallback jika OpenCV belum terinstall — berikan demo hasil
        import random
        demo_score = random.randint(45, 92)
        verdict = get_verdict(demo_score)
        return JSONResponse({
            "status": "demo",
            "pesan_sistem": "OpenCV tidak terinstall. Menampilkan hasil simulasi. Install dengan: pip install opencv-python",
            "skor_keseluruhan": demo_score,
            "verdict": verdict,
            "indikator": {
                "analisis_warna": {"skor": random.randint(50, 95), "status": "Baik", "detail": "Saturasi warna normal (simulasi)"},
                "ketajaman_cetak": {"skor": random.randint(50, 90), "status": "Cukup Tajam", "detail": "Detail cetak terdeteksi (simulasi)"},
                "tekstur_cetak": {"skor": random.randint(55, 85), "status": "Tekstur Konsisten", "detail": "Pola cetak halus (simulasi)"},
                "proporsi_ukuran": {"skor": 85, "status": "Proporsi Normal", "detail": "Rasio aspek normal (simulasi)"},
                "eksposur_cahaya": {"skor": random.randint(60, 90), "status": "Eksposur Baik", "detail": "Distribusi cahaya merata (simulasi)"},
                "deteksi_pola": {"skor": random.randint(55, 85), "status": "Tepi Normal", "detail": "Pola cetak terdeteksi (simulasi)"},
            },
            "resolusi": {"lebar": 1920, "tinggi": 1080, "piksel": 2073600},
            "waktu_analisis_ms": random.randint(80, 250),
        })

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File harus berupa gambar (JPEG/PNG)")

    contents = await file.read()
    if len(contents) < 1000:
        raise HTTPException(status_code=400, detail="File gambar terlalu kecil atau kosong")
    if len(contents) > 20 * 1024 * 1024:  # 20 MB limit
        raise HTTPException(status_code=400, detail="File gambar terlalu besar (maksimal 20MB)")

    start_time = time.time()

    try:
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Tidak dapat membaca gambar")

        # Resize jika terlalu besar (untuk performa)
        max_dim = 1200
        h, w = img.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)))

        analysis = analyze_money_image(img)
        elapsed_ms = int((time.time() - start_time) * 1000)
        verdict = get_verdict(analysis["skor_keseluruhan"])

        return JSONResponse({
            "status": "success",
            "skor_keseluruhan": analysis["skor_keseluruhan"],
            "verdict": verdict,
            "indikator": analysis["indikator"],
            "resolusi": analysis["resolusi"],
            "waktu_analisis_ms": elapsed_ms,
        })

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menganalisis gambar: {str(e)}")


@router.get("/status")
def status_deteksi():
    """Cek status ketersediaan fitur deteksi uang."""
    return {
        "cv2_available": CV2_AVAILABLE,
        "fitur": "Deteksi Uang Palsu via Kamera",
        "versi": "1.0.0",
        "metode": [
            "Analisis Warna & Saturasi (HSV)",
            "Ketajaman Cetak (Laplacian Variance)",
            "Analisis Tekstur (Sobel Gradient)",
            "Proporsi Ukuran (Aspect Ratio)",
            "Distribusi Histogram Kecerahan",
            "Deteksi Pola & Tepi (Canny)",
        ]
    }
