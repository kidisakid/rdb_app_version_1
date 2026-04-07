# Data Pipeline

A data processing application for cleaning and transforming CSV and Excel files. Run steps in sequence from a Streamlit UI, preview results, and download the output.

## Features

- **Normalize headers** — Trim whitespace and convert column names to title case.
- **Remove duplicates** — Drop duplicate rows, optionally by selected columns.
- **Add date metadata** — Detect a date column (e.g. `date`, `date_published`) and add Year, Month, Day, and Quarter.
- **Translate columns** — Translate selected text columns to a target language (e.g. English) with optional source auto-detection and similarity grouping to reduce API calls.

Input formats: CSV, Excel (`.xlsx`, `.xls`). Output: CSV or Excel download.

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`

## Installation

From the project root:

```bash
pip install -r requirements.txt
```

## Usage

Start the Streamlit app:

```bash
python main.py
```

Or run Streamlit directly:

```bash
streamlit run app.py
```

Then:

1. Upload a CSV or Excel file.
2. In the sidebar, select one or more steps (or "Run all steps").
3. Configure options for "Remove duplicates" (columns) and "Translate columns" (columns, target/source language) if used.
4. Click **Run pipeline**, review the preview table, and use **Download CSV** or **Download Excel** to save the result.

## Project structure

```
project-root/
  main.py              # Entry point; launches Streamlit app
  app.py               # Streamlit UI and pipeline orchestration
  config.py            # Paths, encodings, delimiters
  requirements.txt
  data/
    raw/               # Default location for raw input files (CLI usage)
    output/            # Default output location (CLI usage)
  src/
    cleaning/
      normalize_headers.py
      removing_duplicates.py
    transformation/
      add_dates_metadata.py
      translate_columns.py
    utils/
      csv_handler.py   # CSV/Excel read and write helpers
```

## Configuration

Edit `config.py` to change:

- `PROJECT_ROOT`, `DATA_DIR`, `OUTPUT_DATA_DIR`, `RAW_DATA_DIR`
- `RAW_DATA_FILE` (default input for script/CLI usage)
- `CSV_ENCODINGS`, `CSV_DELIMITERS` used when reading CSV

## Authentication & password recovery

The RDB App uses MongoDB-backed authentication with bcrypt hashing and role-based access control (`user`, `admin`, `super_admin`). Key security properties:

- **Self-service password change requires the current password** and is only reachable from inside an authenticated session (Sidebar → Change Password). The public login page no longer exposes a Change Password tab.
- **Lockout:** after 5 consecutive failures, both login and change-password lock the account for 15 minutes.
- **Audit log:** every login, change, lockout, and admin reset writes a record to the `security_events` collection.
- **Minimum password policy:** 8 characters, not equal to the username.

### Forgot password (recovery flow)

1. The user contacts an admin out-of-band (chat / phone / in-person).
2. The admin opens **User Control**, clicks the key icon on the user's row, and enters a one-time temporary password that meets the policy.
3. The admin delivers the temporary password to the user out-of-band (never email it).
4. The user signs in with the temporary password. They are routed directly to the Change Password screen and cannot access any other tool until they pick a new password.
5. The new password clears the `must_change_password` flag and forces a fresh sign-in.

### Super-admin self-lockout

If a super_admin forgets their own password and no other super_admin is available to reset it, the in-app recovery path cannot help — by design, no in-app backdoor exists.

To recover, operators should:

- Keep at least **two super_admin accounts** so either can reset the other, OR
- Recover via direct MongoDB access (ops-level) by generating a new bcrypt hash in a one-off Python script and updating the target user document. Example:

  ```python
  import bcrypt
  from pymongo import MongoClient
  client = MongoClient("<mongo-uri>")
  users = client["<db_name>"]["users"]
  new_hash = bcrypt.hashpw(b"TemporaryPassword123", bcrypt.gensalt())
  users.update_one(
      {"username": "root"},
      {"$set": {"password": new_hash, "must_change_password": True}},
  )
  ```

  This script runs outside the app, against the DB directly, and sets the `must_change_password` flag so the super_admin is forced to pick a new password on next sign-in.

## License

Rythmos DB
