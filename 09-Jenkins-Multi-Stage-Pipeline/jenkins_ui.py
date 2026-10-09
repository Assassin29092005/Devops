"""Exercise 9: drive the Jenkins web UI (Playwright + headless Edge) and take the screenshots.

Reuses the logged-in Jenkins session (state.json) and the lab screenshot helper (shot.py) from the session scratch
folder. Every screenshot is taken from the real Jenkins page right after the real click.

    python jenkins_ui.py plugins                  # Step 1: Pipeline plugin is installed
    python jenkins_ui.py create                   # Step 4: New Item -> Pipeline -> OK
    python jenkins_ui.py configure                # Step 6: Pipeline script from SCM -> Git -> */main -> Save
    python jenkins_ui.py build <N> <first-png-no> # Step 7: Build Now, wait for build N, job page/console/graph
    python jenkins_ui.py graph <N> <png>          # Pipeline Overview (graph view) of build N
    python jenkins_ui.py stageview <png-no>       # install "Pipeline: Stage View" from Manage Jenkins -> Plugins
    python jenkins_ui.py stage <png-no> <name>    # screenshot the classic Stage View on the job page
"""
import os, re, sys, time

SCRATCH = r"C:\Users\arusw\AppData\Local\Temp\claude\D--Devops\bcbceb5a-8098-4a44-af43-3b005a03799a\scratchpad"
sys.path.insert(0, os.path.join(SCRATCH, "tools"))
from shot import launch, urlbar  # noqa: E402

JENKINS = "http://localhost:8080"
JOB = "Python-MultiStage-Pipeline"
REPO = "https://github.com/Assassin29092005/devops-sample-code.git"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshot")
STATE = os.path.join(SCRATCH, "jenkins", "state.json")


def shot(page, name, full=False):
    png = os.path.join(OUT, name)
    page.screenshot(path=png, full_page=full)
    urlbar(png, page.url)
    print("saved", png)


def show(page, locator, offset=110):
    """Scroll an element to the top of the viewport (below Jenkins' sticky header)."""
    locator.scroll_into_view_if_needed()
    y = locator.evaluate("e => e.getBoundingClientRect().top + window.scrollY")
    page.evaluate(f"window.scrollTo(0, {y} - {offset})")
    page.wait_for_timeout(500)


def plugins(page):
    page.goto(f"{JENKINS}/manage/pluginManager/installed", wait_until="networkidle")
    page.fill("#filter-box", "Pipeline")
    page.wait_for_timeout(1500)
    shot(page, "02-pipeline-plugin-installed.png")


def create(page):
    page.goto(f"{JENKINS}/", wait_until="networkidle")
    page.get_by_role("link", name="New Item").click()
    page.wait_for_load_state("networkidle")
    page.fill("#name", JOB)
    page.locator(".org_jenkinsci_plugins_workflow_job_WorkflowJob label").click()
    page.wait_for_timeout(500)
    shot(page, "07-new-item-pipeline.png")
    page.locator("#ok-button").click()
    page.wait_for_url(f"**/job/{JOB}/configure", timeout=30000)
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name="Save").click()
    page.wait_for_url(f"**/job/{JOB}/", timeout=30000)
    page.wait_for_load_state("networkidle")
    shot(page, "08-job-created.png")


def configure(page):
    page.set_viewport_size({"width": 1366, "height": 1050})  # room for Definition ... Branch Specifier in one view
    page.goto(f"{JENKINS}/job/{JOB}/configure", wait_until="networkidle")
    sec = page.locator(".jenkins-section__title", has_text=re.compile(r"^\s*Pipeline\s*$"))
    show(page, sec)
    shot(page, "12-configure-pipeline-default-definition.png")
    definition = page.locator("select.dropdownList").filter(has=page.locator("option", has_text="Pipeline script from SCM"))
    definition.select_option(label="Pipeline script from SCM")
    page.wait_for_timeout(1000)
    scm = page.locator("select.dropdownList").filter(has=page.locator("option", has_text=re.compile(r"^\s*Git\s*$")))
    scm.select_option(label="Git")
    page.wait_for_timeout(1500)
    url_box = page.locator("input[name='_.url']")
    url_box.fill(REPO)
    url_box.press("Tab")  # triggers the Git plugin's connection check (must stay silent for a public repo)
    page.wait_for_timeout(3000)
    branch = page.locator("input[name='_.name'][default='*/master']")
    print("default branch specifier:", branch.input_value())
    show(page, definition, offset=200)
    shot(page, "13-configure-scm-git-default-master.png")
    branch.fill("*/main")  # the repository only has 'main'
    branch.press("Tab")
    page.wait_for_timeout(800)
    script_path = page.locator("input[name='_.scriptPath']")
    print("script path:", script_path.input_value())
    show(page, branch, offset=330)
    shot(page, "14-configure-branch-main-script-path.png")
    page.get_by_role("button", name="Save").click()
    page.wait_for_url(f"**/job/{JOB}/", timeout=30000)
    page.wait_for_load_state("networkidle")
    shot(page, "15-job-page-after-save.png")


def build(page, n, first):
    page.goto(f"{JENKINS}/job/{JOB}/", wait_until="networkidle")
    page.get_by_role("link", name="Build Now").first.click()
    for _ in range(300):
        r = page.request.get(f"{JENKINS}/job/{JOB}/{n}/api/json")
        if r.ok and not r.json()["building"]:
            result = r.json()["result"]
            print(f"build #{n} result:", result)
            break
        time.sleep(1)
    else:
        raise TimeoutError(f"build #{n} did not finish in 300 s")
    tag = "failed" if result != "SUCCESS" else "success"
    page.goto(f"{JENKINS}/job/{JOB}/", wait_until="networkidle")
    page.wait_for_timeout(2000)
    shot(page, f"{first:02d}-build-{n}-{tag}-job-page.png")
    page.goto(f"{JENKINS}/job/{JOB}/{n}/console", wait_until="networkidle")
    page.wait_for_timeout(1500)
    shot(page, f"{first + 1:02d}-build-{n}-console-output.png", full=True)
    graph(page, n, f"{first + 2:02d}-build-{n}-pipeline-graph.png")
    print(page.request.get(f"{JENKINS}/job/{JOB}/{n}/consoleText").text())


def graph(page, n, png):
    """Pipeline Graph View plugin: build sidebar -> Pipeline Overview (/<n>/stages)."""
    page.goto(f"{JENKINS}/job/{JOB}/{n}/stages", wait_until="networkidle")
    page.wait_for_timeout(3000)
    shot(page, png)


def stageview(page, no):
    page.goto(f"{JENKINS}/manage/pluginManager/available", wait_until="networkidle")
    page.fill("#filter-box", "Pipeline: Stage View")
    page.wait_for_timeout(3000)
    page.locator("tr[data-plugin-id='pipeline-stage-view'] label").click()  # styled label covers the checkbox
    page.wait_for_timeout(500)
    shot(page, f"{no:02d}-plugins-available-stage-view.png")
    page.locator("#button-install").click()
    page.wait_for_load_state("networkidle")
    for _ in range(180):
        txt = page.locator("body").inner_text()
        if "Success" in txt and "Pending" not in txt and "Installing" not in txt:
            break
        time.sleep(1)
        page.reload(wait_until="networkidle")
    page.wait_for_timeout(1000)
    shot(page, f"{no + 1:02d}-stage-view-plugin-installed.png")


def stage(page, no, name):
    page.goto(f"{JENKINS}/job/{JOB}/", wait_until="networkidle")
    page.wait_for_timeout(3000)
    sv = page.locator("#pipeline-box, .cbwf-stage-view").first
    if sv.count():
        show(page, sv, offset=150)
    shot(page, f"{no:02d}-{name}.png")


if __name__ == "__main__":
    pw, browser = launch()
    ctx = browser.new_context(viewport={"width": 1366, "height": 850}, storage_state=STATE)
    page = ctx.new_page()
    try:
        me = page.request.get(f"{JENKINS}/whoAmI/api/json").json()
        assert me.get("name") == "admin", f"saved session expired ({me}); run SCRATCH\\jenkins\\login.py first"
        cmd, args = sys.argv[1], sys.argv[2:]
        if cmd == "build":
            build(page, int(args[0]), int(args[1]))
        elif cmd == "graph":
            graph(page, int(args[0]), args[1])
        elif cmd == "stageview":
            stageview(page, int(args[0]))
        elif cmd == "stage":
            stage(page, int(args[0]), args[1])
        else:
            globals()[cmd](page)
    except Exception:
        page.screenshot(path=os.path.join(SCRATCH, "ex9", "failure.png"), full_page=True)
        open(os.path.join(SCRATCH, "ex9", "failure.html"), "w", encoding="utf-8").write(page.content())
        raise
    finally:
        browser.close(); pw.stop()
