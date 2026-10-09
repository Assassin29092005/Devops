"""Lab 06: drive the Jenkins web UI (Playwright + headless Edge) and take the screenshots.

Reuses the logged-in Jenkins session (state.json from the Jenkins labs) and the lab screenshot helper (shot.py).

    python jenkins_ui.py create <png-no>             # New Item -> Pipeline -> paste delivery_monitoring/Jenkinsfile -> Save
    python jenkins_ui.py build <N> <first-png-no>    # Build Now, wait for build N, job page / console / graph view
    python jenkins_ui.py tail <N> <png-no>           # console of build N scrolled to the end
    python jenkins_ui.py stage <png-no> <name>       # classic Stage View on the job page
"""
import os, re, sys, time

SCRATCH = r"C:\Users\arusw\AppData\Local\Temp\claude\D--Devops\bcbceb5a-8098-4a44-af43-3b005a03799a\scratchpad"
sys.path.insert(0, os.path.join(SCRATCH, "tools"))
from shot import launch, urlbar  # noqa: E402

JENKINS = "http://localhost:8080"
JOB = "delivery-monitoring-pipeline"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "screenshot")
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


def create(page, no):
    script = open(os.path.join(HERE, "delivery_monitoring", "Jenkinsfile"), encoding="utf-8").read()
    page.goto(f"{JENKINS}/", wait_until="networkidle")
    page.get_by_role("link", name="New Item").click()
    page.wait_for_load_state("networkidle")
    page.fill("#name", JOB)
    page.locator(".org_jenkinsci_plugins_workflow_job_WorkflowJob label").click()
    page.wait_for_timeout(500)
    shot(page, f"{no:02d}-jenkins-new-item-pipeline.png")
    page.locator("#ok-button").click()
    page.wait_for_url(f"**/job/{JOB}/configure", timeout=30000)
    page.wait_for_load_state("networkidle")
    page.set_viewport_size({"width": 1366, "height": 1000})
    definition = page.locator("select.dropdownList").filter(has=page.locator("option", has_text="Pipeline script from SCM"))
    assert definition.input_value() is not None
    print("definition:", definition.locator("option:checked").inner_text())  # default = "Pipeline script"
    # "paste" the Jenkinsfile into the Pipeline script editor (ACE); the plugin syncs it to textarea _.script
    page.evaluate("s => { const ed = ace.edit('workflow-editor-1'); ed.setValue(s, -1); ed.clearSelection(); }", script)
    page.wait_for_timeout(800)
    assert page.locator("textarea[name='_.script']").input_value().strip() == script.strip(), "script not synced"
    show(page, page.locator(".jenkins-section__title", has_text=re.compile(r"^\s*Pipeline\s*$")))
    shot(page, f"{no + 1:02d}-jenkins-pipeline-script-pasted.png")
    page.get_by_role("button", name="Save").click()
    page.wait_for_url(f"**/job/{JOB}/", timeout=30000)
    page.wait_for_load_state("networkidle")
    page.set_viewport_size({"width": 1366, "height": 850})
    shot(page, f"{no + 2:02d}-jenkins-job-created.png")


def build(page, n, first):
    page.goto(f"{JENKINS}/job/{JOB}/", wait_until="networkidle")
    page.get_by_role("link", name="Build Now").first.click()
    for _ in range(900):
        r = page.request.get(f"{JENKINS}/job/{JOB}/{n}/api/json")
        if r.ok and not r.json()["building"]:
            result = r.json()["result"]
            print(f"build #{n} result:", result)
            break
        time.sleep(1)
    else:
        raise TimeoutError(f"build #{n} did not finish in 900 s")
    tag = "failed" if result != "SUCCESS" else "success"
    page.goto(f"{JENKINS}/job/{JOB}/{n}/console", wait_until="networkidle")
    page.wait_for_timeout(1500)
    shot(page, f"{first:02d}-build-{n}-{tag}-console-output.png", full=True)
    page.goto(f"{JENKINS}/job/{JOB}/{n}/stages", wait_until="networkidle")
    page.wait_for_timeout(3000)
    shot(page, f"{first + 1:02d}-build-{n}-pipeline-graph.png")
    text = page.request.get(f"{JENKINS}/job/{JOB}/{n}/consoleText").text()
    open(os.path.join(SCRATCH, "ex6", f"build{n}.txt"), "w", encoding="utf-8").write(text)
    print(text[-3000:])


def tail(page, n, no):
    """Console of build N scrolled to the end (the docker commands of the last stages and the result)."""
    page.set_viewport_size({"width": 1366, "height": 1100})
    page.goto(f"{JENKINS}/job/{JOB}/{n}/console", wait_until="networkidle")
    page.wait_for_timeout(1500)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(800)
    shot(page, f"{no:02d}-build-{n}-console-tail-docker-commands.png")


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
        assert me.get("name") == "admin", f"saved session expired ({me}); run SCRATCH\jenkins\login.py first"
        cmd, args = sys.argv[1], sys.argv[2:]
        if cmd == "build":
            build(page, int(args[0]), int(args[1]))
        elif cmd == "tail":
            tail(page, int(args[0]), int(args[1]))
        elif cmd == "stage":
            stage(page, int(args[0]), args[1])
        else:
            create(page, int(args[0]))
    except Exception:
        page.screenshot(path=os.path.join(SCRATCH, "ex6", "failure.png"), full_page=True)
        open(os.path.join(SCRATCH, "ex6", "failure.html"), "w", encoding="utf-8").write(page.content())
        raise
    finally:
        browser.close(); pw.stop()
