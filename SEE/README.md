# SEE Lab: Jenkins Freestyle Job Triggered from Git

## Objective
Configure Jenkins to fetch a shell-based storefront check script from a GitHub repository and execute it as a repeatable Freestyle build. Demonstrate that pushing an update to GitHub produces a corresponding change in the Jenkins console output on rebuild.

---

## Environment Setup
* **OS:** Windows 11 Home Single Language
* **Jenkins:** Jenkins LTS (running locally at `http://localhost:8080`)
* **Git:** Git for Windows (`git` on PATH, Git Bash shell for build step)
* **GitHub Account:** `Assassin29092005`
* **Project Repository:** https://github.com/Assassin29092005/storefront-check

---

## Repository Layout
```
SEE/
├── README.md                     # this write-up
├── Storefront-Check-config.xml   # exported Jenkins job config (config.xml)
├── storefront-check/             # local clone of the GitHub project repo
│   └── hello-world.sh            # executable script Jenkins runs
└── screenshots/                  # evidence captures
    ├── github-repo.png
    ├── jenkins-job-config.png
    ├── console-output-v1.png
    └── console-output-v2.png
```

---

## Step-by-Step Execution

### 1. Create local Git repository with executable `hello-world.sh`
```powershell
mkdir storefront-check
cd storefront-check
git init
```

`hello-world.sh`:
```bash
#!/bin/bash
echo "=== Storefront Check ==="
echo "Build Successful! Storefront services are up and running."
echo "Status: ALL CHECKS PASSED"
echo "Version: 2.0 - Updated with inventory check"
echo "Inventory Module: LOADED"
echo "Timestamp: $(date)"
```

```powershell
git add hello-world.sh
git commit -m "Add hello-world.sh with storefront check script"
```

### 2. Connect to GitHub remote and push
Created an empty repository `storefront-check` on GitHub under `Assassin29092005`, then:
```powershell
git branch -M main
git remote add origin https://github.com/Assassin29092005/storefront-check.git
git push -u origin main
```
Verified `hello-world.sh` visible at https://github.com/Assassin29092005/storefront-check — evidence in `screenshots/github-repo.png`.

### 3. Create Jenkins Freestyle project `Storefront-Check`
* **Dashboard → New Item → Freestyle project →** name: `Storefront-Check`.
* **Source Code Management → Git:**
  * Repository URL: `https://github.com/Assassin29092005/storefront-check.git`
  * Branches to build: `*/main`
* Full exported job config is in [`Storefront-Check-config.xml`](./Storefront-Check-config.xml).

### 4. Add Execute shell build step and run Build Now
Build step (`Execute shell`):
```bash
chmod +x hello-world.sh
./hello-world.sh
```
Saved the job, clicked **Build Now** → Build #1 completed with status **SUCCESS**.

### 5. Verify console output, then update, push, rebuild
Opened `Build #1 → Console Output` — showed the v1 messages (`Version: 1.0`). Evidence: `screenshots/console-output-v1.png`.

Edited `hello-world.sh` locally to add the inventory check and bump to `Version: 2.0`:
```powershell
# edit hello-world.sh locally
git add hello-world.sh
git commit -m "Update hello-world.sh with version 2.0 and inventory check"
git push origin main
```

Back in Jenkins → **Build Now** → Build #2 completed **SUCCESS**. Console Output now shows `Version: 2.0 - Updated with inventory check` and `Inventory Module: LOADED`. Evidence: `screenshots/console-output-v2.png`.

---

## Evidence

| Artifact | Screenshot |
|---|---|
| GitHub repo with `hello-world.sh` | `screenshots/github-repo.png` |
| Jenkins job SCM + build-step config | `screenshots/jenkins-job-config.png` |
| Console Output — Build #1 (v1) | `screenshots/console-output-v1.png` |
| Console Output — Build #2 (v2 after push) | `screenshots/console-output-v2.png` |

---

## Verification Summary
- **GitHub repo:** `Assassin29092005/storefront-check` — contains `hello-world.sh`.
- **Jenkins job:** `Storefront-Check` — Freestyle, Git SCM wired to the repo, `Execute shell` step runs the script.
- **Build #1:** SUCCESS — original script output.
- **Build #2:** SUCCESS — reflects the pushed update, proving Jenkins re-fetches from GitHub on each build.
