# Uptime Monitoring — Reference Guide
**How to monitor web frontends, backend APIs, and infrastructure services**

---

## 1. Monitor Types Available

### HTTP / HTTPS Monitor
Sends an HTTP GET to a URL and checks the response status code. Use for any web
page, login page, or API endpoint that returns a standard HTTP response.

**Setup:**
| Field | Value |
|-------|-------|
| Monitor Type | HTTP / HTTPS |
| URL | Full URL e.g. `https://app.example.com/login` |
| Accepted Status Codes | `200-299` (default), or add `403` if the page redirects to login |
| Interval | 60 seconds recommended |
| Retries | 3 (waits for 3 failures before marking DOWN) |

**Example:**
```
Type:  HTTP / HTTPS
URL:   https://app.example.com/login
Codes: 200-299
```

---

### HTTP Keyword Monitor
Fetches a URL and checks that a specific word/phrase appears in the body. If the
keyword is **not found**, the monitor is marked **DOWN** even on HTTP 200.

**When to use:** `/health` or `/status` endpoints that return JSON, where a 200
doesn't guarantee health.

**Example — API health check:**
```
Type:    HTTP Keyword
URL:     https://api.example.com/health
Keyword: "status":"ok"
```

**Tip:** Keep the keyword short and unique — use part of a JSON pair
(`"status":"ok"`) rather than just `ok` to avoid false positives.

---

### TCP Port Monitor
Checks whether a port is open and accepting connections. No HTTP request — just
verifies reachability. Use for databases, message queues, and non-HTTP services.

**Example — PostgreSQL:**
```
Type: TCP Port
Host: db-server.example.com:5432
```

---

## 2. Monitoring Backend APIs — Step by Step

1. **Identify what the API exposes** — a `/health`, `/status`, `/actuator/health`
   endpoint? JSON with a status field? Which port?
2. **Choose the monitor type:**
   ```
   Has a /health endpoint returning JSON  →  HTTP Keyword
   Returns HTTP 200 when running          →  HTTP / HTTPS
   Database or non-HTTP service           →  TCP Port
   Behind a gateway                       →  Monitor the gateway endpoint
   ```
3. **Add the monitor** — dashboard → **+ Add Monitor**, fill in type, friendly
   name, URL/host, application group, keyword (if applicable), interval, retries.
4. **Add to a status page** (optional) — **Status Pages → Edit → tick the monitor → Save**.

---

## 3. Common Backend Services — Quick Reference

| Service | Monitor Type | Typical Port | Notes |
|---------|--------------|--------------|-------|
| REST API with `/health` | HTTP Keyword | 443 / 8080 | Keyword: `"status":"ok"` |
| REST API, no health endpoint | HTTP / HTTPS | 443 / 8080 | Any endpoint returning 200 |
| SOAP / WS endpoint | HTTP / HTTPS | 443 / 8080 | Monitor the WSDL URL |
| PostgreSQL | TCP Port | 5432 | |
| Oracle DB | TCP Port | 1521 | |
| SQL Server | TCP Port | 1433 | |
| IBM MQ | TCP Port | 1414 | |
| RabbitMQ | TCP Port | 5672 | 15672 for management UI |
| Kafka | TCP Port | 9092 | |
| Redis | TCP Port | 6379 | |
| Spring Boot | HTTP Keyword | 8080 | `/actuator/health` · Keyword: `"status":"UP"` |
| Node.js | HTTP Keyword | 3000 | `/health` · Keyword: `ok` |
| .NET Core | HTTP Keyword | 5000 | `/health` · Keyword: `Healthy` |

---

## 4. Recommended Health Endpoint Standard

If your team owns the service, add a `/health` endpoint returning:

```json
{ "status": "ok", "service": "your-service-name", "version": "1.0.0" }
```

Then monitor it with HTTP Keyword and keyword `"status":"ok"`. This distinguishes
"port is open" from "service is actually healthy".

---

## 5. Monitor Settings Reference

| Setting | Description | Recommended |
|---------|-------------|-------------|
| Interval | How often the check runs | 60 seconds |
| Retries | Consecutive failures before DOWN | 3 |
| Timeout | How long to wait for a response | 10 seconds |
| Accepted Status Codes | HTTP codes considered healthy | `200-299` |
| Application Group | Groups monitors on the dashboard | Your app name |
| Tags | Optional labels for filtering | e.g. `production, api` |
| Email Alert | Email on status change | Enable for critical services |

---

## 6. Accessing the Application

| URL | Purpose |
|-----|---------|
| `http://localhost:5000` | Main dashboard |
| `http://localhost:5000/?page=default` | Default status page (shareable) |

Behind a reverse proxy, use your own HTTPS URL instead of `localhost:5000`.

**Start:** run `start.bat` (Windows) or `python app.py`. **Stop:** `Ctrl+C`.
