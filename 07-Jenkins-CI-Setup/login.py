"""Log in to the local Jenkins as 'admin' in a fresh headless Edge session (screenshot 14).

python login.py [optional-screenshot.png]   -> signs in, asserts /whoAmI says admin/authenticated, saves a screenshot
The password is read at runtime from the container and never printed.
Copy of the session helper SCRATCH\\jenkins\\login.py; only the two paths below were made absolute so it runs from
this folder. The Playwright login state is written to the session scratch folder, not into this folder.
"""
import os, subprocess, sys

SCRATCH = r"C:\Users\arusw\AppData\Local\Temp\claude\D--Devops\bcbceb5a-8098-4a44-af43-3b005a03799a\scratchpad"
sys.path.insert(0, os.path.join(SCRATCH, "tools"))
from shot import launch, urlbar  # noqa: E402

pwd = subprocess.run(["docker", "exec", "jenkins", "cat", "/var/jenkins_home/secrets/initialAdminPassword"],
                     capture_output=True, text=True, check=True).stdout.strip()
pw, browser = launch()
ctx = browser.new_context(viewport={"width": 1366, "height": 850})
page = ctx.new_page()
page.goto("http://localhost:8080/login", wait_until="networkidle")
page.fill("#j_username", "admin")
page.fill("#j_password", pwd)
page.get_by_text("Keep me signed in").click()  # styled label covers the checkbox itself
assert page.is_checked("#remember_me")
page.get_by_role("button", name="Sign in").click()
page.wait_for_load_state("networkidle")
me = page.request.get("http://localhost:8080/whoAmI/api/json").json()
assert me["name"] == "admin" and me["authenticated"], f"login failed: {me}"
print("logged in as", me["name"], "- authorities:", me.get("authorities"))
page.goto("http://localhost:8080/whoAmI/", wait_until="networkidle")
if len(sys.argv) > 1:
    page.screenshot(path=sys.argv[1]); urlbar(sys.argv[1], page.url)
ctx.storage_state(path=os.path.join(SCRATCH, "jenkins", "state.json"))
browser.close(); pw.stop()
