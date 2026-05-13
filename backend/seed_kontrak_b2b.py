"""
seed_kontrak_b2b.py
Mengisi tabel kontrak_b2b dengan data contoh realistis antar perusahaan.

Cara pakai (dari root proyek):
    python backend/seed_kontrak_b2b.py

Atau dengan venv aktif:
    venv\\Scripts\\python.exe backend\\seed_kontrak_b2b.py
"""

import sys
import os
import hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from backend.database import SessionLocal, Base, engine
from backend.models import KontrakB2B, User

# Pastikan tabel ada
Base.metadata.create_all(bind=engine)


# ── Data contoh kontrak B2B ──────────────────────────────────
SAMPLE_CONTRACTS = [
    {
        "pihak_pertama_nama":    "PT SecureTransact Indonesia",
        "pihak_pertama_alamat":  "Jl. Ganesha No. 10, Bandung, Jawa Barat 40132",
        "pihak_pertama_npwp":    "01.234.567.8-001.000",
        "pihak_pertama_pic":     "Budi Santoso, S.T., Direktur Utama",

        "pihak_kedua_nama":      "PT Mitra Teknologi Nusantara",
        "pihak_kedua_alamat":    "Gedung Cyber 2 Lt. 11, Jl. HR. Rasuna Said, Jakarta 12950",
        "pihak_kedua_npwp":      "02.345.678.9-010.000",
        "pihak_kedua_pic":       "Dewi Rahayu, M.M., Direktur Operasional",

        "judul_kontrak":  "Perjanjian Kerjasama Pengembangan Sistem Informasi Terintegrasi",
        "deskripsi": (
            "Kontrak ini mengatur kerjasama pengembangan dan implementasi Sistem Informasi "
            "Terintegrasi berbasis cloud untuk kebutuhan manajemen transaksi, inventaris, dan "
            "pelaporan keuangan PT SecureTransact Indonesia. Cakupan pekerjaan meliputi: "
            "analisis kebutuhan, desain sistem, pengembangan modul, testing, deployment, dan "
            "pemeliharaan selama 12 bulan pertama."
        ),
        "nilai_kontrak":   450_000_000,
        "tanggal_mulai":   datetime(2026, 1, 15, tzinfo=timezone.utc),
        "tanggal_selesai": datetime(2026, 12, 31, tzinfo=timezone.utc),
        "status":          "aktif",
    },
    {
        "pihak_pertama_nama":    "PT SecureTransact Indonesia",
        "pihak_pertama_alamat":  "Jl. Ganesha No. 10, Bandung, Jawa Barat 40132",
        "pihak_pertama_npwp":    "01.234.567.8-001.000",
        "pihak_pertama_pic":     "Rina Wulandari, Kepala Pengadaan",

        "pihak_kedua_nama":      "CV Sumber Makmur Logistik",
        "pihak_kedua_alamat":    "Jl. Raya Industri No. 45, Cikarang, Bekasi 17530",
        "pihak_kedua_npwp":      "73.456.789.0-411.000",
        "pihak_kedua_pic":       "Hendra Gunawan, Pimpinan",

        "judul_kontrak":  "Kontrak Pengadaan Perlengkapan Kantor & Perangkat Keras IT",
        "deskripsi": (
            "Perjanjian pengadaan perlengkapan kantor dan perangkat keras IT untuk mendukung "
            "operasional PT SecureTransact Indonesia tahun fiskal 2026. Barang yang diadakan "
            "meliputi: workstation, laptop, peripheral, furnitur kantor, dan perlengkapan "
            "jaringan. Pengiriman dilakukan secara bertahap sesuai jadwal yang disepakati."
        ),
        "nilai_kontrak":   185_000_000,
        "tanggal_mulai":   datetime(2026, 2, 1, tzinfo=timezone.utc),
        "tanggal_selesai": datetime(2026, 7, 31, tzinfo=timezone.utc),
        "status":          "aktif",
    },
    {
        "pihak_pertama_nama":    "PT SecureTransact Indonesia",
        "pihak_pertama_alamat":  "Jl. Ganesha No. 10, Bandung, Jawa Barat 40132",
        "pihak_pertama_npwp":    "01.234.567.8-001.000",
        "pihak_pertama_pic":     "Ahmad Fauzi, General Manager",

        "pihak_kedua_nama":      "PT Konsultan Bisnis Andalan",
        "pihak_kedua_alamat":    "Jl. Sudirman Kav. 52-53, Jakarta Pusat 10220",
        "pihak_kedua_npwp":      "05.678.901.2-021.000",
        "pihak_kedua_pic":       "Dr. Siti Aminah, M.B.A., Managing Partner",

        "judul_kontrak":  "Perjanjian Jasa Konsultasi Strategi Bisnis & Transformasi Digital",
        "deskripsi": (
            "Kontrak jasa konsultasi strategis untuk mendampingi PT SecureTransact Indonesia "
            "dalam proses transformasi digital dan pengembangan strategi bisnis jangka menengah "
            "(2026-2028). Layanan meliputi: audit proses bisnis, perumusan roadmap digital, "
            "pelatihan SDM, dan pendampingan implementasi teknologi baru."
        ),
        "nilai_kontrak":   275_000_000,
        "tanggal_mulai":   datetime(2026, 3, 1, tzinfo=timezone.utc),
        "tanggal_selesai": datetime(2027, 2, 28, tzinfo=timezone.utc),
        "status":          "aktif",
    },
    {
        "pihak_pertama_nama":    "PT SecureTransact Indonesia",
        "pihak_pertama_alamat":  "Jl. Ganesha No. 10, Bandung, Jawa Barat 40132",
        "pihak_pertama_npwp":    "01.234.567.8-001.000",
        "pihak_pertama_pic":     "Budi Santoso, S.T., Direktur Utama",

        "pihak_kedua_nama":      "PT Keamanan Siber Prima",
        "pihak_kedua_alamat":    "Jl. TB Simatupang No. 18, Jakarta Selatan 12430",
        "pihak_kedua_npwp":      "08.901.234.5-013.000",
        "pihak_kedua_pic":       "Ir. Andika Pratama, CEO",

        "judul_kontrak":  "Perjanjian Layanan Keamanan Siber & Audit Sistem Berkala",
        "deskripsi": (
            "Kontrak layanan keamanan informasi komprehensif meliputi: penetration testing "
            "kuartalan, monitoring keamanan 24/7, respons insiden siber, audit kepatuhan ISO "
            "27001, serta pelatihan kesadaran keamanan bagi karyawan. Kontrak berlaku selama "
            "2 tahun dengan opsi perpanjangan."
        ),
        "nilai_kontrak":   120_000_000,
        "tanggal_mulai":   datetime(2025, 7, 1, tzinfo=timezone.utc),
        "tanggal_selesai": datetime(2026, 6, 30, tzinfo=timezone.utc),
        "status":          "selesai",
    },
    {
        "pihak_pertama_nama":    "PT SecureTransact Indonesia",
        "pihak_pertama_alamat":  "Jl. Ganesha No. 10, Bandung, Jawa Barat 40132",
        "pihak_pertama_npwp":    "01.234.567.8-001.000",
        "pihak_pertama_pic":     "Rina Wulandari, Kepala Pengadaan",

        "pihak_kedua_nama":      "PT CloudNesia Infrastruktur",
        "pihak_kedua_alamat":    "Wisma 46 Lt. 22, Jl. Jend. Sudirman Kav. 22-23, Jakarta 10220",
        "pihak_kedua_npwp":      "11.234.567.8-022.000",
        "pihak_kedua_pic":       "Michael Tanaka, Country Director",

        "judul_kontrak":  "Kontrak Sewa Infrastruktur Cloud & Layanan Hosting Terkelola",
        "deskripsi": (
            "Perjanjian penggunaan layanan cloud computing mencakup: virtual private server, "
            "penyimpanan objek (object storage), CDN, load balancer, dan managed database "
            "service. SLA uptime 99.9% dijamin dengan kompensasi kredit otomatis. Termasuk "
            "dukungan teknis 24/7 via dedicated account manager."
        ),
        "nilai_kontrak":   96_000_000,
        "tanggal_mulai":   datetime(2026, 1, 1, tzinfo=timezone.utc),
        "tanggal_selesai": datetime(2026, 12, 31, tzinfo=timezone.utc),
        "status":          "aktif",
    },
    {
        "pihak_pertama_nama":    "PT SecureTransact Indonesia",
        "pihak_pertama_alamat":  "Jl. Ganesha No. 10, Bandung, Jawa Barat 40132",
        "pihak_pertama_npwp":    "01.234.567.8-001.000",
        "pihak_pertama_pic":     "Ahmad Fauzi, General Manager",

        "pihak_kedua_nama":      "PT Anugerah Jasa Ketenagakerjaan",
        "pihak_kedua_alamat":    "Jl. Asia Afrika No. 99, Bandung, Jawa Barat 40111",
        "pihak_kedua_npwp":      "14.567.890.1-404.000",
        "pihak_kedua_pic":       "Lestari Handayani, Direktur",

        "judul_kontrak":  "Perjanjian Alih Daya (Outsourcing) Tenaga Kerja Divisi Customer Service",
        "deskripsi": (
            "Kontrak penyediaan tenaga kerja alih daya untuk divisi Customer Service & Support "
            "PT SecureTransact Indonesia. Jumlah tenaga kerja: 15 orang. Layanan mencakup: "
            "rekrutmen, pelatihan, penggajian, administrasi ketenagakerjaan, dan pemantauan "
            "kinerja. Penyedia wajib memastikan kepatuhan terhadap UU Ketenagakerjaan."
        ),
        "nilai_kontrak":   216_000_000,
        "tanggal_mulai":   datetime(2026, 4, 1, tzinfo=timezone.utc),
        "tanggal_selesai": datetime(2027, 3, 31, tzinfo=timezone.utc),
        "status":          "draft",
    },
    {
        "pihak_pertama_nama":    "PT SecureTransact Indonesia",
        "pihak_pertama_alamat":  "Jl. Ganesha No. 10, Bandung, Jawa Barat 40132",
        "pihak_pertama_npwp":    "01.234.567.8-001.000",
        "pihak_pertama_pic":     "Budi Santoso, S.T., Direktur Utama",

        "pihak_kedua_nama":      "PT Digital Marketing Kreatif",
        "pihak_kedua_alamat":    "Jl. Braga No. 5, Bandung, Jawa Barat 40111",
        "pihak_kedua_npwp":      "17.890.123.4-424.000",
        "pihak_kedua_pic":       "Fajar Nugroho, Creative Director",

        "judul_kontrak":  "Kontrak Layanan Pemasaran Digital & Branding Korporat",
        "deskripsi": (
            "Perjanjian jasa pemasaran digital komprehensif meliputi: manajemen media sosial "
            "(Instagram, LinkedIn, X/Twitter), iklan berbayar (Google Ads, Meta Ads), "
            "pembuatan konten bulanan, SEO on-page & off-page, serta laporan analitik mingguan. "
            "Target: peningkatan organic traffic 40% dan brand awareness dalam 6 bulan."
        ),
        "nilai_kontrak":   84_000_000,
        "tanggal_mulai":   datetime(2025, 10, 1, tzinfo=timezone.utc),
        "tanggal_selesai": datetime(2026, 3, 31, tzinfo=timezone.utc),
        "status":          "batal",
    },
    {
        "pihak_pertama_nama":    "PT SecureTransact Indonesia",
        "pihak_pertama_alamat":  "Jl. Ganesha No. 10, Bandung, Jawa Barat 40132",
        "pihak_pertama_npwp":    "01.234.567.8-001.000",
        "pihak_pertama_pic":     "Rina Wulandari, Kepala Pengadaan",

        "pihak_kedua_nama":      "PT Asuransi Proteksi Bisnis",
        "pihak_kedua_alamat":    "Menara BRI Lt. 20, Jl. Jend. Sudirman Kav. 44-46, Jakarta 10210",
        "pihak_kedua_npwp":      "20.123.456.7-201.000",
        "pihak_kedua_pic":       "dr. Kartika Sari, Direktur Layanan Korporat",

        "judul_kontrak":  "Perjanjian Asuransi Korporat & Perlindungan Aset Perusahaan",
        "deskripsi": (
            "Kontrak paket asuransi korporat komprehensif mencakup: asuransi jiwa kumpulan "
            "untuk 50 karyawan, asuransi kecelakaan kerja, asuransi properti kantor, "
            "asuransi tanggung gugat pihak ketiga, dan asuransi siber (cyber liability). "
            "Premi dibayarkan secara tahunan dengan laporan klaim triwulanan."
        ),
        "nilai_kontrak":   48_000_000,
        "tanggal_mulai":   datetime(2026, 1, 1, tzinfo=timezone.utc),
        "tanggal_selesai": datetime(2026, 12, 31, tzinfo=timezone.utc),
        "status":          "aktif",
    },
]


def seed_kontrak_b2b():
    db = SessionLocal()
    try:
        existing = db.query(KontrakB2B).count()
        if existing > 0:
            print(f"Skip — sudah ada {existing} kontrak B2B di database.")
            print("Hapus data lama terlebih dahulu jika ingin seed ulang.")
            return

        # Cari user admin untuk assigned sebagai creator
        admin_user = db.query(User).filter(User.role == "admin").first()
        creator_id = admin_user.id if admin_user else None

        print(f"\nMengisi {len(SAMPLE_CONTRACTS)} kontrak B2B...\n")

        for i, data in enumerate(SAMPLE_CONTRACTS, start=1):
            k = KontrakB2B(
                kode="__placeholder__",
                **data,
                hash_doc=None,
                created_by=creator_id,
            )
            db.add(k)
            db.flush()

            # Generate kode setelah ID diketahui
            k.kode = f"B2B{k.id:03d}"

            # Generate hash metadata
            raw = f"{k.kode}|{k.pihak_pertama_nama}|{k.pihak_kedua_nama}|{k.judul_kontrak}"
            k.hash_doc = hashlib.sha256(raw.encode()).hexdigest()

            print(f"  [{i:02d}] {k.kode} — {k.judul_kontrak[:55]}...")
            print(f"        {k.pihak_pertama_nama} -> {k.pihak_kedua_nama}")
            print(f"        Nilai : Rp {k.nilai_kontrak:>15,}  |  Status: {k.status.upper()}")
            print(f"        Hash  : {k.hash_doc[:32]}...")
            print()

        db.commit()
        print("-" * 60)
        print(f"Selesai! {len(SAMPLE_CONTRACTS)} kontrak B2B berhasil ditambahkan.")
        print()
        print("Ringkasan status:")
        for status in ["aktif", "draft", "selesai", "batal"]:
            count = sum(1 for d in SAMPLE_CONTRACTS if d["status"] == status)
            if count:
                label = {"aktif": "Aktif", "draft": "Draft", "selesai": "Selesai", "batal": "Batal"}[status]
                print(f"  {label:10s}: {count} kontrak")
        print()
        print("Jalankan endpoint /kontrak-b2b/{id}/generate-pdf untuk generate PDF.")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_kontrak_b2b()
