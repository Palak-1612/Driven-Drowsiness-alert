"""Dark-theme Live Dashboard. Run: streamlit run dashboard.py
(detector.py pehle chalu hona chahiye)"""
import json, os, time
import pandas as pd
import streamlit as st

STATUS_FILE = "status.json"
LOG_FILE = "events.csv"
LABELS = {"EYES": "Eyes closed", "YAWN": "Yawning", "NOD": "Head nodding"}
COLORS = {"EYES": "#38bdf8", "YAWN": "#f59e0b", "NOD": "#a78bfa"}
GREEN, ORANGE, RED, GRAY = "#22c55e", "#f59e0b", "#ef4444", "#64748b"

st.set_page_config(page_title="Drowsiness Dashboard", page_icon="😴", layout="wide")

CSS = """
.stApp{background:radial-gradient(circle at 15% 0%,#16213a 0%,#0a0f1c 45%,#05070d 100%);color:#e6edf3;}
header[data-testid="stHeader"]{background:transparent;}
[data-testid="stToolbar"],#MainMenu,footer{display:none !important;}
.block-container{padding-top:2rem;max-width:1200px;}
.title{font-size:2.2rem;font-weight:800;color:#f8fafc;letter-spacing:-.02em;}
.sub{color:#8b9bb4;margin:2px 0 18px 0;font-size:.95rem;}
.section{font-size:1.15rem;font-weight:700;color:#f1f5f9;margin:26px 0 4px 0;}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:14px 0;}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:14px 0;}
@media(max-width:800px){.grid4{grid-template-columns:repeat(2,1fr);}.grid2{grid-template-columns:1fr;}}
.card{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.09);border-radius:16px;padding:18px 20px;}
.label{font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;color:#8b9bb4;}
.value{font-size:2rem;font-weight:700;margin-top:6px;color:#f1f5f9;}
.banner{padding:16px 20px;border-radius:14px;font-weight:600;display:flex;align-items:center;gap:12px;font-size:1.05rem;}
.dot{width:12px;height:12px;border-radius:50%;background:currentColor;flex-shrink:0;}
.ok{background:rgba(34,197,94,.12);border:1px solid rgba(34,197,94,.4);color:#4ade80;}
.warn{background:rgba(245,158,11,.12);border:1px solid rgba(245,158,11,.4);color:#fbbf24;}
.off{background:rgba(100,116,139,.15);border:1px solid rgba(100,116,139,.4);color:#94a3b8;}
.bad{background:rgba(239,68,68,.15);border:1px solid rgba(239,68,68,.6);color:#f87171;animation:pulse 1s infinite;}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(239,68,68,.45);}50%{box-shadow:0 0 28px 6px rgba(239,68,68,.55);}}
.bar{height:12px;background:rgba(255,255,255,.08);border-radius:99px;overflow:hidden;margin-top:12px;}
.fill{height:100%;border-radius:99px;}
.pill{display:inline-block;margin-top:10px;padding:6px 14px;border-radius:99px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);color:#cbd5e1;font-size:.9rem;}
.hrow{margin:14px 0;}
.htop{display:flex;justify-content:space-between;font-size:.88rem;color:#cbd5e1;}
.row{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.06);font-size:.9rem;color:#cbd5e1;}
.badge{padding:3px 12px;border-radius:99px;font-size:.78rem;font-weight:600;}
.muted{color:#8b9bb4;font-size:.9rem;}
.stButton>button{background:rgba(255,255,255,.06);color:#e6edf3;border:1px solid rgba(255,255,255,.2);border-radius:10px;padding:6px 18px;}
.stButton>button:hover{border-color:#f87171;color:#f87171;background:rgba(239,68,68,.08);}
"""

def html(s):
    """Lines ko strip karke jodta hai, taaki markdown HTML ko code na samjhe."""
    st.markdown("".join(line.strip() for line in s.splitlines()), unsafe_allow_html=True)

html("<style>" + CSS + "</style>")
html('<div class="title">😴 Driver Drowsiness Detection</div>'
     '<div class="sub">Real-time monitoring: eyes, yawning and head position</div>')

def read_status():
    try:
        with open(STATUS_FILE) as f:
            return json.load(f)
    except Exception:
        return None

def read_events():
    try:
        df = pd.read_csv(LOG_FILE)
        return df if len(df) else None
    except Exception:
        return None

def reset_report():
    try:
        os.remove(LOG_FILE)
    except Exception:
        pass

def card(label, value, color="#f1f5f9"):
    return (f'<div class="card"><div class="label">{label}</div>'
            f'<div class="value" style="color:{color}">{value}</div></div>')

def render():
    s = read_status()
    online = bool(s) and (time.time() - s.get("updated", 0) < 3)

    # ---------- Live status ----------
    if not online:
        html('<div class="banner off"><span class="dot"></span>'
             'Detector is not running. Start it in a terminal with: python detector.py</div>')
    else:
        status, fatigue = s["status"], int(s["fatigue"])
        if status.startswith("DROWSY"):
            html(f'<div class="banner bad"><span class="dot"></span>🚨 DROWSINESS ALERT! {s["last_msg"]}</div>')
        elif status == "FACE NOT FOUND":
            html('<div class="banner warn"><span class="dot"></span>'
                 "Driver's face is not visible to the camera</div>")
        else:
            html('<div class="banner ok"><span class="dot"></span>Driver is awake and alert</div>')

        level = "HIGH" if (status.startswith("DROWSY") or fatigue >= 70) \
            else "MEDIUM" if fatigue >= 40 else "LOW"
        lvl_color = {"LOW": GREEN, "MEDIUM": ORANGE, "HIGH": RED}[level]
        fat_color = GREEN if fatigue < 40 else ORANGE if fatigue < 70 else RED
        stat_color = RED if status.startswith("DROWSY") else ORANGE if status == "FACE NOT FOUND" else GREEN

        html('<div class="grid4">'
             + card("Status", status, stat_color)
             + card("Eye ratio (EAR)", s["ear"])
             + card("Fatigue", f"{fatigue}%", fat_color)
             + card("Alert level", level, lvl_color)
             + "</div>")
        html(f'<div class="card"><div class="label">Fatigue meter (last 60 sec)</div>'
             f'<div class="bar"><div class="fill" style="width:{fatigue}%;background:{fat_color}"></div></div>'
             f'<div class="pill">{"🔊 System action: ALARM ACTIVE" if s["alarm"] else "👀 System action: Monitoring"}</div></div>')

    # ---------- Trip report ----------
    html('<div class="section">Trip report</div>')
    df = read_events()
    if df is None:
        html('<div class="card muted">No alerts yet.</div>')
    else:
        counts = df["event"].value_counts()
        total = len(df)
        html('<div class="grid4">'
             + card("Total alerts", total)
             + card("Eyes closed", int(counts.get("EYES", 0)), COLORS["EYES"])
             + card("Yawns", int(counts.get("YAWN", 0)), COLORS["YAWN"])
             + card("Head nods", int(counts.get("NOD", 0)), COLORS["NOD"])
             + "</div>")

        biggest = max(int(counts.max()), 1)
        bars = ""
        for k in ("EYES", "YAWN", "NOD"):
            n = int(counts.get(k, 0))
            bars += (f'<div class="hrow"><div class="htop"><span>{LABELS[k]}</span><span>{n}</span></div>'
                     f'<div class="bar"><div class="fill" style="width:{n / biggest * 100:.0f}%;background:{COLORS[k]}"></div></div></div>')

        score = max(0, 100 - total * 5)
        sc_color = GREEN if score >= 70 else ORANGE if score >= 40 else RED
        rows = ""
        for _, r in df.tail(5).iloc[::-1].iterrows():
            c = COLORS.get(r["event"], GRAY)
            rows += (f'<div class="row"><span>{r["time"]}</span>'
                     f'<span class="badge" style="background:{c}33;color:{c}">{LABELS.get(r["event"], r["event"])}</span></div>')

        html('<div class="grid2">'
             f'<div class="card"><div class="label">Alert type</div>{bars}</div>'
             f'<div class="card"><div class="label">Safety score</div>'
             f'<div class="value" style="color:{sc_color}">{score}/100</div>'
             f'<div class="bar"><div class="fill" style="width:{score}%;background:{sc_color}"></div></div>'
             f'<div class="label" style="margin-top:18px">Recent alerts</div>{rows}</div>'
             '</div>')

    st.button("Reset report", on_click=reset_report)

# Page har 1 second me sirf isi hisse ko refresh karta hai (flicker nahi hota)
if hasattr(st, "fragment"):
    st.fragment(run_every=1)(render)()
else:
    render()
    time.sleep(1)
    st.rerun()
