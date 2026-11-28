from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

app = FastAPI(title="Hospital EHR/PACS & IoMT API", version="1.1.0")

TOKENS = {
    "doctor-token-123": {"user": "dr.an", "role": "doctor"},
    "nurse-token-456":  {"user": "nurse.binh", "role": "nurse"},
    "iomt-token-789":   {"user": "monitor-icu-01", "role": "iomt"},
}

PATIENTS = [
    {"id": "BN-001", "name": "Nguyen Van A", "ward": "ICU-A", "diagnosis": "Post-op monitoring"},
    {"id": "BN-002", "name": "Tran Thi B", "ward": "Cardiology-B", "diagnosis": "Arrhythmia"},
]
TELEMETRY_LOG = []


class Telemetry(BaseModel):
    device_id: str
    heart_rate: int
    spo2: int


def verify_role(authorization: Optional[str], allowed_roles: list[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Bearer token")
    token = authorization.split(" ", 1)[1].strip()
    identity = TOKENS.get(token)
    if not identity:
        raise HTTPException(status_code=401, detail="Invalid token")
    if identity["role"] not in allowed_roles:
        raise HTTPException(status_code=403, detail=f"Role '{identity['role']}' forbidden")
    return identity


@app.get("/")
def health():
    return {"service": "hospital-ehr-pacs-api", "server_ip": "192.168.200.12", "status": "ok"}


@app.get("/api/v1/ehr/patients")
def get_patients(authorization: Optional[str] = Header(default=None)):
    actor = verify_role(authorization, ["doctor"])
    return {"requested_by": actor, "patients": PATIENTS}


@app.post("/api/v1/iomt/telemetry")
def post_telemetry(payload: Telemetry, authorization: Optional[str] = Header(default=None)):
    actor = verify_role(authorization, ["iomt", "nurse", "doctor"])
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor["user"],
        **payload.model_dump(),
    }
    TELEMETRY_LOG.append(record)
    return {"status": "accepted", "total_records": len(TELEMETRY_LOG), "record": record}


@app.get("/api/v1/iomt/telemetry")
def list_telemetry(authorization: Optional[str] = Header(default=None)):
    actor = verify_role(authorization, ["doctor", "nurse"])
    return {"requested_by": actor, "records": TELEMETRY_LOG[-20:]}


HTML_UI = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hospital EHR/PACS &amp; IoMT Portal (Server 3)</title>
<style>
  body { font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 24px; }
  .wrap { max-width: 820px; margin: 0 auto; }
  h1 { margin: 0 0 6px; font-size: 22px; color: #38bdf8; }
  .sub { color: #94a3b8; margin-bottom: 20px; font-size: 13px; }
  .card { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 16px; margin-bottom: 16px; }
  label { display: block; font-size: 13px; color: #cbd5e1; margin-bottom: 6px; }
  select, input { background: #0f172a; color: #f8fafc; border: 1px solid #475569; border-radius: 6px; padding: 8px 10px; font-size: 14px; }
  select { width: 100%; }
  .row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
  .row input { flex: 1; min-width: 120px; }
  button { background: #0284c7; color: #fff; border: none; border-radius: 6px; padding: 9px 14px; cursor: pointer; font-weight: bold; }
  button:hover { background: #0369a1; }
  button.sec { background: #334155; }
  button.sec:hover { background: #475569; }
  .badge { display: inline-block; padding: 3px 10px; border-radius: 999px; font-weight: bold; font-size: 13px; }
  .s200 { background: #14532d; color: #86efac; }
  .s401 { background: #7f1d1d; color: #fca5a5; }
  .s403 { background: #78350f; color: #fcd34d; }
  pre { background: #020617; border: 1px solid #334155; border-radius: 8px; padding: 12px; overflow-x: auto; font-size: 13px; color: #a7f3d0; }
</style>
</head>
<body>
<div class="wrap">
  <h1>Hospital EHR/PACS &amp; IoMT Portal</h1>
  <div class="sub">Server 3 (192.168.200.12:8080) &mdash; Offline Zero-Trust RBAC Demo</div>

  <div class="card">
    <label for="role">Chọn danh tính (Bearer Token):</label>
    <select id="role">
      <option value="">Không có Token (Anonymous &rarr; kỳ vọng 401)</option>
      <option value="iomt-token-789">IoMT Monitor (iomt-token-789 &rarr; EHR 403 / Telemetry 200)</option>
      <option value="nurse-token-456">Y tá / Nurse (nurse-token-456 &rarr; EHR 403 / Telemetry 200)</option>
      <option value="doctor-token-123">Bác sĩ / Doctor (doctor-token-123 &rarr; Toàn quyền 200)</option>
    </select>
    <div class="row">
      <button class="sec" onclick="callApi('GET', '/')">1. Health Check (/)</button>
      <button onclick="callApi('GET', '/api/v1/ehr/patients')">2. Xem Bệnh Án EHR</button>
      <button class="sec" onclick="callApi('GET', '/api/v1/iomt/telemetry')">3. Xem Lịch Sử IoMT</button>
    </div>
  </div>

  <div class="card">
    <label>Gửi dữ liệu sinh hiệu từ Thiết bị IoMT (POST /api/v1/iomt/telemetry):</label>
    <div class="row">
      <input id="dev" value="ICU-MON-01" placeholder="Device ID">
      <input id="hr" type="number" value="78" placeholder="Heart Rate">
      <input id="spo2" type="number" value="99" placeholder="SpO2 %">
      <button onclick="sendTelemetry()">Gửi Telemetry</button>
    </div>
  </div>

  <div class="card">
    <div>Kết quả HTTP: <span id="status" class="badge s200">Chưa gọi</span></div>
    <pre id="out">Bấm một nút phía trên để kiểm thử phân quyền RBAC...</pre>
  </div>
</div>

<script>
function getHeaders() {
  const token = document.getElementById('role').value;
  const h = { 'Content-Type': 'application/json' };
  if (token) h['Authorization'] = 'Bearer ' + token;
  return h;
}
function renderResult(code, data) {
  const el = document.getElementById('status');
  el.textContent = 'HTTP ' + code;
  el.className = 'badge ' + (code === 200 ? 's200' : (code === 401 ? 's401' : 's403'));
  document.getElementById('out').textContent = JSON.stringify(data, null, 2);
}
async function callApi(method, path, body = null) {
  try {
    const opts = { method, headers: getHeaders() };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(path, opts);
    const data = await res.json();
    renderResult(res.status, data);
  } catch (err) {
    renderResult(0, { error: String(err) });
  }
}
function sendTelemetry() {
  callApi('POST', '/api/v1/iomt/telemetry', {
    device_id: document.getElementById('dev').value,
    heart_rate: Number(document.getElementById('hr').value),
    spo2: Number(document.getElementById('spo2').value)
  });
}
</script>
</body>
</html>
"""


@app.get("/ui", response_class=HTMLResponse)
def web_ui():
    return HTML_UI
