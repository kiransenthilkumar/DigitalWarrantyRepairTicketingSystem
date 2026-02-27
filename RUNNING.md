# How to Run the Project (Quick)

This file contains the exact steps to set up and run the project locally (Windows PowerShell and POSIX shells). Follow the section for your OS.

## Prerequisites
- Python 3.8+
- pip

---

## Windows (PowerShell)

1. Create & activate virtual environment
```powershell
python -m venv venv
.\venv\Scripts\Activate
```

2. Install dependencies
```powershell
pip install -r requirements.txt
```

3. Ensure `instance/` directory exists (required for SQLite DB file)
```powershell
mkdir .\instance
```

4. Create `.env` if missing
```powershell
copy .env.example .env
# Edit .env to set SECRET_KEY or DATABASE_URL if needed
```

5. (Optional) Initialize the database manually

   The application will try to create the tables and a default admin user
   when it starts, but if you prefer to run the initialization beforehand
   (or if the server raised an error), execute the following:
   ```powershell
   python - <<'PY'
   from app import create_app
   from extensions import db
   app = create_app()
   with app.app_context():
       db.create_all()
   print("DB initialized")
   PY
   ```
   If the automatic step fails, the server will still start and print a
   warning; this manual command is useful for debugging.

6. (Optional) Load seed/demo data
```powershell
python seed_data.py
```

7. Start the development server
You can simply run the application file; a reloader is disabled so it
won't crash during restarts.
```powershell
python app.py
```
Alternatively you may use the flask CLI if you wish:
```powershell
$env:FLASK_APP="app"
$env:FLASK_ENV="development"
flask run --host=0.0.0.0
```

Open: http://localhost:5000

Default demo/admin credentials:
- Email: admin@example.com
- Password: admin123

---

## macOS / Linux / WSL (POSIX shell)

1. Create & activate virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Ensure `instance/` directory exists
```bash
mkdir -p instance
```

4. Create `.env` if missing
```bash
cp .env.example .env
# Edit .env to set SECRET_KEY or DATABASE_URL if needed
```

5. Initialize the database
```bash
python - <<'PY'
from app import create_app
from extensions import db
app = create_app()
with app.app_context():
    db.create_all()
print("DB initialized")
PY
```

6. (Optional) Load seed/demo data
```bash
python seed_data.py
```

7. Start the development server
```bash
python app.py
# or
export FLASK_APP=app
export FLASK_ENV=development
flask run --host=0.0.0.0
```

Open: http://localhost:5000

---

## Troubleshooting: `sqlite3.OperationalError: unable to open database file`

- Ensure you ran `mkdir instance` from the project root so the folder exists and is writable.
- Confirm your `.env` or `config.py` points to a valid SQLite path, e.g. `sqlite:///instance/warranty_system.db`.
- Run the small Python block in step 5 from the project root to get clearer error output.
- Check file permissions and that the process can create files in the `instance/` directory.

Quick permission check (Windows PowerShell):
```powershell
icacls .\instance /grant "%USERNAME%:(OI)(CI)F"
```

Quick path test (makes file writable):
```powershell
python - <<'PY'
import os
p = os.path.join(os.getcwd(), 'instance', 'warranty_system.db')
print('expected path:', p)
print('parent exists:', os.path.exists(os.path.dirname(p)))
try:
    open(p, 'a').close()
    print('file writable or created')
except Exception as e:
    print('error creating file:', e)
PY
```

---

If you'd like, I can add these steps into `README.md` instead or run the DB initialization for you now. If you want the file name or location changed, tell me which. 