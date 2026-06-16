
import os, time
from playwright.sync_api import sync_playwright

BASE   = "http://127.0.0.1:5000"
OUTDIR = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(OUTDIR, exist_ok=True)

# ── credentials (adjust if different) ──────────────────────────────────────
PASSENGER_EMAIL    = "raghavendrakarkanaller@gmail.com"
PASSENGER_PASSWORD = "raghavendra"
ADMIN_EMAIL        = "admin@buspass.com"
ADMIN_PASSWORD     = "admin123"

def ss(page, name, full=True):
    path = os.path.join(OUTDIR, f"{name}.png")
    page.screenshot(path=path, full_page=full)
    print(f"  [OK] {name}.png")
    return path

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(viewport={"width": 1400, "height": 900})
        page    = ctx.new_page()

        # ── 1. Login page ────────────────────────────────────────────────
        page.goto(f"{BASE}/login")
        page.wait_for_load_state("networkidle")
        ss(page, "01_login_page")

        # ── 2. Register page ─────────────────────────────────────────────
        try:
            page.goto(f"{BASE}/register")
            page.wait_for_load_state("networkidle")
            ss(page, "02_register_page")
        except:
            pass

        # ── 3. Log in as passenger ────────────────────────────────────────
        page.goto(f"{BASE}/login")
        page.wait_for_load_state("networkidle")
        try:
            page.fill('input[name="email"]',    PASSENGER_EMAIL)
            page.fill('input[name="password"]', PASSENGER_PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            time.sleep(1)
        except Exception as e:
            print(f"  ! login attempt: {e}")

        # ── 4. Passenger Dashboard ────────────────────────────────────────
        page.goto(f"{BASE}/dashboard")
        page.wait_for_load_state("networkidle")
        ss(page, "03_passenger_dashboard")

        # ── 5. Apply Pass form ────────────────────────────────────────────
        try:
            page.goto(f"{BASE}/apply_pass")
            page.wait_for_load_state("networkidle")
            ss(page, "04_apply_pass_form")
        except:
            pass

        # ── 6. My Pass / View Pass ────────────────────────────────────────
        try:
            page.goto(f"{BASE}/view_pass")
            page.wait_for_load_state("networkidle")
            ss(page, "05_view_pass_qr")
        except:
            pass

        # ── 7. Alerts ─────────────────────────────────────────────────────
        try:
            page.goto(f"{BASE}/alerts")
            page.wait_for_load_state("networkidle")
            ss(page, "06_alerts_page")
        except:
            pass

        # ── 8. Feedback ───────────────────────────────────────────────────
        try:
            page.goto(f"{BASE}/feedback")
            page.wait_for_load_state("networkidle")
            ss(page, "07_feedback_page")
        except:
            pass

        # ── 9. Passenger history ──────────────────────────────────────────
        try:
            page.goto(f"{BASE}/history")
            page.wait_for_load_state("networkidle")
            ss(page, "08_pass_history")
        except:
            pass

        # ── 10. QR Verify page ────────────────────────────────────────────
        try:
            page.goto(f"{BASE}/verify_pass")
            page.wait_for_load_state("networkidle")
            ss(page, "09_qr_verify_page")
        except:
            pass

        # ── 11. Log out and log in as Admin ───────────────────────────────
        page.goto(f"{BASE}/logout")
        page.wait_for_load_state("networkidle")
        page.goto(f"{BASE}/login")
        page.wait_for_load_state("networkidle")
        try:
            page.fill('input[name="email"]',    ADMIN_EMAIL)
            page.fill('input[name="password"]', ADMIN_PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            time.sleep(1)
        except Exception as e:
            print(f"  ! admin login: {e}")

        # ── 12. Admin Dashboard ───────────────────────────────────────────
        page.goto(f"{BASE}/admin_dashboard")
        page.wait_for_load_state("networkidle")
        time.sleep(2)  # let charts render
        ss(page, "10_admin_dashboard")

        # ── 13. Manage Applications ───────────────────────────────────────
        try:
            page.goto(f"{BASE}/manage_applications")
            page.wait_for_load_state("networkidle")
            ss(page, "11_manage_applications")
        except:
            pass

        # ── 14. Manage Routes ─────────────────────────────────────────────
        try:
            page.goto(f"{BASE}/manage_routes")
            page.wait_for_load_state("networkidle")
            ss(page, "12_manage_routes")
        except:
            pass

        # ── 15. Manage Users ──────────────────────────────────────────────
        try:
            page.goto(f"{BASE}/manage_users")
            page.wait_for_load_state("networkidle")
            ss(page, "13_manage_users")
        except:
            pass

        # ── 16. Stats / Analytics ─────────────────────────────────────────
        try:
            page.goto(f"{BASE}/stats")
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            ss(page, "14_stats_analytics")
        except:
            pass

        # ── 17. Admin Feedback View ───────────────────────────────────────
        try:
            page.goto(f"{BASE}/admin_feedback")
            page.wait_for_load_state("networkidle")
            ss(page, "15_admin_feedback")
        except:
            pass

        browser.close()

    print("\nAll screenshots saved to:", OUTDIR)
    return OUTDIR

if __name__ == "__main__":
    run()
