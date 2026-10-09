"""Exercise 8: create and run the "HelloWorld" Freestyle job through the Jenkins web UI (Playwright + headless Edge).

Reuses the logged-in Jenkins session saved by exercise 7 (state.json) and the lab's screenshot helper (shot.py),
both in the session scratch folder. Every screenshot is taken from the real Jenkins page after the real click.

    python create_hello_world_job.py

One-shot: it expects that no job called HelloWorld exists yet (New Item refuses a duplicate name).
"""
import os, re, sys, time

SCRATCH = r"C:\Users\arusw\AppData\Local\Temp\claude\D--Devops\bcbceb5a-8098-4a44-af43-3b005a03799a\scratchpad"
sys.path.insert(0, os.path.join(SCRATCH, "tools"))
from shot import launch, urlbar  # noqa: E402

JENKINS = "http://localhost:8080"
JOB = "HelloWorld"
REPO = "https://github.com/Assassin29092005/devops-sample-code.git"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshot")
STATE = os.path.join(SCRATCH, "jenkins", "state.json")


def shot(page, name, full=False):
    png = os.path.join(OUT, name)
    page.screenshot(path=png, full_page=full)
    urlbar(png, page.url)
    print("saved", png)


def show(page, locator, offset=110):
    """Scroll a config section to the top of the viewport (below Jenkins' sticky header)."""
    locator.scroll_into_view_if_needed()
    y = locator.evaluate("e => e.getBoundingClientRect().top + window.scrollY")
    page.evaluate(f"window.scrollTo(0, {y} - {offset})")
    page.wait_for_timeout(400)


pw, browser = launch()
ctx = browser.new_context(viewport={"width": 1366, "height": 850}, storage_state=STATE)
page = ctx.new_page()
try:
    me = page.request.get(f"{JENKINS}/whoAmI/api/json").json()
    assert me.get("name") == "admin", f"saved session expired ({me}); run SCRATCH\\jenkins\\login.py first"

    # Step 1: access Jenkins (already logged in as admin)
    page.goto(f"{JENKINS}/", wait_until="networkidle")
    shot(page, "11-jenkins-dashboard.png")

    # Step 2: New Item -> name -> Freestyle project -> OK
    page.get_by_role("link", name="New Item").click()
    page.wait_for_load_state("networkidle")
    page.fill("#name", JOB)
    page.locator(".hudson_model_FreeStyleProject label").click()
    page.wait_for_timeout(500)
    shot(page, "12-new-item-freestyle-project.png")
    page.locator("#ok-button").click()
    page.wait_for_url(f"**/job/{JOB}/configure", timeout=30000)
    page.wait_for_load_state("networkidle")

    # Step 3a: General -> description
    page.fill("textarea[name='description']", "Hello World! Jenkins job.")
    show(page, page.locator("textarea[name='description']"), offset=260)
    shot(page, "13-configure-general-description.png")

    # Step 3b: Source Code Management -> Git, repository URL, branch */main
    scm = page.locator(".jenkins-section__title", has_text="Source Code Management")
    show(page, scm)
    page.locator("label.jenkins-radio__label", has_text=re.compile(r"^\s*Git\s*$")).click()
    page.wait_for_timeout(800)
    url_box = page.locator("input[name='_.url']")
    url_box.fill(REPO)
    url_box.press("Tab")  # triggers Jenkins' "Failed to connect..." validation, which should stay empty
    page.wait_for_timeout(2500)
    branch = page.locator("input[name='_.name'][default='*/master']")
    print("default branch specifier:", branch.input_value())
    show(page, url_box, offset=230)  # Repository URL + Branch Specifier in one view
    shot(page, "14-configure-scm-git-default-master.png")
    branch.fill("*/main")  # the repo only has 'main'; Jenkins' default '*/master' would find no revision
    branch.press("Tab")
    page.wait_for_timeout(1000)
    show(page, url_box, offset=230)
    shot(page, "15-configure-scm-branch-main.png")

    # Step 3c: Build Steps -> Add build step -> Execute shell -> "sh hello-world.sh"
    steps = page.locator(".jenkins-section__title", has_text="Build Steps")
    show(page, steps)
    page.get_by_role("button", name="Add build step").click()
    page.wait_for_timeout(500)
    page.get_by_role("button", name="Execute shell").click()
    page.wait_for_timeout(1000)
    cm = page.locator("[descriptorid='hudson.tasks.Shell'] .CodeMirror")
    if cm.count():
        cm.first.click()
        page.keyboard.type("sh hello-world.sh")
    else:
        page.locator("[descriptorid='hudson.tasks.Shell'] textarea[name='command']").fill("sh hello-world.sh")
    page.wait_for_timeout(500)
    show(page, steps)
    shot(page, "16-configure-build-step-execute-shell.png")

    # Step 4: Save -> job page
    page.get_by_role("button", name="Save").click()
    page.wait_for_url(f"**/job/{JOB}/", timeout=30000)
    page.wait_for_load_state("networkidle")
    shot(page, "17-job-page-after-save.png")

    # Build Now -> wait for build #1 to finish
    page.get_by_role("link", name="Build Now").first.click()
    for _ in range(120):
        r = page.request.get(f"{JENKINS}/job/{JOB}/1/api/json")
        if r.ok and not r.json()["building"]:
            print("build #1 result:", r.json()["result"])
            break
        time.sleep(1)
    else:
        raise TimeoutError("build #1 did not finish in 120 s")
    page.goto(f"{JENKINS}/job/{JOB}/", wait_until="networkidle")
    page.wait_for_timeout(1500)
    shot(page, "18-job-page-build-history.png")

    # Step 5: Build History -> #1 -> Console Output
    page.locator(f"a[href$='/job/{JOB}/1/']").first.click()
    page.wait_for_load_state("networkidle")
    shot(page, "19-build-1-page.png")
    page.get_by_role("link", name="Console Output").first.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    shot(page, "20-build-1-console-output.png", full=True)
    print(page.request.get(f"{JENKINS}/job/{JOB}/1/consoleText").text())
except Exception:
    page.screenshot(path=os.path.join(SCRATCH, "ex8", "failure.png"), full_page=True)
    open(os.path.join(SCRATCH, "ex8", "failure.html"), "w", encoding="utf-8").write(page.content())
    raise
finally:
    browser.close(); pw.stop()
