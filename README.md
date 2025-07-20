---

# **Welcome to Reclaim: The Off-Screen Time Tracker (MVP)**

Track Less of What Distracts You. Celebrate What Resets You. Unlike traditional screen-time trackers that measure only how long you stay online, this app flips the narrative -- It highlights how long you've been offline, idle, or consciously away from your device.

Whether you want to download the ready-to-run `.exe` or dive into the raw code, this guide will help you get started.

<img width="1898" height="905" alt="image" src="https://github.com/user-attachments/assets/c5d20fde-343b-4117-9511-9910ea48db22" />


---

## **🌟 What Sets This Tracker Apart?**

✅ It highlights time spent **away** from your screen  
 ✅ Tracks passive inactivity as a measure of focus and wellness  
 ✅ Gives you achievements and streaks for disconnecting  
 ✅ All data stays on your device — no accounts, no cloud, and absolutely no data about your activity gets sent to us

---

## **🔄 Your Options for Using This Tool**

### **🧃 Option 1: Run the Prebuilt App (`.exe`)**

#### **✅ How to Run**

* Download `reclaimtracker.exe` from the main page of this GitHub repo.  
* Double-click to launch the app.

#### **📊 How to Access the Dashboard Later**

* When launched, the dashboard opens automatically in your default browser.  
* To reopen it:  
  * Look for the **tray icon** in the taskbar (small blue square)  
  * Right-click → choose **"Open Dashboard"**

#### **⚠️ Windows Security Warning**

You may see a warning like “Windows protected your PC” or “Unrecognized app.” This is normal because:

* The app is built from raw Python code  
* It hasn’t been digitally signed yet  
* It’s in MVP stage with limited distribution

**You can safely click "More info" → "Run anyway"**

---

### **🛠️ Option 2: Use the Raw Code**

#### **📂 Location**

Open the `Raw Codes` folder from the main page of this repo — it contains:

| File | Purpose |
| ----- | ----- |
| `reclaimtrackerpython.py` | Main backend \+ tracking logic |
| `reclaimtrackerhtml.html` | Dashboard frontend |

#### 

#### **📦 Required Python Modules**

pip install flask pystray psutil pynput pillow pywin32

#### **▶️ How to Run**

* Download the reclaimtrackerpython.py and reclaimtrackerhtml.html files to your computer  
* Open a command prompt terminal inside the folder (type ‘cd Downloads’ and press enter in your command prompt)  
* Run this in your command promt next: ‘pip install flask pystray psutil pynput pillow pywin32’  
* Then run: python reclaimtrackerpython.py

#### **📊 How to Access the Dashboard**

* The Python server starts automatically at `http://127.0.0.1:8080`  
* Your browser should open the dashboard automatically  
* If not, manually open your browser and go to that URL (http://127.0.0.1:8080)

---

## **🧪 MVP Stage Disclaimer**

This project is still in its early phase. While stable for daily use, it may:

* Trigger antivirus warnings  
* Miss advanced features like user authentication or cloud sync

We welcome feedback, suggestions, and testing from the community.
