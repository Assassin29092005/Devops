# SEE Lab: Jenkins Freestyle Job Triggered from Git

## Objective
Configure Jenkins to fetch a shell-based storefront check script from a GitHub repository and execute it as a repeatable Freestyle build. Demonstrate that pushing an update to GitHub produces a corresponding change in the Jenkins console output on rebuild.

---

## Environment
* **OS:** Windows 11 Home Single Language (10.0.26200), Windows PowerShell 5.1
* **Git:** Git for Windows `2.55.0.windows.3` (`core.autocrlf=true`, `init.defaultBranch=master`)
* **GitHub Account:** `Assassin29092005` (`aru.swamy29@gmail.com`)
* **GitHub Repository:** https://github.com/Assassin29092005/storefront-check (public, branch `main`)
* **Jenkins:** `2.580.1` in Docker container `jenkins` (`jenkins/jenkins:lts`, http://localhost:8080, user `admin`), Git plugin `5.10.1`, git `2.47.3` inside the container
* **Docker:** Docker Desktop `29.9.3` on Windows

---

## Repository Layout
```
SEE/
├── README.md                        # This write-up
├── hello-world.sh                   # Copy of the final script (v2.0)
├── Storefront-Check-config.xml      # Exported Jenkins job config (config.xml)
├── build1-console-output.txt        # Full console output of Build #1
├── build2-console-output.txt        # Full console output of Build #2
└── storefront-check/                # Local Git working clone
    ├── .git/
    └── hello-world.sh               # Executable script Jenkins runs
```

---

## Step-by-Step Execution

### Step 1 — Create local Git repository with executable `hello-world.sh`

Created the project directory, initialised a Git repository on branch `main`, and wrote the shell script with LF line endings:

```powershell
New-Item -ItemType Directory -Force -Path "d:\Devops\SEE\storefront-check"
Set-Location "d:\Devops\SEE\storefront-check"
git init -b main
```

**`hello-world.sh` (v1 — initial commit):**
```bash
#!/bin/bash
echo "=== Storefront Check ==="
echo "Build Successful! Storefront services are up and running."
echo "Status: ALL CHECKS PASSED"
echo "Timestamp: $(date)"
```

Made the file executable in Git (Windows has no Unix file-mode bit) and committed:
```powershell
git add hello-world.sh
git update-index --chmod=+x hello-world.sh   # records mode 100755 in the index
git commit -m "Add hello-world.sh with storefront check script"
```

**Result:**
```
[main (root-commit) 1118cde] Add hello-world.sh with storefront check script
 1 file changed, 5 insertions(+)
 create mode 100755 hello-world.sh
```

**Verification — no "Co-Authored-By" in any commit:**
```powershell
git log --format="%B" | Select-String -Pattern "co-authored" -SimpleMatch
# (no output — none found)
```

---

### Step 2 — Connect to remote GitHub repository and push

Created a new public repository `storefront-check` under `Assassin29092005` via the GitHub REST API, then linked and pushed:

```powershell
git remote add origin https://github.com/Assassin29092005/storefront-check.git
git remote -v
git push -u origin main
```

**Result:**
```
* [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
```

**Verification — file visible on GitHub:**
* Repository: `Assassin29092005/storefront-check` (public)
* URL: https://github.com/Assassin29092005/storefront-check
* File `hello-world.sh` — 168 bytes, branch `main`
* Commit author: **Assassin29092005** `<aru.swamy29@gmail.com>`

---

### Step 3 — Create Jenkins Freestyle project `Storefront-Check`

Ensured the Jenkins container was running:
```powershell
docker start jenkins
docker ps --filter name=jenkins
# jenkins  Up ... 0.0.0.0:8080->8080/tcp, 0.0.0.0:50000->50000/tcp
```

Created the Freestyle project `Storefront-Check` via the Jenkins REST API with the following configuration:

* **Source Code Management → Git**
  * Repository URL: `https://github.com/Assassin29092005/storefront-check.git`
  * Branches to build: `*/main`
* **Build Steps → Execute shell:**
  ```bash
  chmod +x hello-world.sh
  ./hello-world.sh
  ```

The full exported job config is in [`Storefront-Check-config.xml`](./Storefront-Check-config.xml).

**Verification:**
```
Job Name: Storefront-Check | Status: blue (stable)
SCM Repo URL: https://github.com/Assassin29092005/storefront-check.git
Branch: */main
```

---

### Step 4 — Run Build Now and check result

Triggered Build #1 via the Jenkins API:

```powershell
# Equivalent to clicking Build Now in the Jenkins UI
curl -X POST http://localhost:8080/job/Storefront-Check/build
```

**Build #1 Result:** `SUCCESS` (duration: 4424 ms)

**Console Output (key lines from [`build1-console-output.txt`](./build1-console-output.txt)):**
```
Started by user admin
Running as SYSTEM
Cloning repository https://github.com/Assassin29092005/storefront-check.git
Checking out Revision 1118cde04d0d418a644aee99ebfb28abbda4d3cb (refs/remotes/origin/main)
Commit message: "Add hello-world.sh with storefront check script"
[Storefront-Check] $ /bin/sh -xe /tmp/jenkins1564676962759264976.sh
+ chmod +x hello-world.sh
+ ./hello-world.sh
=== Storefront Check ===
Build Successful! Storefront services are up and running.
Status: ALL CHECKS PASSED
Timestamp: Fri Nov 20 03:07:15 UTC 2026
Finished: SUCCESS
```

---

### Step 5 — Modify script, push, rebuild, verify updated output

Edited `hello-world.sh` to add version and inventory-module lines:

**`hello-world.sh` (v2 — updated):**
```bash
#!/bin/bash
echo "=== Storefront Check ==="
echo "Build Successful! Storefront services are up and running."
echo "Status: ALL CHECKS PASSED"
echo "Version: 2.0 - Updated with inventory check"
echo "Inventory Module: LOADED"
echo "Timestamp: $(date)"
```

Committed and pushed (no Co-Authored-By):
```powershell
git add hello-world.sh
git commit -m "Update hello-world.sh with version 2.0 and inventory check"
git push origin main
```

**Result:**
```
[main b4ed270] Update hello-world.sh with version 2.0 and inventory check
 1 file changed, 2 insertions(+)
   1118cde..b4ed270  main -> main
```

Triggered Build #2 in Jenkins → **SUCCESS** (duration: 1279 ms).

**Console Output (key lines from [`build2-console-output.txt`](./build2-console-output.txt)):**
```
Started by user admin
Running as SYSTEM
Checking out Revision b4ed270bdb1acb2ce94b45815052acf94f39e522 (refs/remotes/origin/main)
Commit message: "Update hello-world.sh with version 2.0 and inventory check"
[Storefront-Check] $ /bin/sh -xe /tmp/jenkins17832044591764358783.sh
+ chmod +x hello-world.sh
+ ./hello-world.sh
=== Storefront Check ===
Build Successful! Storefront services are up and running.
Status: ALL CHECKS PASSED
Version: 2.0 - Updated with inventory check
Inventory Module: LOADED
Timestamp: Fri Nov 20 03:10:07 UTC 2026
Finished: SUCCESS
```

The two new lines (`Version: 2.0 …` and `Inventory Module: LOADED`) confirm Jenkins re-fetched the updated script from GitHub.

---

## Verification Summary

| Check | Result |
|---|---|
| **GitHub repository** | `Assassin29092005/storefront-check`, public, branch `main` |
| **Git author (all commits)** | `Assassin29092005 <aru.swamy29@gmail.com>` |
| **Co-Authored-By in commits** | **None** — verified with `git log --format="%B" \| Select-String "co-authored"` |
| **hello-world.sh executable bit** | `100755` (confirmed via `git ls-files --stage`) |
| **Jenkins job** | Freestyle project `Storefront-Check`, Git SCM → `*/main`, Execute shell → `chmod +x hello-world.sh && ./hello-world.sh` |
| **Build #1** | `SUCCESS` — cloned commit `1118cde`, printed original storefront check output |
| **Build #2** | `SUCCESS` — fetched commit `b4ed270`, printed updated output with `Version: 2.0` and `Inventory Module: LOADED` |
| **Script change detected** | Build #2 output differs from Build #1, proving Jenkins re-fetches from GitHub on each build |

---

## Commands Used

```powershell
# Git operations
git init -b main
git add hello-world.sh
git update-index --chmod=+x hello-world.sh
git commit -m "Add hello-world.sh with storefront check script"
git remote add origin https://github.com/Assassin29092005/storefront-check.git
git push -u origin main
git commit -m "Update hello-world.sh with version 2.0 and inventory check"
git push origin main

# Docker / Jenkins
docker start jenkins
docker ps --filter name=jenkins

# Jenkins API (equivalent UI actions)
# Create job:  POST /createItem?name=Storefront-Check  (with config.xml body)
# Trigger build: POST /job/Storefront-Check/build
# View output:  GET  /job/Storefront-Check/{buildNumber}/consoleText
```

---

## Cleanup / State Left Running
* **Jenkins container `jenkins`** — still running (ports 8080 and 50000, volume `jenkins_home`). The job `Storefront-Check` and its two successful builds were kept as evidence.
* **GitHub repository** `https://github.com/Assassin29092005/storefront-check` (public, branch `main`, two commits) — kept for verification.
* **Local clone** is in `d:\Devops\SEE\storefront-check\`.
