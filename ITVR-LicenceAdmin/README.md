# ITVR Licence Admin (local tool)

A private, local web app to generate PRO licence keys for Uptime Monitoring and
keep a record of every client you've licensed.

**Runs only on your machine.** Your private signing key (`license_private.pem`)
never leaves here — it is never put on the public website or any server.

## Run it

**Windows:** double-click **`Start-LicenceAdmin.bat`**.

**Linux / Fedora:**
```bash
chmod +x start-licence-admin.sh    # first time only
./start-licence-admin.sh
```
(Needs `python3` with venv support — on Fedora: `sudo dnf install -y python3`.)

On first run it sets up a local environment, opens `http://127.0.0.1:8750/` in
your browser, and prints an admin password in the console — save it.

To choose your own password, create a `.env` file next to `admin.py`:
```
ADMIN_PASSWORD=YourStrongPassword
```

## Use it

1. **Sign in** with the admin password.
2. **Generate a key:** enter the client/company name, pick a length
   (default 1 year), optionally add a note (payment ref, contact), click
   **Generate key**, then copy it and email it to the customer.
3. **Issued licences:** every key is logged — client, issue date, expiry, and
   status (active / expiring soon / expired). Search by client or note.
   Use this to see who's licensed and who's due to renew.

Deleting a row only removes it from your log — it does **not** revoke the key
(offline keys can't be revoked; they simply expire on their date).

## Keep safe & back up

- `license_private.pem` — the signing key. If you lose it you can't issue keys
  that validate against the shipped apps. If it leaks, anyone could mint keys.
  Back it up somewhere private and secure.
- `licences.db` — your client/licence records. Back it up too.

These are listed in `.gitignore` so they're never committed if you use git.

## How a sale works

1. Customer pays R500 (your payment method).
2. You open this tool → Generate key (1 year) for their company name.
3. Email them the key.
4. They enter it in the app under **Settings → About → Licence & Plan**.
5. Note their expiry date here so you can prompt them to renew next year.
