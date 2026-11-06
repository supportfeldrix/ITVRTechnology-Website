/* ============================================================
   ITVR Technology — shared site script
   ============================================================ */

/* ────────────────────────────────────────────────────────────
   DOWNLOAD LINK for Uptime Monitoring. Point this at your hosted
   zip or a GitHub release asset when ready. Path is relative to
   the product page (products/uptime.html).
   Leave "" to show a "contact us" message instead.
   ──────────────────────────────────────────────────────────── */
const DOWNLOAD_URL = "../assets/UptimeMonitor-Windows-v1.0.zip";

function startDownload() {
  if (DOWNLOAD_URL) {
    const a = document.createElement('a');
    a.href = DOWNLOAD_URL;
    a.download = DOWNLOAD_URL.split('/').pop() || 'UptimeMonitor.zip';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  } else {
    alert("Download coming soon. Contact info@itvrtechnology.co.za to get the package.");
  }
  return false;
}

/* ── Theme toggle (shared across pages) ── */
function currentTheme() {
  try { return localStorage.getItem('itvr-theme') || 'light'; } catch(e) { return 'light'; }
}
function applyTheme(theme) {
  const dark = theme === 'dark';
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
  try { localStorage.setItem('itvr-theme', dark ? 'dark' : 'light'); } catch(e) {}
  document.querySelectorAll('.theme-btn').forEach(b => b.textContent = dark ? '☀️' : '🌙');
}
function toggleTheme() {
  applyTheme(currentTheme() === 'dark' ? 'light' : 'dark');
}

/* ── OS tabs (product page) ── */
function showTab(tab) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.dataset.tab === tab));
}

/* ── Init ── */
(function () {
  applyTheme(currentTheme());
  document.querySelectorAll('[data-year]').forEach(el => el.textContent = new Date().getFullYear());
})();
