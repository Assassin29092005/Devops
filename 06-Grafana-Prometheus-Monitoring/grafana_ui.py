"""Lab 06: drive the Grafana web UI (Playwright + headless Edge) and take the screenshots.

    python grafana_ui.py login <png-no>        # login page, default credentials, "Skip" the password change
    python grafana_ui.py datasource <png-no>   # Connections -> Data sources -> Add -> Prometheus -> Save & test
    python grafana_ui.py dashboard <png-no> <name>   # open the "Delivery Monitoring" dashboard (last 15 minutes)
    python grafana_ui.py alerts <png-no>       # Alerting -> Alert rules filtered to Firing, then the HighPendingDeliveries rule
GF_PASSWORD must hold the Grafana admin password (the documented default on a fresh container).
The Grafana session is kept in SCRATCH\ex6\grafana_state.json between calls.
"""
import os, sys

SCRATCH = r"C:\Users\arusw\AppData\Local\Temp\claude\D--Devops\bcbceb5a-8098-4a44-af43-3b005a03799a\scratchpad"
sys.path.insert(0, os.path.join(SCRATCH, "tools"))
from shot import launch, urlbar  # noqa: E402

GRAFANA = "http://localhost:3000"
PROM_URL = "http://host.docker.internal:9090"  # Windows/Docker Desktop instead of the exercise's 172.17.0.1
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshot")
STATE = os.path.join(SCRATCH, "ex6", "grafana_state.json")


def shot(page, name, full=False):
    png = os.path.join(OUT, name)
    page.screenshot(path=png, full_page=full)
    urlbar(png, page.url)
    print("saved", png)


def login(page, no):
    page.goto(f"{GRAFANA}/login", wait_until="load")
    page.wait_for_selector("input[name='user']")
    page.wait_for_timeout(1500)
    shot(page, f"{no:02d}-grafana-login-page.png")
    page.fill("input[name='user']", "admin")
    page.fill("input[name='password']", os.environ["GF_PASSWORD"])  # Grafana's documented default, read from env
    page.get_by_role("button", name="Log in").click()
    skip = page.get_by_role("button", name="Skip")
    skip.wait_for(timeout=20000)
    page.wait_for_timeout(1000)
    shot(page, f"{no + 1:02d}-grafana-change-password-skip.png")
    skip.click()
    page.wait_for_url(f"{GRAFANA}/", timeout=20000)
    page.wait_for_timeout(3000)
    shot(page, f"{no + 2:02d}-grafana-home-after-login.png")


def datasource(page, no):
    page.goto(f"{GRAFANA}/connections/datasources", wait_until="load")
    page.wait_for_timeout(2500)
    shot(page, f"{no:02d}-grafana-connections-data-sources.png")
    page.get_by_role("link", name="Add data source").first.click()
    page.wait_for_url("**/connections/datasources/new", timeout=20000)
    page.wait_for_timeout(2500)
    shot(page, f"{no + 1:02d}-grafana-add-data-source-prometheus.png")
    page.get_by_role("button", name="Prometheus", exact=True).first.click()
    page.wait_for_url("**/connections/datasources/edit/**", timeout=20000)
    url_box = page.locator("#connection-url")
    url_box.wait_for(timeout=20000)
    url_box.fill(PROM_URL)
    url_box.press("Tab")
    page.wait_for_timeout(1000)
    url_box.scroll_into_view_if_needed()
    page.evaluate("window.scrollBy(0, -250)")
    page.wait_for_timeout(800)
    shot(page, f"{no + 2:02d}-grafana-prometheus-url.png")
    page.get_by_role("button", name="Save & test").click()
    page.get_by_text("Successfully queried the Prometheus API").wait_for(timeout=30000)
    page.wait_for_timeout(1500)
    page.get_by_text("Successfully queried the Prometheus API").evaluate("e => e.scrollIntoView({block: 'center'})")
    page.wait_for_timeout(800)
    shot(page, f"{no + 3:02d}-grafana-save-and-test-success.png")


def retest(page, no):
    """Open the saved Prometheus data source again and re-run "Save & test" (for a clearer success screenshot)."""
    page.goto(f"{GRAFANA}/connections/datasources", wait_until="load")
    page.get_by_role("link", name="prometheus").first.click()
    page.wait_for_url("**/connections/datasources/edit/**", timeout=20000)
    page.get_by_role("button", name="Save & test").click()
    page.get_by_text("Successfully queried the Prometheus API").wait_for(timeout=30000)
    page.wait_for_timeout(1500)
    page.get_by_text("Successfully queried the Prometheus API").evaluate("e => e.scrollIntoView({block: 'center'})")
    page.wait_for_timeout(800)
    shot(page, f"{no:02d}-grafana-save-and-test-success.png")


def quiet_login(page):
    """Log in without screenshots (a Grafana container re-created by the pipeline starts with a fresh database)."""
    page.goto(f"{GRAFANA}/login", wait_until="load")
    page.fill("input[name='user']", "admin")
    page.fill("input[name='password']", os.environ["GF_PASSWORD"])
    page.get_by_role("button", name="Log in").click()
    page.get_by_role("button", name="Skip").click(timeout=20000)
    page.wait_for_url(f"{GRAFANA}/", timeout=20000)


def dashboard(page, no, name):
    url = f"{GRAFANA}/d/delivery-monitoring/delivery-monitoring?orgId=1&from=now-15m&to=now&refresh=10s"
    page.goto(url, wait_until="load")
    page.wait_for_timeout(2000)
    if "/login" in page.url:
        quiet_login(page)
        page.goto(url, wait_until="load")
    page.wait_for_timeout(8000)
    shot(page, f"{no:02d}-{name}.png")


def alerts(page, no):
    """Alerting -> Alert rules (List view, State = Firing), then the HighPendingDeliveries rule page.
    Grafana shows the Prometheus rules as data source-managed rules (read from the Prometheus rules API)."""
    page.goto(f"{GRAFANA}/alerting/list?view=list", wait_until="load")
    page.wait_for_timeout(2000)
    if "/login" in page.url:
        quiet_login(page)
        page.goto(f"{GRAFANA}/alerting/list?view=list", wait_until="load")
    page.get_by_text("HighAverageDeliveryTime").first.wait_for(timeout=30000)  # both rules loaded
    page.locator("button", has_text="Firing").first.click()  # State filter in the left column
    page.get_by_text("found 1 rule").wait_for(timeout=30000)
    page.wait_for_timeout(2000)
    shot(page, f"{no:02d}-step6-grafana-alert-rules-firing.png")
    page.get_by_text("HighPendingDeliveries", exact=True).first.click()
    page.get_by_text("Pending period").wait_for(timeout=30000)
    page.wait_for_timeout(5000)
    shot(page, f"{no + 1:02d}-step6-grafana-high-pending-rule-firing.png")


if __name__ == "__main__":
    pw, browser = launch()
    kw = {"storage_state": STATE} if os.path.exists(STATE) and sys.argv[1] != "login" else {}
    ctx = browser.new_context(viewport={"width": 1366, "height": 850}, **kw)
    page = ctx.new_page()
    try:
        cmd, no = sys.argv[1], int(sys.argv[2])
        if cmd == "dashboard":
            dashboard(page, no, sys.argv[3])
        else:
            globals()[cmd](page, no)
        ctx.storage_state(path=STATE)
    except Exception:
        page.screenshot(path=os.path.join(SCRATCH, "ex6", "failure.png"), full_page=True)
        open(os.path.join(SCRATCH, "ex6", "failure.html"), "w", encoding="utf-8").write(page.content())
        raise
    finally:
        browser.close(); pw.stop()
