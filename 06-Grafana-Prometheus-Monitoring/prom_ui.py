"""Lab 06: screenshots of the Prometheus 3 web UI (Playwright + headless Edge).

    python prom_ui.py <first-png-no> <page> [<page> ...]
pages: home | targets | alerts | config | query:<name>:<promql>
"""
import os, sys, urllib.parse

SCRATCH = r"C:\Users\arusw\AppData\Local\Temp\claude\D--Devops\bcbceb5a-8098-4a44-af43-3b005a03799a\scratchpad"
sys.path.insert(0, os.path.join(SCRATCH, "tools"))
from shot import launch, urlbar  # noqa: E402

PROM = "http://localhost:9090"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshot")


def shot(page, name, full=False):
    png = os.path.join(OUT, name)
    page.screenshot(path=png, full_page=full)
    urlbar(png, page.url)
    print("saved", png)


def run(page, no, spec):
    if spec == "home":
        page.goto(PROM + "/", wait_until="load")
        name = "prometheus-home"
    elif spec == "targets":
        page.goto(PROM + "/targets", wait_until="load")
        name = "prometheus-targets-up"
    elif spec == "alerts":
        page.goto(PROM + "/alerts", wait_until="load")
        page.wait_for_timeout(1500)
        for rule in page.get_by_text("HighPendingDeliveries").all() + page.get_by_text("HighAverageDeliveryTime").all():
            try:  # expand each rule so its active alerts (labels, state, value) are visible
                rule.click(timeout=2000); page.wait_for_timeout(500)
            except Exception:
                pass
        name = "prometheus-alerts"
    elif spec == "config":
        page.goto(PROM + "/config", wait_until="load")
        name = "prometheus-runtime-config"
    else:  # query:<name>:<promql>
        _, name, expr = spec.split(":", 2)
        q = urllib.parse.urlencode({"g0.expr": expr, "g0.tab": "graph", "g0.range_input": "15m"})
        page.goto(f"{PROM}/query?{q}", wait_until="load")
    page.wait_for_timeout(2500)
    shot(page, f"{no:02d}-{name}.png", full=spec in ("alerts",))


if __name__ == "__main__":
    pw, browser = launch()
    page = browser.new_context(viewport={"width": 1366, "height": 850}).new_page()
    try:
        no = int(sys.argv[1])
        for i, spec in enumerate(sys.argv[2:]):
            run(page, no + i, spec)
    finally:
        browser.close(); pw.stop()
