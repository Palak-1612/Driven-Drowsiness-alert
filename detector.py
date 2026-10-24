"""Driver Drowsiness Alert v4
Eyes + Yawn + Head nod | Beep + English voice | Fatigue meter | Live status for dashboard
Run: python detector.py   |  Quit: press q
"""
import cv2, time, csv, os, json, threading
from collections import deque
import numpy as np
import mediapipe as mp
import pyttsx3

# ---------- Settings (demo ke time tune karna) ----------
EAR_THRESH = 0.15    # isse kam = aankh band
EYE_SECONDS = 2.0      #q itni der band to alarm
MAR_THRESH = 0.5       # isse zyada = yawn
YAWN_SECONDS = 1.2
NOD_DELTA = 0.15      # head jhukne ki sensitivity
NOD_SECONDS = 1.0
ALERT_COOLDOWN = 6     # do alerts ke beech gap (sec)
FATIGUE_WINDOW = 60    # fatigue meter pichhle itne sec ka dekhta hai
LOG_FILE = "events.csv"
STATUS_FILE = "status.json"   # dashboard isse live data padhta hai

# ---------- MediaPipe landmark indices ----------
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
LEFT_EYE = [362, 385, 387, 263, 373, 380]
MOUTH = [78, 13, 308, 14]  # left, top, right, bottom

MESSAGES = {
    "EYES": "Wake up! You are feeling sleepy. Please stop the car.",
    "YAWN": "You are yawning. Please take a break.",
    "NOD": "Stay alert! Your head is dropping.",
}

def dist(a, b):
    return np.linalg.norm(a - b)

def ear(p):
    return (dist(p[1], p[5]) + dist(p[2], p[4])) / (2.0 * dist(p[0], p[3]))

def mar(p):
    return dist(p[1], p[3]) / dist(p[0], p[2])

def head_ratio(lm, w, h):
    f, n, c = (np.array([lm[i].x * w, lm[i].y * h]) for i in (10, 1, 152))
    return dist(n, f) / dist(c, n)

def beep():
    try:
        import winsound          # Windows me built-in, install nahi karna
        for _ in range(3):
            winsound.Beep(1200, 250)
    except Exception:
        print("\a")

def speak(text):
    def run():
        try:
            beep()
            e = pyttsx3.init()
            e.setProperty("rate", 150)
            e.say(text)
            e.runAndWait()
        except Exception as ex:
            print("Voice error:", ex)
    threading.Thread(target=run, daemon=True).start()

def log_event(kind):
    new = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        wr = csv.writer(f)
        if new:
            wr.writerow(["time", "event"])
        wr.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), kind])

def write_status(data):
    try:
        tmp = STATUS_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, STATUS_FILE)
    except Exception:
        pass   # dashboard ne file kholi ho to ek baar skip, koi dikkat nahi

def fatigue_percent(history):
    """PERCLOS: pichhle 60 sec me aankhen kitni der band thi."""
    if len(history) < 30:
        return 0
    perclos = sum(c for _, c in history) / len(history)
    return int(min(100, max(0, (perclos - 0.05) / 0.25 * 100)))

def draw_meter(frame, pct):
    color = (0, 200, 0) if pct < 40 else (0, 165, 255) if pct < 70 else (0, 0, 255)
    cv2.rectangle(frame, (20, 70), (220, 90), (60, 60, 60), -1)
    cv2.rectangle(frame, (20, 70), (20 + 2 * pct, 90), color, -1)
    cv2.putText(frame, f"Fatigue: {pct}%", (230, 88),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def main():
    face_mesh = mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1, refine_landmarks=True,
        min_detection_confidence=0.5, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(0)

    start = {"EYES": None, "YAWN": None, "NOD": None}
    limits = {"EYES": EYE_SECONDS, "YAWN": YAWN_SECONDS, "NOD": NOD_SECONDS}
    last_alert, last_write = 0, 0
    last_msg = "No alerts yet"
    baseline, calib = None, []
    history = deque()
    t0 = time.time()
    avg_ear, m = 0.0, 0.0

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        res = face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        status, color = "AWAKE", (0, 200, 0)
        now = time.time()

        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark
            pts = lambda ids: np.array([[lm[i].x * w, lm[i].y * h] for i in ids])
            le, re_, mo = pts(LEFT_EYE), pts(RIGHT_EYE), pts(MOUTH)
            avg_ear = (ear(le) + ear(re_)) / 2
            m = mar(mo)
            hr = head_ratio(lm, w, h)

            # aankhon ke upar hari outline
            for eye in (le, re_):
                cv2.polylines(frame, [eye.astype(np.int32)], True, (0, 255, 0), 1)

            history.append((now, 1 if avg_ear < EAR_THRESH else 0))
            while history and now - history[0][0] > FATIGUE_WINDOW:
                history.popleft()

            if now - t0 < 3:
                calib.append(hr)
                cv2.putText(frame, "Calibrating... seedha baitho", (20, 130),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            elif baseline is None:
                baseline = np.mean(calib)

            conds = {
                "EYES": avg_ear < EAR_THRESH,
                "YAWN": m > MAR_THRESH,
                "NOD": baseline is not None and abs(hr - baseline) > NOD_DELTA * baseline,
            }

            for k, active in conds.items():
                if active:
                    start[k] = start[k] or now
                    if now - start[k] > limits[k]:
                        status, color = f"DROWSY: {k}", (0, 0, 255)
                        if now - last_alert > ALERT_COOLDOWN:
                            speak(MESSAGES[k])
                            log_event(k)
                            last_msg = MESSAGES[k]
                            last_alert = now
                else:
                    start[k] = None
        else:
            status, color = "FACE NOT FOUND", (0, 165, 255)

        pct = fatigue_percent(history)

        # ---- screen par drawing ----
        if status.startswith("DROWSY"):
            cv2.rectangle(frame, (0, 0), (w - 1, h - 1), (0, 0, 255), 10)
            cv2.putText(frame, "DROWSINESS ALERT!", (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        else:
            cv2.putText(frame, status, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
        cv2.putText(frame, f"EAR: {avg_ear:.2f}", (w - 160, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        draw_meter(frame, pct)
        cv2.imshow("Drowsiness Alert", frame)

        # ---- dashboard ke liye live status (har 0.3 sec) ----
        if now - last_write > 0.3:
            write_status({
                "status": status, "ear": round(float(avg_ear), 3),
                "mar": round(float(m), 3), "fatigue": pct,
                "alarm": (now - last_alert) < 4 and last_alert > 0,
                "last_msg": last_msg, "updated": now,
            })
            last_write = now

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
