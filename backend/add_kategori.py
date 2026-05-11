from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    db.execute(text("ALTER TABLE produk ADD COLUMN kategori VARCHAR(100) DEFAULT 'Umum'"))
    db.commit()
    print("kategori column added")
except Exception as e:
    if "Duplicate" in str(e):
        print("kategori column already exists")
    else:
        print(f"Error: {e}")
finally:
    db.close()
