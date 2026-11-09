"""
ITVR Licence Admin — local tool to generate PRO licence keys and track clients.

Runs on YOUR machine only. The private signing key never leaves here.
Start it, open the browser, log in, generate keys, and keep a record of every
client you've licensed (name, issue date, expiry, status).

First run prints an admin password to the console (or set ADMIN_PASSWORD in a
.env file next to this script).
"""
import os
import sys
import json
import base64
import sqlite3
import secrets
import threading
import time
import webbrowser
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, request, jsonify, session, redirect, Response
import bcrypt
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# ── Paths ──
if getattr(sys, "frozen", False):
    BASE = os.path.dirname(sys.executable)
else:
    BASE = os.path.dirname(os.path.abspath(__file__))

DB_PATH   = os.path.join(BASE, "licences.db")
PRIV_PATH = os.path.join(BASE, "license_private.pem")

# ── Minimal .env loader ──
def _load_dotenv():
    p = os.path.join(BASE, ".env")
    if not os.path.exists(p):
        return
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except Exception:
        pass
_load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
PORT = int(os.environ.get("PORT", "8750"))

# ── DB ──
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY CHECK (id=1),
                password_hash TEXT NOT NULL
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS licences (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                client      TEXT NOT NULL,
                tier        TEXT NOT NULL DEFAULT 'pro',
                issued      TEXT NOT NULL,
                expires     TEXT,
                key         TEXT NOT NULL,
                notes       TEXT,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            )""")
        # First-run admin password
        row = conn.execute("SELECT password_hash FROM admin WHERE id=1").fetchone()
        if not row:
            pw = os.environ.get("ADMIN_PASSWORD") or secrets.token_urlsafe(12)
            ph = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
            conn.execute("INSERT INTO admin (id, password_hash) VALUES (1, ?)", (ph,))
            banner = "=" * 60
            print("\n" + banner)
            print("  ITVR Licence Admin — first-run login")
            print(banner)
            print("  Username: admin")
            if os.environ.get("ADMIN_PASSWORD"):
                print("  Password: (as set in .env)")
            else:
                print(f"  Password: {pw}")
                print("  ^ Save this. Set ADMIN_PASSWORD in .env to choose your own.")
            print(banner + "\n")

def verify_admin(password):
    with db() as conn:
        row = conn.execute("SELECT password_hash FROM admin WHERE id=1").fetchone()
    if not row:
        return False
    try:
        return bcrypt.checkpw(password.encode(), row["password_hash"].encode())
    except Exception:
        return False

# ── Auth guard ──
def login_required(f):
    @wraps(f)
    def wrap(*a, **k):
        if not session.get("admin"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Not authenticated"}), 401
            return redirect("/login")
        return f(*a, **k)
    return wrap

# ── Key signing ──
def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

def _load_private_key():
    if not os.path.exists(PRIV_PATH):
        return None
    with open(PRIV_PATH, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def generate_key(client: str, days: int):
    priv = _load_private_key()
    if priv is None:
        raise RuntimeError("license_private.pem not found next to admin.py")
    payload = {
        "name": client,
        "tier": "pro",
        "issued": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    expires = None
    if days and days > 0:
        expires = (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%d")
        payload["expires"] = expires
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    signature = priv.sign(payload_bytes)
    key = f"{_b64url(payload_bytes)}.{_b64url(signature)}"
    return key, payload["issued"], expires


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route("/login", methods=["GET"])
def login_page():
    return Response(LOGIN_HTML, mimetype="text/html")

@app.route("/api/login", methods=["POST"])
def api_login():
    d = request.get_json() or {}
    if verify_admin(d.get("password", "")):
        session["admin"] = True
        return jsonify({"ok": True})
    return jsonify({"error": "Wrong password"}), 401

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True})

@app.route("/api/change-password", methods=["POST"])
@login_required
def api_change_password():
    d = request.get_json() or {}
    current = d.get("current", "")
    new     = d.get("new", "")
    if not verify_admin(current):
        return jsonify({"error": "Current password is incorrect."}), 403
    if len(new) < 8:
        return jsonify({"error": "New password must be at least 8 characters."}), 400
    ph = bcrypt.hashpw(new.encode(), bcrypt.gensalt()).decode()
    with db() as conn:
        conn.execute("UPDATE admin SET password_hash=? WHERE id=1", (ph,))
    return jsonify({"ok": True})

@app.route("/", methods=["GET"])
@login_required
def home():
    return Response(APP_HTML, mimetype="text/html")

@app.route("/api/generate", methods=["POST"])
@login_required
def api_generate():
    d = request.get_json() or {}
    client = (d.get("client") or "").strip()
    notes  = (d.get("notes") or "").strip()
    try:
        days = int(d.get("days") or 365)
    except (ValueError, TypeError):
        days = 365
    if not client:
        return jsonify({"error": "Client name is required"}), 400
    key, issued, expires = generate_key(client, days)
    with db() as conn:
        conn.execute(
            "INSERT INTO licences (client, tier, issued, expires, key, notes) VALUES (?,?,?,?,?,?)",
            (client, "pro", issued, expires, key, notes)
        )
    return jsonify({"ok": True, "client": client, "issued": issued,
                    "expires": expires or "never", "key": key})

@app.route("/api/licences", methods=["GET"])
@login_required
def api_licences():
    q = (request.args.get("q") or "").strip().lower()
    with db() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM licences ORDER BY id DESC").fetchall()]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for r in rows:
        if r["expires"]:
            if r["expires"] < today:
                r["status"] = "expired"
            else:
                # days left
                try:
                    exp = datetime.strptime(r["expires"], "%Y-%m-%d").date()
                    r["days_left"] = (exp - datetime.now(timezone.utc).date()).days
                except Exception:
                    r["days_left"] = None
                r["status"] = "active"
        else:
            r["status"] = "active"  # never expires
    if q:
        rows = [r for r in rows if q in (r["client"] or "").lower()
                or q in (r["notes"] or "").lower()]
    return jsonify(rows)

@app.route("/api/licences/<int:lid>", methods=["DELETE"])
@login_required
def api_delete_licence(lid):
    with db() as conn:
        conn.execute("DELETE FROM licences WHERE id=?", (lid,))
    return jsonify({"ok": True})


# ─────────────────────────────────────────────
# Inline HTML (kept simple — single-file tool)
# ─────────────────────────────────────────────
STYLE = """
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,Segoe UI,Arial,sans-serif}
body{background:#0f141b;color:#e8eef2;min-height:100vh}
.top{background:#141c23;border-bottom:1px solid #263440;padding:14px 22px;display:flex;align-items:center;justify-content:space-between}
.brand{font-weight:800;font-size:16px}.brand span{color:#17c3b2}
.wrap{max-width:1000px;margin:0 auto;padding:26px 22px}
.card{background:#172028;border:1px solid #263440;border-radius:12px;padding:22px;margin-bottom:22px}
h2{font-size:16px;margin-bottom:14px}
label{display:block;font-size:12px;font-weight:700;color:#aab7c0;margin:12px 0 5px;text-transform:uppercase;letter-spacing:.04em}
input,select,textarea{width:100%;background:#0f141b;border:1px solid #2a3642;color:#e8eef2;border-radius:8px;padding:10px 12px;font-size:14px;outline:none}
input:focus,select:focus,textarea:focus{border-color:#17c3b2}
.row{display:flex;gap:14px;flex-wrap:wrap}.row>div{flex:1;min-width:180px}
.btn{background:#17c3b2;color:#06211f;border:none;border-radius:8px;padding:11px 20px;font-weight:700;font-size:14px;cursor:pointer;margin-top:14px}
.btn:hover{background:#3ee0cf}
.btn-sm{padding:5px 10px;font-size:12px;margin:0}
.btn-ghost{background:transparent;border:1px solid #2a3642;color:#aab7c0}
.keybox{margin-top:16px;background:#0f141b;border:1px solid #17c3b2;border-radius:8px;padding:14px;font-family:monospace;font-size:12px;word-break:break-all;display:none}
table{width:100%;border-collapse:collapse;margin-top:10px}
th,td{text-align:left;padding:9px 10px;font-size:13px;border-bottom:1px solid #263440}
th{color:#7a8893;font-size:11px;text-transform:uppercase;letter-spacing:.05em}
.badge{font-size:11px;font-weight:700;padding:3px 9px;border-radius:20px}
.badge.active{background:rgba(52,209,127,.16);color:#34d17f}
.badge.expired{background:rgba(242,106,106,.16);color:#f26a6a}
.badge.soon{background:rgba(240,169,59,.16);color:#f0a93b}
.muted{color:#7a8893;font-size:12px}
.keycell{font-family:monospace;font-size:11px;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.search{max-width:280px}
.msg{margin-top:10px;font-size:13px}
.login{max-width:360px;margin:12vh auto}
.copy{cursor:pointer;color:#17c3b2}
</style>
"""

LOGIN_HTML = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>ITVR Licence Admin — Login</title>{STYLE}</head>
<body><div class="login card">
  <div class="brand" style="margin-bottom:16px">ITVR <span>Licence Admin</span></div>
  <label>Password</label>
  <input id="pw" type="password" placeholder="Admin password" onkeydown="if(event.key==='Enter')doLogin()"/>
  <button class="btn" style="width:100%" onclick="doLogin()">Sign in</button>
  <div class="msg" id="msg" style="color:#f26a6a"></div>
</div>
<script>
async function doLogin(){{
  const r = await fetch('/api/login',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{password:document.getElementById('pw').value}})}});
  if(r.ok){{location.href='/';}} else {{document.getElementById('msg').textContent='Wrong password';}}
}}
</script></body></html>"""

APP_HTML = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>ITVR Licence Admin</title>{STYLE}</head>
<body>
<div class="top">
  <div class="brand">ITVR <span>Licence Admin</span></div>
  <button class="btn btn-sm btn-ghost" onclick="logout()">Sign out</button>
</div>
<div class="wrap">
  <div class="card">
    <h2>Generate a PRO licence key</h2>
    <div class="row">
      <div><label>Client / company name</label><input id="client" placeholder="e.g. Acme Ltd"/></div>
      <div><label>Licence length</label>
        <select id="days">
          <option value="365">1 year (365 days)</option>
          <option value="730">2 years (730 days)</option>
          <option value="0">Never expires</option>
          <option value="30">30 days (trial)</option>
          <option value="90">90 days (trial)</option>
        </select>
      </div>
    </div>
    <label>Notes (optional)</label>
    <input id="notes" placeholder="e.g. paid via EFT ref 12345, contact john@acme.com"/>
    <button class="btn" onclick="gen()">Generate key</button>
    <div class="keybox" id="keybox"></div>
  </div>

  <div class="card">
    <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
      <h2 style="margin:0">Issued licences</h2>
      <input class="search" id="q" placeholder="Search client or notes…" oninput="loadList()"/>
    </div>
    <div id="list"><p class="muted" style="margin-top:12px">Loading…</p></div>
  </div>

  <div class="card">
    <h2>Change admin password</h2>
    <div class="row">
      <div><label>Current password</label><input id="cpw-cur" type="password" placeholder="Current password"/></div>
      <div><label>New password</label><input id="cpw-new" type="password" placeholder="At least 8 characters"/></div>
      <div><label>Confirm new password</label><input id="cpw-new2" type="password" placeholder="Re-enter new password"/></div>
    </div>
    <button class="btn" onclick="changePw()">Update password</button>
    <div class="msg" id="cpw-msg"></div>
  </div>
</div>
<script>
async function gen(){{
  const client=document.getElementById('client').value.trim();
  const days=document.getElementById('days').value;
  const notes=document.getElementById('notes').value.trim();
  if(!client){{alert('Enter a client name');return;}}
  const r=await fetch('/api/generate',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{client,days,notes}})}});
  const d=await r.json();
  if(!r.ok){{alert(d.error||'Error');return;}}
  const box=document.getElementById('keybox');
  box.style.display='block';
  box.innerHTML='<b>'+d.client+'</b> — expires: '+d.expires+'<br><br>'+d.key+
    '<br><br><span class="copy" onclick="navigator.clipboard.writeText(this.dataset.k);this.textContent=\\'✓ copied\\'" data-k="'+d.key+'">📋 Copy key</span>';
  document.getElementById('client').value='';document.getElementById('notes').value='';
  loadList();
}}
async function loadList(){{
  const q=encodeURIComponent(document.getElementById('q').value||'');
  const r=await fetch('/api/licences?q='+q);
  const rows=await r.json();
  if(!rows.length){{document.getElementById('list').innerHTML='<p class="muted" style="margin-top:12px">No licences yet.</p>';return;}}
  let h='<table><thead><tr><th>Client</th><th>Issued</th><th>Expires</th><th>Status</th><th>Key</th><th></th></tr></thead><tbody>';
  for(const r of rows){{
    let badge='<span class="badge active">active</span>';
    if(r.status==='expired')badge='<span class="badge expired">expired</span>';
    else if(r.days_left!=null && r.days_left<=30)badge='<span class="badge soon">'+r.days_left+'d left</span>';
    h+='<tr><td><b>'+esc(r.client)+'</b>'+(r.notes?'<br><span class="muted">'+esc(r.notes)+'</span>':'')+'</td>'+
       '<td>'+r.issued+'</td><td>'+(r.expires||'never')+'</td><td>'+badge+'</td>'+
       '<td class="keycell"><span class="copy" onclick="navigator.clipboard.writeText(this.dataset.k);this.textContent=\\'✓\\'" data-k="'+r.key+'">'+r.key.slice(0,22)+'… 📋</span></td>'+
       '<td><button class="btn btn-sm btn-ghost" onclick="del('+r.id+')">Delete</button></td></tr>';
  }}
  h+='</tbody></table>';
  document.getElementById('list').innerHTML=h;
}}
function esc(s){{return (s||'').replace(/[&<>]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]));}}
async function del(id){{if(!confirm('Delete this licence record? (The key stays valid until it expires.)'))return;await fetch('/api/licences/'+id,{{method:'DELETE'}});loadList();}}
async function logout(){{await fetch('/api/logout',{{method:'POST'}});location.href='/login';}}
async function changePw(){{
  const cur=document.getElementById('cpw-cur').value;
  const nw=document.getElementById('cpw-new').value;
  const nw2=document.getElementById('cpw-new2').value;
  const msg=document.getElementById('cpw-msg');
  if(nw!==nw2){{msg.style.color='#f26a6a';msg.textContent='New passwords do not match.';return;}}
  if(nw.length<8){{msg.style.color='#f26a6a';msg.textContent='New password must be at least 8 characters.';return;}}
  const r=await fetch('/api/change-password',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{current:cur,new:nw}})}});
  const d=await r.json();
  if(r.ok){{msg.style.color='#34d17f';msg.textContent='✓ Password updated.';document.getElementById('cpw-cur').value='';document.getElementById('cpw-new').value='';document.getElementById('cpw-new2').value='';}}
  else {{msg.style.color='#f26a6a';msg.textContent=d.error||'Could not update password.';}}
}}
loadList();
</script></body></html>"""


def main():
    init_db()
    def _open():
        time.sleep(1.2)
        try: webbrowser.open(f"http://127.0.0.1:{PORT}/")
        except Exception: pass
    threading.Thread(target=_open, daemon=True).start()
    print(f"\n  ITVR Licence Admin running at http://127.0.0.1:{PORT}/")
    print("  Close this window to stop.\n")
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True, use_reloader=False)

if __name__ == "__main__":
    main()
