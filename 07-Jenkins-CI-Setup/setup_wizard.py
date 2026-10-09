"""Drive the Jenkins first-run setup wizard in headless Edge and screenshot every screen.

Run:  python setup_wizard.py
The initial admin password is read at runtime from the container and is never printed.
The wizard's forms (admin user, instance configuration) live inside an iframe, so each screen
is recognised by its footer button, which is in the main page. Works from a fresh install and
also resumes a wizard that was interrupted part-way (Jenkins asks to unlock again, then resumes).
"""
import os, subprocess, sys, time

SCRATCH = r"C:\Users\arusw\AppData\Local\Temp\claude\D--Devops\bcbceb5a-8098-4a44-af43-3b005a03799a\scratchpad"
sys.path.insert(0, os.path.join(SCRATCH, "tools"))
from shot import launch, urlbar  # noqa: E402

BASE = "http://localhost:8080"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshot")


def password():
    return subprocess.run(["docker", "exec", "jenkins", "cat", "/var/jenkins_home/secrets/initialAdminPassword"],
                          capture_output=True, text=True, check=True).stdout.strip()


def snap(page, name):
    page.wait_for_timeout(1500)
    p = os.path.join(OUT, name)
    page.screenshot(path=p)
    urlbar(p, page.url)
    print("saved", name, "@", page.url, flush=True)


def button(page, name):
    b = page.get_by_role("button", name=name)
    return b.first if b.count() and b.first.is_visible() else None


def main():
    pw, browser = launch()
    page = browser.new_context(viewport={"width": 1366, "height": 850}).new_page()
    page.goto(BASE, wait_until="networkidle")
    seen, deadline = set(), time.time() + 30 * 60
    try:
        while time.time() < deadline:
            if page.locator("#security-token").is_visible():                     # Unlock Jenkins
                snap(page, "05-unlock-jenkins.png")
                page.fill("#security-token", password())
                page.get_by_role("button", name="Continue").click()
                page.wait_for_load_state("networkidle")
            elif page.get_by_text("Install suggested plugins").first.is_visible():  # Customize Jenkins
                snap(page, "06-customize-jenkins.png")
                page.get_by_text("Install suggested plugins").first.click()
                page.wait_for_timeout(20000)
                snap(page, "07-installing-suggested-plugins.png")
            elif button(page, "Retry"):                                          # plugin failures
                snap(page, "07b-plugin-install-failures.png")
                button(page, "Retry").click()
            elif button(page, "Skip and continue as admin") and "admin" not in seen:  # Create First Admin User
                seen.add("admin")
                snap(page, "08-create-first-admin-user.png")
                button(page, "Skip and continue as admin").click()
            elif button(page, "Save and Finish") and "inst" not in seen:          # Instance Configuration
                seen.add("inst")
                url = page.frame_locator("iframe").first.locator("input[name=rootUrl]").input_value()
                print("Jenkins URL field:", url, flush=True)
                snap(page, "09-instance-configuration.png")
                button(page, "Save and Finish").click()
            elif button(page, "Start using Jenkins"):                            # Jenkins is ready!
                snap(page, "10-jenkins-is-ready.png")
                button(page, "Start using Jenkins").click()
                page.wait_for_load_state("networkidle")
                page.get_by_text("Welcome to Jenkins!").first.wait_for(timeout=60000)
                snap(page, "11-jenkins-dashboard.png")
                break
            time.sleep(3)
        else:
            raise TimeoutError("setup wizard did not finish within 30 minutes")

        page.goto(BASE + "/manage/about/", wait_until="networkidle")
        snap(page, "12-about-jenkins-version.png")
        page.goto(BASE + "/manage/pluginManager/installed", wait_until="networkidle")
        snap(page, "13-installed-plugins.png")
    except Exception:
        dbg = os.path.join(SCRATCH, "ex7")
        page.screenshot(path=os.path.join(dbg, "debug.png"))
        open(os.path.join(dbg, "debug.html"), "w", encoding="utf-8").write(page.content())
        print("FAILED at", page.url, "- debug.png/debug.html saved in", dbg, flush=True)
        raise
    finally:
        browser.close(); pw.stop()


if __name__ == "__main__":
    main()
