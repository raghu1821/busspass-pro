"""
Script to regenerate all existing QR codes with the new verification URL format.
Run once: python regen_qr.py
"""
import mysql.connector
import qrcode
import os

db_config = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "admin123"),
    "database": os.getenv("DB_NAME", "buspassdb"),
    "port":     int(os.getenv("DB_PORT", 3306))
}

db = mysql.connector.connect(**db_config)
cursor = db.cursor(dictionary=True)
cursor.execute("SELECT * FROM Pass")
passes = cursor.fetchall()

BASE_URL = "https://busspass-pro.onrender.com"
folder = os.path.join(os.getcwd(), "static", "qrcodes")
os.makedirs(folder, exist_ok=True)

for p in passes:
    pid = p["pass_id"]
    url = f"{BASE_URL}/verify/{pid}"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0d1117", back_color="white")
    path = os.path.join(folder, f"pass_{pid}.png")
    img.save(path)
    print(f"[OK] Regenerated QR for Pass #{pid} -> {url}")

db.close()
print(f"\nDone! {len(passes)} QR codes regenerated.")
