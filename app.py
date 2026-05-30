import mysql.connector
from flask import Flask, render_template, request, session, redirect, send_file
from werkzeug.utils import secure_filename
import qrcode
from reportlab.pdfgen import canvas
import os
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.secret_key = "buspasssecret"

# MySQL Connection
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "admin123"),
    "database": os.getenv("DB_NAME", "buspassdb"),
    "port": int(os.getenv("DB_PORT", 3306))
}

# TiDB requires specific SSL settings to connect successfully from Render
if db_config["host"] != "localhost":
    db_config["ssl_disabled"] = False
    db_config["ssl_verify_cert"] = False
    db_config["ssl_verify_identity"] = False

db = mysql.connector.connect(**db_config)

print("Database Connected Successfully")

@app.route("/")
def home():
    return render_template("index.html")

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

        cursor = db.cursor()

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
        db.commit()

        return redirect("/login?msg=Account+created+successfully!+Please+sign+in.&type=success")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cursor = db.cursor(dictionary=True)

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

    cursor = db.cursor(dictionary=True)

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

    cursor = db.cursor(dictionary=True)

    update_query = """
    UPDATE Pass
    SET status='Expired'
    WHERE valid_until < CURDATE()
    """

    cursor.execute(update_query)

    db.commit()

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

    return render_template(
        "view_pass.html",
        pass_data=pass_data
    )

@app.route("/generate_qr/<int:pass_id>")
def generate_qr(pass_id):

    # Check if pass exists
    cursor = db.cursor(dictionary=True)

    query = """
    SELECT * FROM Pass
    WHERE pass_id=%s
    """

    cursor.execute(query, (pass_id,))

    pass_data = cursor.fetchone()

    if not pass_data:
        return "Pass Not Found"

    # Create QR
    qr_data = f"""
    PASS ID: {pass_data['pass_id']}
    NAME: {pass_data['passenger_name']}
    TYPE: {pass_data['pass_type']}
    STATUS: {pass_data['status']}
    """

    img = qrcode.make(qr_data)

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
    cursor = db.cursor(dictionary=True)

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

        db.commit()

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

    cursor = db.cursor(dictionary=True)

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

    cursor = db.cursor(dictionary=True)
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
    db.commit()

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
    db.commit()

    # Get latest pass
    cursor.execute("""
    SELECT * FROM Pass
    ORDER BY pass_id DESC
    LIMIT 1
    """)

    new_pass = cursor.fetchone()

    pass_id = new_pass["pass_id"]

    # Generate QR data
    qr_data = f"""
    PASS ID: {pass_id}
    NAME: {new_pass['passenger_name']}
    TYPE: {new_pass['pass_type']}
    STATUS: {new_pass['status']}
    """

    # Create QR image
    img = qrcode.make(qr_data)

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

    db.commit()

    return "OK"

@app.route("/reject/<int:id>")
def reject(id):

    cursor = db.cursor(dictionary=True)
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

    db.commit()

    return "OK"

@app.route("/download_pass/<int:pass_id>")
def download_pass(pass_id):

    cursor = db.cursor(dictionary=True)

    query = """
    SELECT * FROM Pass
    WHERE pass_id=%s
    """

    cursor.execute(query, (pass_id,))

    pass_data = cursor.fetchone()

    if not pass_data:
        return "Pass Not Found"

    pdf_file = f"static/pdfs/buspass_{pass_id}.pdf"

    c = canvas.Canvas(pdf_file)

    c.setFont("Helvetica-Bold", 20)
    c.drawString(180, 800, "BUS PASS")

    c.setFont("Helvetica", 14)
    c.drawString(
    100,
    780,
    f"Pass ID: {pass_data['pass_id']}"
)

    c.drawString(
        100,
        740,
        f"Passenger Name: {pass_data['passenger_name']}"
    )

    c.drawString(
        100,
        700,
        f"Pass Type: {pass_data['pass_type']}"
    )

    c.drawString(
        100,
        660,
        f"Valid Until: {pass_data['valid_until']}"
    )

    c.drawString(
        100,
        620,
        f"Status: {pass_data['status']}"
    )
    

    qr_path = f"static/qrcodes/pass_{pass_id}.png"

    if os.path.exists(qr_path):

        c.drawImage(
            qr_path,
            350,
            580,
            width=150,
            height=150
        )

    c.save()

    return send_file(
    pdf_file,
    as_attachment=True
)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/stats")
def stats():
    cursor = db.cursor(dictionary=True)
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

    cursor = db.cursor(dictionary=True)

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

    cursor = db.cursor(dictionary=True)

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
        db.commit()

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

    cursor = db.cursor(dictionary=True)

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

            db.commit()

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

        cursor = db.cursor()

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

        db.commit()

        return redirect("/feedback?msg=Feedback+submitted!+Thank+you+for+your+response.&type=success")

    return render_template("feedback.html")

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    
    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        cursor = db.cursor(dictionary=True)

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

    cursor = db.cursor(dictionary=True)

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

    cursor = db.cursor(dictionary=True)

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

    cursor = db.cursor()

    query = """
    DELETE FROM Passenger
    WHERE passenger_id=%s
    """

    cursor.execute(query, (id,))

    db.commit()

    return redirect("/manage_users")

@app.route("/manage_routes", methods=["GET", "POST"])
def manage_routes():

    if "admin" not in session:
        return redirect("/admin_login")

    cursor = db.cursor(dictionary=True)

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

        db.commit()

    cursor.execute("SELECT * FROM Route")

    routes = cursor.fetchall()

    return render_template(
        "manage_routes.html",
        routes=routes
    )


if __name__ == "__main__":
    app.run(debug=True)