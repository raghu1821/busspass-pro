"""
Fresh screenshot script using real TiDB Cloud credentials.
Connects to local Flask server on http://127.0.0.1:5000
Uses passengers with actual data from the database.
"""
import os, time, sys
from playwright.sync_api import sync_playwright

BASE   = "http://127.0.0.1:5000"
OUTDIR = r"c:\Users\ragha\OneDrive\Documents\projects\PROJECT\BUSS_PASS_MANAGEMENT\docs\screenshots"
os.makedirs(OUTDIR, exist_ok=True)

# Best credentials from DB:
# - charu: Physically Challenged, Verified doc, Approved application (good for dashboard)
# - PC Test User: Physically Challenged, Verified doc, Active pass (good for view_pass)
# Admin: username=admin, password=admin123 (via /admin_login)

PASSENGER_EMAIL    = "charu@gmail.com"      # Has Approved application + Verified doc
PASSENGER_PASSWORD = "charu123"

PASS_USER_EMAIL    = "charu@gmail.com"  # Has Active pass
PASS_USER_PASSWORD = "charu123"

STUDENT_EMAIL      = "r123@gmail.com"       # Student with Approved app - for fare preview
STUDENT_PASSWORD   = "ragu123"

ADMIN_USER     = "admin"
ADMIN_PASSWORD = "admin123"

def ss(page, name, full=True, delay=0):
    if delay:
        time.sleep(delay)
    path = os.path.join(OUTDIR, f"{name}.png")
    page.screenshot(path=path, full_page=full)
    print(f"  [OK] {name}.png")
    return path

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(viewport={"width": 1400, "height": 900})
        page    = ctx.new_page()

        # ── 1. Login page ─────────────────────────────────────────────────────
        print("\n[1] Login page...")
        page.goto(f"{BASE}/login")
        page.wait_for_load_state("networkidle")
        ss(page, "01_login_page")

        # ── 2. Register page ──────────────────────────────────────────────────
        print("[2] Register page...")
        page.goto(f"{BASE}/register")
        page.wait_for_load_state("networkidle")
        ss(page, "02_register_page")

        # ── 3. Log in as passenger (charu - has Approved app + verified doc) ──
        print("[3] Logging in as charu (Physically Challenged, approved app)...")
        page.goto(f"{BASE}/login")
        page.wait_for_load_state("networkidle")
        try:
            page.fill('input[name="email"]',    PASSENGER_EMAIL)
            page.fill('input[name="password"]', PASSENGER_PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            print(f"   Landed on: {page.url}")
        except Exception as e:
            print(f"  ! login attempt: {e}")

        # ── 4. Passenger Dashboard ────────────────────────────────────────────
        print("[4] Passenger Dashboard...")
        page.goto(f"{BASE}/dashboard")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        ss(page, "03_passenger_dashboard")

        # ── 5. Apply Pass form ────────────────────────────────────────────────
        print("[5] Apply Pass form (using student - ragu for fare preview)...")
        page.goto(f"{BASE}/logout")
        page.wait_for_load_state("networkidle")
        page.goto(f"{BASE}/login")
        page.wait_for_load_state("networkidle")
        page.fill('input[name="email"]',    STUDENT_EMAIL)
        page.fill('input[name="password"]', STUDENT_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        page.goto(f"{BASE}/apply_pass")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        ss(page, "04_apply_pass_form")

        # ── 6. View Pass / QR page (using PC Test User with active pass) ───────
        print("[6] View Pass / QR page (PC Test User - active pass)...")
        page.goto(f"{BASE}/logout")
        page.wait_for_load_state("networkidle")
        page.goto(f"{BASE}/login")
        page.wait_for_load_state("networkidle")
        page.fill('input[name="email"]',    PASS_USER_EMAIL)
        page.fill('input[name="password"]', PASS_USER_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        page.goto(f"{BASE}/view_pass")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        ss(page, "05_view_pass_qr")

        # ── 7. Alerts page ────────────────────────────────────────────────────
        # Alerts are integrated into the Passenger Dashboard. We log in as STUDENT_EMAIL (who has no document uploaded)
        # and capture the dashboard showing the "Document Required" alert banner.
        print("[7] Alerts page (showing dashboard alert)...")
        try:
            page.goto(f"{BASE}/logout")
            page.wait_for_load_state("networkidle")
            page.goto(f"{BASE}/login")
            page.wait_for_load_state("networkidle")
            page.fill('input[name="email"]',    STUDENT_EMAIL)
            page.fill('input[name="password"]', STUDENT_PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            time.sleep(1.5)
            ss(page, "06_alerts_page")
        except Exception as e:
            print(f"  ! alerts: {e}")

        # ── 8. Feedback page ──────────────────────────────────────────────────
        print("[8] Feedback page...")
        try:
            page.goto(f"{BASE}/feedback")
            page.wait_for_load_state("networkidle")
            ss(page, "07_feedback_page")
        except Exception as e:
            print(f"  ! feedback: {e}")

        # ── 9. Pass History ───────────────────────────────────────────────────
        # In the application, travel/application history is located at /activity.
        print("[9] Pass History page (via /activity)...")
        try:
            page.goto(f"{BASE}/logout")
            page.wait_for_load_state("networkidle")
            page.goto(f"{BASE}/login")
            page.wait_for_load_state("networkidle")
            page.fill('input[name="email"]',    PASS_USER_EMAIL)
            page.fill('input[name="password"]', PASS_USER_PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            time.sleep(1.5)
            page.goto(f"{BASE}/activity")
            page.wait_for_load_state("networkidle")
            ss(page, "08_pass_history")
        except Exception as e:
            print(f"  ! history: {e}")

        # ── 10. QR Verify page ────────────────────────────────────────────────
        print("[10] QR Verify page (pass_id=480021)...")
        try:
            page.goto(f"{BASE}/verify/480021")
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            ss(page, "09_qr_verify_page")
        except Exception as e:
            print(f"  ! verify: {e}")

        # ── 11. Profile page ──────────────────────────────────────────────────
        print("[11] Profile page...")
        try:
            page.goto(f"{BASE}/login")
            page.wait_for_load_state("networkidle")
            page.fill('input[name="email"]',    PASSENGER_EMAIL)
            page.fill('input[name="password"]', PASSENGER_PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            page.goto(f"{BASE}/profile")
            page.wait_for_load_state("networkidle")
            ss(page, "10_profile_page")
        except Exception as e:
            print(f"  ! profile: {e}")

        # ── 12. Admin Login ───────────────────────────────────────────────────
        print("[12] Admin Login page...")
        page.goto(f"{BASE}/logout")
        page.wait_for_load_state("networkidle")
        page.goto(f"{BASE}/admin_login")
        page.wait_for_load_state("networkidle")
        ss(page, "11_admin_login_page")

        # ── 13. Admin login and dashboard ─────────────────────────────────────
        print("[13] Admin Dashboard...")
        try:
            page.fill('input[name="username"]', ADMIN_USER)
            page.fill('input[name="password"]', ADMIN_PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            print(f"   Landed on: {page.url}")
        except Exception as e:
            print(f"  ! admin login: {e}")

        page.goto(f"{BASE}/admin")
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        ss(page, "12_admin_dashboard")

        # ── 14. Manage Applications ───────────────────────────────────────────
        # Both admin dashboard and manage applications are on the /admin route.
        # To show application details / management, we open the passenger details modal by clicking "View".
        print("[14] Manage Applications (showing details modal on /admin)...")
        try:
            page.goto(f"{BASE}/admin")
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            # Click the first "View" button to show passenger details modal
            page.click('button:has-text("View")')
            time.sleep(1.5)
            ss(page, "13_manage_applications")
            # Close the modal or refresh to return to clean state
            page.goto(f"{BASE}/admin")
            page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"  ! manage_applications: {e}")

        # ── 15. Manage Routes ─────────────────────────────────────────────────
        print("[15] Manage Routes...")
        try:
            page.goto(f"{BASE}/manage_routes")
            page.wait_for_load_state("networkidle")
            ss(page, "14_manage_routes")
        except Exception as e:
            print(f"  ! manage_routes: {e}")

        # ── 16. Manage Users ──────────────────────────────────────────────────
        print("[16] Manage Users...")
        try:
            page.goto(f"{BASE}/manage_users")
            page.wait_for_load_state("networkidle")
            ss(page, "15_manage_users")
        except Exception as e:
            print(f"  ! manage_users: {e}")

        # ── 17. Stats / Analytics ─────────────────────────────────────────────
        print("[17] Stats / Analytics...")
        try:
            page.goto(f"{BASE}/stats")
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            ss(page, "16_stats_analytics")
        except Exception as e:
            print(f"  ! stats: {e}")

        # ── 18. Admin Feedback ────────────────────────────────────────────────
        print("[18] Admin Feedback (via /view_feedback)...")
        try:
            page.goto(f"{BASE}/view_feedback")
            page.wait_for_load_state("networkidle")
            ss(page, "17_admin_feedback")
        except Exception as e:
            print(f"  ! admin_feedback: {e}")

        browser.close()

    print(f"\nAll screenshots saved to: {OUTDIR}")
    return OUTDIR

if __name__ == "__main__":
    run()
