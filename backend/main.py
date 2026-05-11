from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import inventory, transaction, auth, kontrak, io_system, deteksi_uang, midtrans_payment, laporan

app = FastAPI(
    title="SecureTransact API",
    description="Backend API Tugas IFB-352 - Grup C10 ITENAS",
    version="1.0.0",
)

# CORS - izinkan frontend Vue
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from database import SessionLocal
from sqlalchemy import text

# Health check
@app.get("/", tags=["Health"])
def read_root():
    return {"status": "success", "message": "SecureTransact Backend berjalan!"}

@app.get("/system-status", tags=["Health"])
def get_system_status():
    db_status = "offline"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db_status = "online"
    except Exception:
        pass
    finally:
        try:
            db.close()
        except:
            pass

    return {
        "status": "success",
        "data": {
            "system_status": [
                {"name": "Backend FastAPI", "status": "online", "up": 100},
                {"name": "Database", "status": db_status, "up": 99 if db_status == "online" else 0},
                {"name": "Frontend Vue", "status": "online", "up": 100},
            ],
            "sec_checks": [
                {"name": "HTTPS / TLS 1.2+", "ok": True},
                {"name": "Rate Limiting", "ok": False},
                {"name": "JWT Authentication", "ok": True},
                {"name": "Input Validation", "ok": True},
            ]
        }
    }

# Register semua router
app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(transaction.router)
app.include_router(kontrak.router)
app.include_router(io_system.router)
app.include_router(deteksi_uang.router)
app.include_router(midtrans_payment.router)
app.include_router(laporan.router)

