import mysql.connector
from flask import Flask, render_template, request, session, redirect, send_file, jsonify
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import qrcode
from reportlab.pdfgen import canvas
import os
import random
import string
import threading
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.secret_key = os.getenv("SECRET_KEY", "buspasssecret2024xK9")

# ── Flask-Mail (OTP emails) ─────────────────────────────────────────────────
app.config["MAIL_SERVER"]   = "smtp.gmail.com"
app.config["MAIL_PORT"]     = 587
app.config["MAIL_USE_TLS"]  = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USER", "")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASS", "")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USER", "")
mail = Mail(app)

# ── Database Config ─────────────────────────────────────────────────────────
_db_config = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "admin123"),
    "database": os.getenv("DB_NAME", "buspassdb"),
    "port":     int(os.getenv("DB_PORT", 3306))
}
if _db_config["host"] != "localhost":
    _db_config["ssl_disabled"]        = False
    _db_config["ssl_verify_cert"]     = False
    _db_config["ssl_verify_identity"] = False

_db_conn = None

def get_db():
    """Return a live DB connection, reconnecting automatically if dropped."""
    global _db_conn
    try:
        if _db_conn is None or not _db_conn.is_connected():
            _db_conn = mysql.connector.connect(**_db_config)
    except Exception:
        _db_conn = mysql.connector.connect(**_db_config)
    return _db_conn

print("Database helper ready")

# ── Error Handlers ───────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500

@app.route("/")
def home():
    return render_template("index.html")

# ── Public Pass Verification (QR scan destination) ───────────────────────────
@app.route("/verify/<int:pass_id>")
def verify_pass(pass_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    # Auto-expire passes
    cursor.execute("UPDATE Pass SET status='Expired' WHERE valid_until < CURDATE()")
    db.commit()
    # Fetch pass with passenger photo
    cursor.execute("""
        SELECT Pass.*, Passenger.photo, Passenger.category
        FROM Pass
        JOIN Passenger ON Pass.passenger_name = Passenger.full_name
        WHERE Pass.pass_id = %s
    """, (pass_id,))
    pass_data = cursor.fetchone()
    return render_template("verify_pass.html", pass_data=pass_data)

# Serve PWA service worker from root path (required by browser spec)
@app.route("/sw.js")
def service_worker():
    from flask import send_from_directory
    return send_from_directory("static", "sw.js", mimetype="application/javascript")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        address = request.form["address"]
        category = request.form["category"]
        password = request.form["password"]

        # Photo Upload
        photo = request.files.get("photo")
        if not photo:
            return redirect("/register?msg=No+photo+uploaded.+Please+select+a+photo.&type=error")

        filename = secure_filename(photo.filename)

        photo.save(
            os.path.join(
                "static/uploads",
                filename
            )
        )

        cursor = get_db().cursor()

        query = """
INSERT INTO Passenger
(full_name, email, phone, address, category, password, photo)
VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

        values = (
    full_name,
    email,
    phone,
    address,
    category,
    password,
    filename
)

        cursor.execute(query, values)
        get_db().commit()

        return redirect("/login?msg=Account+created+successfully!+Please+sign+in.&type=success")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cursor = get_db().cursor(dictionary=True)

        query = """
        SELECT * FROM Passenger
        WHERE email=%s AND password=%s
        """

        cursor.execute(query, (email, password))

        user = cursor.fetchone()

        if user:
            session["user"] = user["full_name"]
            return redirect("/dashboard")

        else:
            return redirect("/login?msg=Invalid+email+or+password.+Please+try+again.&type=error")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]

    cursor = get_db().cursor(dictionary=True)

    query = """
SELECT
Pass_Application.*,
Route.source,
Route.destination
FROM Pass_Application
JOIN Route
ON Pass_Application.route_id = Route.route_id
WHERE passenger_name=%s
"""
    cursor.execute(query, (user,))

    applications = cursor.fetchall()

    return render_template(
        "dashboard.html",
        user=user,
        applications=applications
    )
@app.route("/view_pass")
def view_pass():
    if "user" not in session: return redirect("/login")

    if "user" not in session:
        return redirect("/login")

    user = session["user"]

    cursor = get_db().cursor(dictionary=True)

    update_query = """
    UPDATE Pass
    SET status='Expired'
    WHERE valid_until < CURDATE()
    """

    cursor.execute(update_query)

    get_db().commit()

    query = """
    SELECT Pass.*, Passenger.photo
    FROM Pass
    JOIN Passenger
    ON Pass.passenger_name = Passenger.full_name
    WHERE Pass.passenger_name=%s
    ORDER BY pass_id DESC
    LIMIT 1
    """

    cursor.execute(query, (user,))

    pass_data = cursor.fetchone()

    # Auto-regenerate QR if missing (Render ephemeral storage wipes files on deploy)
    if pass_data:
        qr_path = os.path.join(os.getcwd(), "static", "qrcodes", f"pass_{pass_data['pass_id']}.png")
        if not os.path.exists(qr_path):
            base_url = os.getenv("APP_URL", "https://busspass-pro.onrender.com")
            qr_data_str = f"{base_url}/verify/{pass_data['pass_id']}"
            import qrcode
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
            qr.add_data(qr_data_str)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#0d1117", back_color="white")
            os.makedirs(os.path.dirname(qr_path), exist_ok=True)
            img.save(qr_path)

    return render_template(
        "view_pass.html",
        pass_data=pass_data
    )

@app.route("/generate_qr/<int:pass_id>")
def generate_qr(pass_id):

    # Check if pass exists
    cursor = get_db().cursor(dictionary=True)

    query = """
    SELECT * FROM Pass
    WHERE pass_id=%s
    """

    cursor.execute(query, (pass_id,))

    pass_data = cursor.fetchone()

    if not pass_data:
        return "Pass Not Found"

    # Generate QR as a verification URL
    base_url = os.getenv("APP_URL", "https://busspass-pro.onrender.com")
    qr_data = f"{base_url}/verify/{pass_id}"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0d1117", back_color="white")

    # Absolute folder path
    folder_path = os.path.join(
        os.getcwd(),
        "static",
        "qrcodes"
    )

    os.makedirs(folder_path, exist_ok=True)

    file_path = os.path.join(
        folder_path,
        f"pass_{pass_id}.png"
    )

    img.save(file_path)

    return f"""
    QR Generated Successfully

    Saved At:
    {file_path}
    """

@app.route("/apply_pass", methods=["GET", "POST"])
def apply_pass():
    if "user" not in session:
        return redirect("/login")
    cursor = get_db().cursor(dictionary=True)

    if request.method == "POST":

        passenger_name = session["user"]

        check_query = """
        SELECT * FROM Pass_Application
        WHERE passenger_name=%s
        AND status='Pending'
        """

        cursor.execute(
            check_query,
            (passenger_name,)
        )

        existing = cursor.fetchone()

        if existing:
            return redirect("/apply_pass?msg=You+already+have+a+pending+application.&type=warning")

        active_query = """
        SELECT * FROM Pass
        WHERE passenger_name=%s
        AND status='Active'
        """

        cursor.execute(
            active_query,
            (passenger_name,)
        )

        active_pass = cursor.fetchone()

        if active_pass:
            return redirect("/apply_pass?msg=You+already+have+an+active+pass.&type=warning")

        route_id = request.form["route_id"]

        pass_type = request.form["pass_type"]

        duration_months = request.form["duration_months"]

        query = """
        INSERT INTO Pass_Application
        (passenger_name, route_id, pass_type, duration_months, status)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            passenger_name,
            route_id,
            pass_type,
            duration_months,
            "Pending"
        )

        cursor.execute(query, values)

        get_db().commit()

        return redirect("/dashboard?msg=Application+submitted+successfully!+Awaiting+admin+approval.&type=success")

    cursor.execute(
        "SELECT * FROM Route"
    )

    routes = cursor.fetchall()

    return render_template(
        "apply_pass.html",
        routes=routes
    )

@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/admin_login")

    cursor = get_db().cursor(dictionary=True)

    search = request.args.get("search")

    if search:

        query = """
        SELECT
        Pass_Application.*,
        Route.source,
        Route.destination
        FROM Pass_Application
        JOIN Route
        ON Pass_Application.route_id = Route.route_id
        WHERE passenger_name LIKE %s
        """

        cursor.execute(
            query,
            (f"%{search}%",)
        )

    else:

        query = """
        SELECT
        Pass_Application.*,
        Route.source,
        Route.destination
        FROM Pass_Application
        JOIN Route
        ON Pass_Application.route_id = Route.route_id
        """

        cursor.execute(query)

    applications = cursor.fetchall()
    cursor.execute(
    "SELECT COUNT(*) AS total FROM Pass_Application"
)

    total_apps = cursor.fetchone()["total"]

    cursor.execute(
    """
    SELECT COUNT(*) AS approved
    FROM Pass_Application
    WHERE status='Approved'
    """
)

    approved = cursor.fetchone()["approved"]

    cursor.execute(
    """
    SELECT COUNT(*) AS pending
    FROM Pass_Application
    WHERE status='Pending'
    """
)

    pending = cursor.fetchone()["pending"]

    cursor.execute(
    "SELECT COUNT(*) AS users FROM Passenger"
)

    users = cursor.fetchone()["users"]

    return render_template(
    "admin.html",
    applications=applications,
    total_apps=total_apps,
    approved=approved,
    pending=pending,
    users=users
)

@app.route("/approve/<int:id>")
def approve(id):

    cursor = get_db().cursor(dictionary=True)
    check_query = """
SELECT * FROM Pass_Application
WHERE application_id=%s
"""

    cursor.execute(
    check_query,
    (id,)
    )

    existing = cursor.fetchone()

    if existing["status"] != "Pending":
        return redirect("/admin?msg=Application+already+processed.&type=warning")

    # Update application status
    query = """
    UPDATE Pass_Application
    SET status='Approved'
    WHERE application_id=%s
    """

    cursor.execute(query, (id,))
    get_db().commit()

    # Get approved application details
    query2 = """
    SELECT * FROM Pass_Application
    WHERE application_id=%s
    """

    cursor.execute(query2, (id,))

    app_data = cursor.fetchone()

    # Insert into Pass table
    query3 = """
    INSERT INTO Pass
    (passenger_name, pass_type, valid_until, status)
    VALUES (%s, %s, DATE_ADD(CURDATE(), INTERVAL 30 DAY), %s)
    """

    values = (
        app_data["passenger_name"],
        app_data["pass_type"],
        "Active"
    )

    cursor.execute(query3, values)
    get_db().commit()

    # Get latest pass
    cursor.execute("""
    SELECT * FROM Pass
    ORDER BY pass_id DESC
    LIMIT 1
    """)

    new_pass = cursor.fetchone()

    pass_id = new_pass["pass_id"]

    # Generate QR as a verification URL — opens a beautiful page when scanned
    base_url = os.getenv("APP_URL", "https://busspass-pro.onrender.com")
    qr_data = f"{base_url}/verify/{pass_id}"

    # Create QR image
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0d1117", back_color="white")

    # Create folder if not exists
    folder_path = os.path.join(
        os.getcwd(),
        "static",
        "qrcodes"
    )

    os.makedirs(folder_path, exist_ok=True)

    # File path
    file_path = os.path.join(
        folder_path,
        f"pass_{pass_id}.png"
    )

    # Save image
    img.save(file_path)
    qr_file = f"pass_{pass_id}.png"

    update_query = """
UPDATE Pass
SET qr_code=%s
WHERE pass_id=%s
"""

    cursor.execute(
    update_query,
    (qr_file, pass_id)
)

    get_db().commit()

    return "OK"

@app.route("/reject/<int:id>")
def reject(id):

    cursor = get_db().cursor(dictionary=True)
    check_query = """
SELECT * FROM Pass_Application
WHERE application_id=%s
"""

    cursor.execute(
    check_query,
    (id,)
)

    existing = cursor.fetchone()

    if existing["status"] != "Pending":
        return redirect("/admin?msg=Application+already+processed.&type=warning")

    query = """
    UPDATE Pass_Application
    SET status='Rejected'
    WHERE application_id=%s
    """

    cursor.execute(query, (id,))

    get_db().commit()

    return "OK"

@app.route("/download_pass/<int:pass_id>")
def download_pass(pass_id):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.utils import ImageReader
    from PIL import Image as PILImage
    import io

    cursor = get_db().cursor(dictionary=True)
    cursor.execute("""
        SELECT Pass.*, Passenger.photo, Passenger.category, Passenger.phone, Passenger.email
        FROM Pass
        JOIN Passenger ON Pass.passenger_name = Passenger.full_name
        WHERE Pass.pass_id = %s
    """, (pass_id,))
    pass_data = cursor.fetchone()

    if not pass_data:
        return redirect("/view_pass?msg=Pass+not+found.&type=error")

    os.makedirs(os.path.join(os.getcwd(), "static", "pdfs"), exist_ok=True)
    pdf_file = f"static/pdfs/buspass_{pass_id}.pdf"

    # Card dimensions (credit-card aspect ratio, centered on A4)
    W, H = A4  # 595 x 842 pts
    cw, ch = 420, 245  # card width, height in pts
    cx = (W - cw) / 2   # card x origin
    cy = (H - ch) / 2   # card y origin

    c = pdf_canvas.Canvas(pdf_file, pagesize=A4)

    # ── Drop shadow ──────────────────────────────────────────────────────────
    c.saveState()
    c.setFillColorRGB(0, 0, 0, 0.15)
    c.roundRect(cx + 4, cy - 4, cw, ch, 14, fill=1, stroke=0)
    c.restoreState()

    # ── Card background (dark) ───────────────────────────────────────────────
    c.setFillColorRGB(0.07, 0.09, 0.14)
    c.roundRect(cx, cy, cw, ch, 14, fill=1, stroke=0)

    # ── Header gradient band ─────────────────────────────────────────────────
    header_h = 72
    c.setFillColorRGB(0.18, 0.38, 0.82)   # blue
    c.roundRect(cx, cy + ch - header_h, cw, header_h, 14, fill=1, stroke=0)
    # Cover bottom-left/right rounded corners of header (flat bottom)
    c.setFillColorRGB(0.18, 0.38, 0.82)
    c.rect(cx, cy + ch - header_h, cw, 14, fill=1, stroke=0)

    # ── Header text ──────────────────────────────────────────────────────────
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(cx + 16, cy + ch - 32, "BusPass Pro")
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.8, 0.88, 1)
    c.drawString(cx + 16, cy + ch - 47, "DIGITAL BUS PASS")

    # Pass ID badge (top right)
    c.setFillColorRGB(0, 0, 0, 0.25)
    c.roundRect(cx + cw - 80, cy + ch - 50, 70, 22, 6, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(cx + cw - 45, cy + ch - 40, f"#PASS {pass_id:04d}")

    # Status badge
    status = pass_data.get("status", "")
    if status == "Active":
        c.setFillColorRGB(0.06, 0.73, 0.51)
    elif status == "Expired":
        c.setFillColorRGB(0.86, 0.15, 0.15)
    else:
        c.setFillColorRGB(0.5, 0.5, 0.5)
    c.roundRect(cx + cw - 80, cy + ch - 75, 70, 20, 6, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(cx + cw - 45, cy + ch - 65, status.upper())

    # ── Passenger photo ───────────────────────────────────────────────────────
    photo_x, photo_y = cx + 16, cy + ch - header_h - 86
    photo_size = 72
    photo_path = f"static/uploads/{pass_data.get('photo', '')}"
    try:
        if os.path.exists(photo_path) and os.path.isfile(photo_path):
            c.saveState()
            # Draw blue border ring
            c.setFillColorRGB(0.18, 0.38, 0.82)
            c.circle(photo_x + photo_size/2, photo_y + photo_size/2, photo_size/2 + 2, fill=1, stroke=0)
            
            # Create a circular clipping path for the image
            path = c.beginPath()
            path.circle(photo_x + photo_size/2, photo_y + photo_size/2, photo_size/2)
            c.clipPath(path, stroke=0, fill=0)
            
            # Draw the image (it will be clipped to the circle)
            c.drawImage(photo_path, photo_x, photo_y, width=photo_size, height=photo_size)
            c.restoreState()
        else:
            raise Exception("Photo not found")
    except Exception:
        # Draw placeholder circle with initials
        c.setFillColorRGB(0.2, 0.25, 0.35)
        c.circle(photo_x + photo_size/2, photo_y + photo_size/2, photo_size/2, fill=1, stroke=0)
        c.setFillColorRGB(0.5, 0.6, 0.8)
        c.setFont("Helvetica-Bold", 24)
        initials = pass_data.get('passenger_name', '?')[0].upper()
        c.drawCentredString(photo_x + photo_size/2, photo_y + photo_size/2 - 8, initials)

    # ── Passenger name & category ─────────────────────────────────────────────
    name_x = cx + 100
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(name_x, cy + ch - header_h - 22, pass_data.get("passenger_name", ""))
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.55, 0.65, 0.85)
    c.drawString(name_x, cy + ch - header_h - 36, pass_data.get("category", "Passenger"))

    # ── Divider line ──────────────────────────────────────────────────────────
    divider_y = cy + 108
    c.setStrokeColorRGB(0.18, 0.25, 0.4)
    c.setLineWidth(0.5)
    c.line(cx + 16, divider_y, cx + cw - 16, divider_y)

    # ── Pass details grid ─────────────────────────────────────────────────────
    def draw_field(label, value, x, y):
        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0.45, 0.55, 0.75)
        c.drawString(x, y + 11, label.upper())
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(1, 1, 1)
        c.drawString(x, y, str(value))

    col1_x = cx + 16
    col2_x = cx + 155
    col3_x = cx + 285

    draw_field("Pass Type",    pass_data.get("pass_type", "—"),   col1_x, cy + 82)
    draw_field("Valid Until",  str(pass_data.get("valid_until", "—")), col2_x, cy + 82)
    draw_field("Phone",        pass_data.get("phone", "—"),        col3_x, cy + 82)

    draw_field("Email",        pass_data.get("email", "—")[:28],  col1_x, cy + 50)

    # ── QR Code ───────────────────────────────────────────────────────────────
    qr_path = f"static/qrcodes/pass_{pass_id}.png"
    if os.path.exists(qr_path):
        qr_size = 68
        qr_x = cx + cw - qr_size - 14
        qr_y = cy + 20
        # White bg for QR
        c.setFillColorRGB(1, 1, 1)
        c.roundRect(qr_x - 4, qr_y - 4, qr_size + 8, qr_size + 8, 4, fill=1, stroke=0)
        c.drawImage(qr_path, qr_x, qr_y, width=qr_size, height=qr_size)

    # ── Scan me label ─────────────────────────────────────────────────────────
    c.setFillColorRGB(0.45, 0.55, 0.75)
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(cx + cw - 14 - 34, cy + 13, "SCAN TO VERIFY")

    # ── Footer strip ─────────────────────────────────────────────────────────
    c.setFillColorRGB(0.1, 0.14, 0.22)
    c.rect(cx, cy, cw, 20, fill=1, stroke=0)
    # Round bottom corners
    c.setFillColorRGB(0.07, 0.09, 0.14)
    c.roundRect(cx, cy, cw, 20, 14, fill=1, stroke=0)
    c.setFillColorRGB(0.07, 0.09, 0.14)
    c.rect(cx, cy + 10, cw, 10, fill=1, stroke=0)
    c.setFillColorRGB(0.3, 0.4, 0.6)
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(cx + cw/2, cy + 6, "BusPass Pro  •  busspass-pro.onrender.com  •  Issued digitally")

    # ── Page watermark (faint) ────────────────────────────────────────────────
    c.saveState()
    c.setFillColorRGB(0.07, 0.09, 0.14, 0.04)
    c.setFont("Helvetica-Bold", 72)
    c.rotate(30)
    c.drawString(200, 100, "BUSPASS PRO")
    c.restoreState()

    c.save()

    # Redirect to the actual static path so the URL shows /static/pdfs/...
    # Adding a timestamp query param forces the browser to ignore cache if it was updated
    import time
    return redirect(f"/static/pdfs/buspass_{pass_id}.pdf?t={int(time.time())}")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/stats")
def stats():
    cursor = get_db().cursor(dictionary=True)
    # Total Users
    cursor.execute(
        "SELECT COUNT(*) AS total_users FROM Passenger"
    )

    total_users = cursor.fetchone()["total_users"]

    # Approved Passes
    cursor.execute("""
    SELECT COUNT(*) AS approved
    FROM Pass_Application
    WHERE status='Approved'
    """)

    approved = cursor.fetchone()["approved"]

    # Rejected Passes
    cursor.execute("""
    SELECT COUNT(*) AS rejected
    FROM Pass_Application
    WHERE status='Rejected'
    """)

    rejected = cursor.fetchone()["rejected"]

    # Pending Applications
    cursor.execute("""
    SELECT COUNT(*) AS pending
    FROM Pass_Application
    WHERE status='Pending'
    """)

    pending = cursor.fetchone()["pending"]

    return render_template(
        "stats.html",
        total_users=total_users,
        approved=approved,
        rejected=rejected,
        pending=pending
    )


@app.route("/profile")
def profile():
    if "user" not in session: return redirect("/login")

    if "user" not in session:
        return redirect("/login")

    cursor = get_db().cursor(dictionary=True)

    query = """
    SELECT *
    FROM Passenger
    WHERE full_name=%s
    """

    cursor.execute(
        query,
        (session["user"],)
    )

    data = cursor.fetchone()

    return render_template(
    "profile.html",
    data=data
)

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if "user" not in session: return redirect("/login")

    if "user" not in session:
        return redirect("/login")

    cursor = get_db().cursor(dictionary=True)

    if request.method == "POST":

        phone = request.form["phone"]
        address = request.form["address"]

        photo = request.files.get("photo")

        if photo and photo.filename:

            filename = secure_filename(photo.filename)

            photo.save(
                os.path.join(
                    "static/uploads",
                    filename
                )
            )

            query = """
            UPDATE Passenger
            SET phone=%s,
                address=%s,
                photo=%s
            WHERE full_name=%s
            """

            values = (
                phone,
                address,
                filename,
                session["user"]
            )

        else:

            query = """
            UPDATE Passenger
            SET phone=%s,
                address=%s
            WHERE full_name=%s
            """

            values = (
                phone,
                address,
                session["user"]
            )

        cursor.execute(query, values)
        get_db().commit()

        return redirect("/profile")

    query = """
    SELECT *
    FROM Passenger
    WHERE full_name=%s
    """

    cursor.execute(
        query,
        (session["user"],)
    )

    data = cursor.fetchone()

    return render_template(
        "edit_profile.html",
        data=data
    )

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "user" not in session: return redirect("/login")

    if "user" not in session:
        return redirect("/login")

    user = session["user"]

    cursor = get_db().cursor(dictionary=True)

    if request.method == "POST":

        old_password = request.form["old_password"]
        new_password = request.form["new_password"]

        query = """
        SELECT * FROM Passenger
        WHERE full_name=%s
        AND password=%s
        """

        cursor.execute(
            query,
            (user, old_password)
        )

        data = cursor.fetchone()

        if data:

            query2 = """
            UPDATE Passenger
            SET password=%s
            WHERE full_name=%s
            """

            cursor.execute(
                query2,
                (new_password, user)
            )

            get_db().commit()

            return redirect("/profile?msg=Password+updated+successfully!&type=success")

        else:

            return redirect("/change_password?msg=Old+password+is+incorrect.+Please+try+again.&type=error")

    return render_template(
        "change_password.html"
    )
@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if "user" not in session: return redirect("/login")

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        message = request.form["message"]

        cursor = get_db().cursor()

        query = """
        INSERT INTO Feedback
        (passenger_name, message)
        VALUES (%s, %s)
        """

        values = (
            session["user"],
            message
        )

        cursor.execute(query, values)

        get_db().commit()

        return redirect("/feedback?msg=Feedback+submitted!+Thank+you+for+your+response.&type=success")

    return render_template("feedback.html")

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    
    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        cursor = get_db().cursor(dictionary=True)

        query = """
        SELECT * FROM Admin
        WHERE username=%s
        AND password=%s
        """

        cursor.execute(
            query,
            (username, password)
        )

        admin = cursor.fetchone()

        if admin:

            session["admin"] = admin["username"]

            return redirect("/admin")

        else:

            return redirect("/admin_login?msg=Invalid+username+or+password.&type=error")

    return render_template(
        "admin_login.html"
    )

@app.route("/view_feedback")
def view_feedback():

    if "admin" not in session:
        return redirect("/admin_login")

    cursor = get_db().cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM Feedback"
    )

    feedbacks = cursor.fetchall()

    return render_template(
        "view_feedback.html",
        feedbacks=feedbacks
    )

@app.route("/manage_users")
def manage_users():

    if "admin" not in session:
        return redirect("/admin_login")

    cursor = get_db().cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM Passenger"
    )

    users = cursor.fetchall()

    return render_template(
        "manage_users.html",
        users=users
    )

@app.route("/delete_user/<int:id>")
def delete_user(id):

    if "admin" not in session:
        return redirect("/admin_login")

    cursor = get_db().cursor()

    query = """
    DELETE FROM Passenger
    WHERE passenger_id=%s
    """

    cursor.execute(query, (id,))

    get_db().commit()

    return redirect("/manage_users")

@app.route("/manage_routes", methods=["GET", "POST"])
def manage_routes():

    if "admin" not in session:
        return redirect("/admin_login")

    cursor = get_db().cursor(dictionary=True)

    if request.method == "POST":

        source = request.form["source"]

        destination = request.form["destination"]

        fare = request.form["fare"]

        query = """
        INSERT INTO Route
        (source, destination, fare)
        VALUES (%s, %s, %s)
        """

        cursor.execute(
            query,
            (source, destination, fare)
        )

        get_db().commit()

    cursor.execute("SELECT * FROM Route")

    routes = cursor.fetchall()

    return render_template(
        "manage_routes.html",
        routes=routes
    )


@app.route("/delete_route/<int:id>")
def delete_route(id):
    if "admin" not in session:
        return redirect("/admin_login")
    cursor = get_db().cursor()
    cursor.execute("DELETE FROM Route WHERE route_id=%s", (id,))
    get_db().commit()
    return redirect("/manage_routes?msg=Route+deleted+successfully.&type=success")

@app.route("/update_route_fare/<int:id>", methods=["POST"])
def update_route_fare(id):
    if "admin" not in session:
        return redirect("/admin_login")
    fare = request.form.get("fare")
    cursor = get_db().cursor()
    cursor.execute("UPDATE Route SET fare=%s WHERE route_id=%s", (fare, id))
    get_db().commit()
    return redirect("/manage_routes?msg=Fare+updated+successfully!&type=success")

# ── Feature 1: Forgot Password / OTP ────────────────────────────────────────
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Passenger WHERE email=%s", (email,))
        user = cursor.fetchone()
        if not user:
            return redirect("/forgot_password?msg=No+account+found+with+that+email.&type=error")

        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        expires = datetime.now() + timedelta(minutes=10)

        # Store OTP in session temporarily
        session["otp_code"]    = otp
        session["otp_email"]   = email
        session["otp_expires"] = expires.isoformat()

        # Always show OTP on screen (reliable fallback)
        # Also try to send email in background if configured
        mail_user = os.getenv("MAIL_USER", "")
        if mail_user:
            def send_async(app_ctx, message):
                with app_ctx:
                    try:
                        mail.send(message)
                    except Exception:
                        pass

            msg = Message(
                subject="BusPass Pro - Your Password Reset OTP",
                recipients=[email]
            )
            msg.html = f"""
            <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;background:#0d1117;color:#fff;border-radius:12px;padding:32px;">
              <h2 style="color:#4f8ef7;">BusPass Pro</h2>
              <h3>Password Reset Request</h3>
              <p>Your OTP is below. It expires in <strong>10 minutes</strong>.</p>
              <div style="background:#161b22;border:2px solid #4f8ef7;border-radius:10px;text-align:center;padding:24px;margin:24px 0;">
                <span style="font-size:40px;font-weight:900;letter-spacing:12px;color:#4f8ef7;">{otp}</span>
              </div>
            </div>"""
            t = threading.Thread(target=send_async, args=(app.app_context(), msg), daemon=True)
            t.start()

        # Always redirect with OTP visible on screen
        return redirect(f"/verify_otp?demo_otp={otp}&email={email}")

    return render_template("forgot_password.html")

@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered_otp   = request.form["otp"]
        new_password  = request.form["new_password"]
        stored_otp    = session.get("otp_code")
        stored_email  = session.get("otp_email")
        expires_str   = session.get("otp_expires")

        if not stored_otp or not expires_str:
            return redirect("/forgot_password?msg=Session+expired.+Please+try+again.&type=error")

        if datetime.now() > datetime.fromisoformat(expires_str):
            return redirect("/forgot_password?msg=OTP+has+expired.+Please+request+a+new+one.&type=error")

        if entered_otp != stored_otp:
            return redirect(f"/verify_otp?email={stored_email}&msg=Invalid+OTP.+Please+try+again.&type=error")

        # Update password
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE Passenger SET password=%s WHERE email=%s", (new_password, stored_email))
        db.commit()

        # Clear OTP session data
        session.pop("otp_code", None)
        session.pop("otp_email", None)
        session.pop("otp_expires", None)

        return redirect("/login?msg=Password+reset+successfully!+Please+sign+in.&type=success")

    return render_template("verify_otp.html",
                           email=request.args.get("email", ""),
                           demo_otp=request.args.get("demo_otp", ""))

# ── Resend OTP ───────────────────────────────────────────────────────────────
@app.route("/resend_otp")
def resend_otp():
    email = session.get("otp_email")
    if not email:
        return redirect("/forgot_password?msg=Session+expired.+Please+enter+your+email+again.&type=error")

    # Generate a fresh OTP
    otp = ''.join(random.choices(string.digits, k=6))
    expires = datetime.now() + timedelta(minutes=10)
    session["otp_code"]    = otp
    session["otp_expires"] = expires.isoformat()

    mail_user = os.getenv("MAIL_USER", "")
    if mail_user:
        def send_async(app_ctx, message):
            with app_ctx:
                try:
                    mail.send(message)
                except Exception:
                    pass

        msg = Message(subject="BusPass Pro - Your New OTP", recipients=[email])
        msg.html = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;background:#0d1117;color:#fff;border-radius:12px;padding:32px;">
          <h2 style="color:#4f8ef7;">BusPass Pro</h2>
          <h3>Your New OTP</h3>
          <p>Your previous OTP was resent. It expires in <strong>10 minutes</strong>.</p>
          <div style="background:#161b22;border:2px solid #4f8ef7;border-radius:10px;text-align:center;padding:24px;margin:24px 0;">
            <span style="font-size:40px;font-weight:900;letter-spacing:12px;color:#4f8ef7;">{otp}</span>
          </div>
        </div>"""
        t = threading.Thread(target=send_async, args=(app.app_context(), msg), daemon=True)
        t.start()
        return redirect(f"/verify_otp?email={email}&msg=New+OTP+sent+to+your+email!&type=success")
    else:
        # Demo mode: show OTP on screen
        return redirect(f"/verify_otp?demo_otp={otp}&email={email}&msg=New+OTP+generated!&type=success")

# ── Feature 3: Real-time Pending Count API (for admin badge) ─────────────────
@app.route("/api/pending_count")
def pending_count():
    if "admin" not in session:
        return jsonify({"count": 0})
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS cnt FROM Pass_Application WHERE status='Pending'")
    result = cursor.fetchone()
    return jsonify({"count": result["cnt"]})

# ── Feature 2: Renew Pass ────────────────────────────────────────────────────
@app.route("/renew_pass/<int:pass_id>")
def renew_pass(pass_id):
    if "user" not in session:
        return redirect("/login")
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Get old pass details
    cursor.execute("SELECT * FROM Pass WHERE pass_id=%s", (pass_id,))
    old_pass = cursor.fetchone()
    if not old_pass:
        return redirect("/view_pass?msg=Pass+not+found.&type=error")

    # Check no pending application exists
    cursor.execute("SELECT * FROM Pass_Application WHERE passenger_name=%s AND status='Pending'", (session["user"],))
    if cursor.fetchone():
        return redirect("/view_pass?msg=You+already+have+a+pending+renewal+application.&type=warning")

    # Get default route (first route)
    cursor.execute("SELECT * FROM Route LIMIT 1")
    default_route = cursor.fetchone()

    # Submit renewal application
    cursor.execute(
        "INSERT INTO Pass_Application (passenger_name, route_id, pass_type, duration_months, status) VALUES (%s, %s, %s, %s, 'Pending')",
        (session["user"], default_route["route_id"], old_pass["pass_type"], 1)
    )
    get_db().commit()
    return redirect("/dashboard?msg=Renewal+application+submitted!+Awaiting+admin+approval.&type=success")

# ── Feature 4: Activity Log ───────────────────────────────────────────────────
@app.route("/activity")
def activity():
    if "user" not in session:
        return redirect("/login")
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT 'application' AS type, status, applied_on AS event_date, route_id
        FROM Pass_Application
        WHERE passenger_name=%s
        ORDER BY applied_on DESC
    """, (session["user"],))
    events = cursor.fetchall()
    return render_template("activity.html", events=events, user=session["user"])


if __name__ == "__main__":
    app.run(debug=True)
