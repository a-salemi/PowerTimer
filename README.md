# PowerTimer

> Modern, crash-proof system automation and power scheduler for Windows.

PowerTimer is an open-source, reliable system power scheduling utility for Windows built with PyQt6, featuring a modern dark interface, crisp custom vector glyphs, and Google Sans typography.

![PowerTimer Preview](assets/preview.png)

---

## Features

- **Intuitive 3-Step Workflow:**
  1. **Choose Action:** Shutdown, Restart, Sleep, Hibernate, Lock Workstation, or Turn Off Screen.
  2. **Configure Timing:** Choose between Countdown Timer, Exact Target Time, or Inactivity / Idle detection.
  3. **Start Schedule:** Monitor with a live digital clock, progress bar, and instant cancellation controls.
- **Dedicated Running Dashboard:** Transitions to an active countdown view with animated progress and real-time status.
- **Safety & Automation Controls:**
  - Force close unresponsive applications (`/f`).
  - Audible chime and notification alert 60 seconds prior to execution.
  - Minimize to Windows System Tray.
- **Crash-Proof Design:** Direct Windows API integration with safe exception handling.

---

## Screenshots

| Setup View | Running Monitor View |
| :---: | :---: |
| ![Setup](assets/preview.png) | ![Running](assets/running_preview.png) |

---

## Installation & Download

### Option 1: Pre-Built Executable (Recommended)
Download the latest standalone `PowerTimer.exe` from the [Releases](../../releases) page. No Python installation required.

### Option 2: Run from Source
1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/PowerTimer.git
   cd PowerTimer
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```

---

## Building from Source

To compile the standalone single-file binary with PyInstaller:

```bash
pyinstaller --onefile --windowed --icon="icon.ico" --add-data "fonts;fonts" --name="PowerTimer" app.py
```

---

## License

This project is licensed under the MIT License.
