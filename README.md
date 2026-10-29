# 🚗 Driver Drowsiness Alert System

A real-time computer vision project that monitors a driver's face through a webcam and raises an alert when signs of drowsiness are detected, helping reduce the risk of fatigue-related road accidents.

Built **solo in 6 hours** at **Hacktoberfest Hack Day Jaunpur** (powered by MLH) and awarded **Best Participant** 🏆.

---

## 📌 Overview

Drowsy driving is one of the leading causes of road accidents. This project uses a camera feed to track the driver's eyes, detects prolonged eye closure and triggers an alert so the driver can react in time. A Streamlit dashboard shows the live status and logged drowsiness events.

## ✨ Features

- Real-time face and eye tracking using a webcam
- Drowsiness detection based on eye closure
- Instant alert when the driver appears drowsy
- Streamlit dashboard for live status
- Event logging to `events.csv`
- Modular code: detection logic and dashboard are separate

## 🛠️ Tech Stack

- **Python**
- **OpenCV**: video capture and image processing
- **MediaPipe**: face and eye landmark detection
- **Streamlit**: dashboard UI
- **NumPy**

## 📂 Project Structure

```
Driven-Drowsiness-alert/
├── detector.py        # Drowsiness detection logic
├── dashboard.py       # Streamlit dashboard
├── events.csv         # Logged drowsiness events
├── status.json        # Live status shared with the dashboard
├── requirements.txt   # Python dependencies
└── README.md
```

## ⚙️ Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Palak-1612/Driven-Drowsiness-alert.git
   cd Driven-Drowsiness-alert
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## ▶️ How to Run

Open two terminals in the project folder (with the virtual environment activated).

**Terminal 1: start the detector**

```bash
python detector.py
```

**Terminal 2: start the dashboard**

```bash
streamlit run dashboard.py
```

Make sure your webcam is connected and not being used by another app.

## 🔮 Future Improvements

- Hardware alerts (buzzer / LED / vibration motor) using Arduino
- Yawn and head-pose detection for better accuracy
- Performance improvements in low-light conditions

## 👩‍💻 Author

**Palak Singh**
Computer Science student | Python and AI/ML enthusiast

- GitHub: [@Palak-1612](https://github.com/Palak-1612)
- LinkedIn: [Palak Singh](https://www.linkedin.com/in/palak-singh-45974a387)
