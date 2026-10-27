# Online Student Management System

[![Student Management CI](https://github.com/Nanmathi28/online_student_management_ci/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Nanmathi28/online_student_management_ci/actions/workflows/ci.yml)

A Flask + SQLite web application for staff/admin login and student record CRUD operations. This project demonstrates an integrated Continuous Integration (CI) pipeline using GitHub Actions.

## Features
- Admin and staff demo login
- Add, view, edit, and delete engineering student records (Name, PRN, Department)
- SQLite database with a separate temporary database for automated tests
- Automated tests for authentication, access control, CRUD, and validation
- Python syntax validation, Ruff linting, dependency vulnerability audit, and coverage enforcement
- GitHub Actions on pushes, pull requests, and manual workflow dispatch
- Test and coverage reports retained as workflow artifacts
- DEMO

## Demo credentials
- Admin: `admin` / `admin123`
- Staff: `staff` / `staff123`

These are classroom demonstration credentials only. Do not use them for a real deployment.

## Run locally (Windows PowerShell)
1. Install Python 3.11 or 3.12, Git, and VS Code.
2. Open this folder in VS Code and open Terminal.
3. Create a virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt and run `.venv\\Scripts\\activate.bat`.
4. Install dependencies:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
5. Start the web application:
   ```powershell
   python app.py
   ```
6. Open `http://127.0.0.1:5000` and log in using a demo account.

## Run quality checks locally
Run each command from the project root:

```powershell
python -m compileall -q app.py tests
ruff check .
pytest --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml --junitxml=junit.xml --cov-fail-under=80
```

The CI pipeline also runs `pip-audit -r requirements.txt` to check resolved project dependencies against known vulnerability advisories. Install `pip-audit` locally with `python -m pip install pip-audit` if you want to run that check on your laptop.

## CI pipeline stages
1. Check out repository source code.
2. Set up Python 3.11 and 3.12 using a matrix build.
3. Install dependencies with pip caching.
4. Validate Python syntax.
5. Run Ruff lint checks.
6. Audit dependencies for known vulnerabilities.
7. Run pytest and enforce at least 80% measured coverage.
8. Upload JUnit and coverage reports as workflow artifacts, even when a preceding check fails.

A failed quality check, dependency audit, test, or coverage threshold causes the job to fail and the badge to show a failing state. A successful run shows a passing state. The dependency audit requires access to the vulnerability advisory service, so a network/service issue can also make that step fail.

## Final GitHub setup
1. Push this repository to GitHub.
2. Replace `YOUR-USERNAME` in the badge URL in this README with your GitHub username.
3. Open **Actions** and inspect the `Student Management CI` workflow.
4. For a stronger team workflow, open **Settings → Rules → Rulesets** (or branch protection settings) and require the CI status checks before merging pull requests, if repository settings and permissions allow it.
5. For the practical demonstration, make a small README change, commit and push it, then show the new workflow run in Actions.

## Security note
This is an educational starter application. Before real deployment, configure a strong secret key through an environment variable, add CSRF protection and appropriate production server settings, and replace the demo authentication setup with properly managed user accounts and password-reset processes.
