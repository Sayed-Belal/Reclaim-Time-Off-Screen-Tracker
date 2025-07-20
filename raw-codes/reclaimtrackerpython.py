from flask import Flask, jsonify, send_from_directory, request
import time
import threading
import win32gui
import win32process
import psutil
from pynput import mouse, keyboard
from datetime import datetime, time as dt_time, timedelta
import json
import os
import random
from collections import defaultdict
import sys
import shutil


IDLE_TIMEOUT = 120
DEFAULT_AWAKE_TIME = "06:00"
DEFAULT_SLEEP_TIME = "23:00"
DATA_FILE = "all_apps_daily_usage_data.json"
SETTINGS_FILE = "all_apps_user_settings.json"
ACHIEVEMENTS_FILE = "user_achievements.json"
HOURLY_ACTIVITY_FILE = "hourly_activity_data.json"

DAILY_QUOTES = [
    "Time off-screen is time invested in yourself.",
    "Small steps each day lead to big changes.",
    "Balance is not something you find, it's something you create.",
    "Every moment offline is a moment to reconnect with yourself.",
    "Digital wellness is self-care in the modern age.",
]

last_input_time = time.time()
total_active_time = 0
daily_usage_data = {}
hourly_activity_data = {}
current_hour_activity = 0
last_tracked_hour = None
app = Flask(__name__, static_url_path='')

def load_json_file(path, default):
    if os.path.exists(path):
        with open(path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default
    return default

def save_json_file(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def format_hms(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

def get_daily_quote():
    return random.choice(DAILY_QUOTES)

def calculate_streak(data):
    streak = 0
    today = datetime.now().date()
    
    for days_back in range(30):
        check_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
        if check_date in data:
            inactive_hours = data[check_date].get("inactive_seconds", 0) / 3600
            if inactive_hours >= 2:
                streak += 1
            else:
                break
        else:
            break
    return streak

def add_to_startup():
    startup_path = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
    exe_path = sys.executable
    destination = os.path.join(startup_path, os.path.basename(exe_path))

    if not os.path.exists(destination):
        shutil.copyfile(exe_path, destination)


def calculate_achievements(user_data):
    achievements = []
    total_inactive_time = sum(day.get("inactive_seconds", 0) for day in user_data.values())
    inactive_hours = total_inactive_time / 3600

    if inactive_hours >= 1:
        achievements.append({
            "title": "First Hour Milestone",
            "description": "Completed your first hour of mindful off-screen time!",
            "icon": "🌟"
        })
    if inactive_hours >= 4:
        achievements.append({
            "title": "Focused Day Achievement",
            "description": "Achieved 4 hours of balanced screen time!",
            "icon": "🏆"
        })
    if inactive_hours >= 8:
        achievements.append({
            "title": "Life Balance Master",
            "description": "Maintained 8 hours of healthy off-screen time!",
            "icon": "🎯"
        })
    
    streak = calculate_streak(user_data)
    if streak >= 7:
        achievements.append({
            "title": "Weekly Warrior",
            "description": f"Maintained a {streak}-day streak!",
            "icon": "🔥"
        })

    return achievements

def get_sleepwake_times_for_date(date_str):
    wake = user_settings.get("wake_times", {}).get(date_str, user_settings.get("awake_time", DEFAULT_AWAKE_TIME))
    sleep = user_settings.get("sleep_times", {}).get(date_str, user_settings.get("sleep_time", DEFAULT_SLEEP_TIME))
    return wake, sleep

def seconds_between(wake_str, sleep_str, now=None, date_str=None):
    now = now or datetime.now()
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        dt = now
    hour_w, min_w = map(int, wake_str.split(":"))
    hour_s, min_s = map(int, sleep_str.split(":"))
    wake_time = datetime.combine(dt.date(), dt_time(hour_w, min_w))
    sleep_time = datetime.combine(dt.date(), dt_time(hour_s, min_s))
    if sleep_time <= wake_time:
        sleep_time += timedelta(days=1)
    period_end = min(now, sleep_time)
    if period_end < wake_time:
        return 0
    return max((period_end - wake_time).total_seconds(), 0)

def get_today_key():
    return datetime.now().strftime("%Y-%m-%d")

def get_current_hour_key():
    return datetime.now().strftime("%Y-%m-%d-%H")

def is_awake_hours():
    now = datetime.now().time()
    today_str = get_today_key()
    wake, sleep = get_sleepwake_times_for_date(today_str)
    hour_w, min_w = map(int, wake.split(":"))
    hour_s, min_s = map(int, sleep.split(":"))
    wake_time = dt_time(hour_w, min_w)
    sleep_time = dt_time(hour_s, min_s)
    if sleep_time > wake_time:
        return wake_time <= now < sleep_time
    else:
        return now >= wake_time or now < sleep_time

def get_focused_window_proc():
    try:
        fg_window = win32gui.GetForegroundWindow()
        if fg_window == 0:
            return None
        _, pid = win32process.GetWindowThreadProcessId(fg_window)
        proc = psutil.Process(pid)
        placement = win32gui.GetWindowPlacement(fg_window)
        if placement[1] == 2:  # minimized
            return None
        return proc.name().lower()
    except Exception:
        return None

def on_input(_):
    global last_input_time
    last_input_time = time.time()

def start_input_listeners():
    mouse.Listener(on_move=on_input, on_click=on_input, on_scroll=on_input).start()
    keyboard.Listener(on_press=on_input).start()

def update_hourly_activity():
    """Update hourly activity tracking"""
    global current_hour_activity, last_tracked_hour
    
    current_hour_key = get_current_hour_key()
    
    if last_tracked_hour and last_tracked_hour != current_hour_key:
        date_part, hour_part = last_tracked_hour.rsplit('-', 1)
        if date_part not in hourly_activity_data:
            hourly_activity_data[date_part] = {}
        hourly_activity_data[date_part][hour_part] = hourly_activity_data[date_part].get(hour_part, 0) + current_hour_activity
        current_hour_activity = 0
        save_json_file(HOURLY_ACTIVITY_FILE, hourly_activity_data)
    
    last_tracked_hour = current_hour_key

def get_peak_activity_hours(days=7):
    """Get the most active hours across recent days"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    hourly_totals = defaultdict(int)
    hourly_counts = defaultdict(int)
    
    for date_str, hours_data in hourly_activity_data.items():
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            if start_date <= date_obj <= end_date:
                for hour_str, seconds in hours_data.items():
                    hour = int(hour_str)
                    hourly_totals[hour] += seconds
                    hourly_counts[hour] += 1
        except (ValueError, KeyError):
            continue

    hourly_averages = {}
    for hour in hourly_totals:
        if hourly_counts[hour] > 0:
            hourly_averages[hour] = hourly_totals[hour] / hourly_counts[hour]
    
    sorted_hours = sorted(hourly_averages.items(), key=lambda x: x[1], reverse=True)
    
    peak_hours = []
    for hour, avg_seconds in sorted_hours[:5]:
        avg_minutes = avg_seconds / 60
        time_str = f"{hour:02d}:00"
        peak_hours.append({
            "hour": hour,
            "time": time_str,
            "average_active_minutes": round(avg_minutes, 1),
            "average_active_seconds": round(avg_seconds, 0)
        })
    
    return peak_hours

def get_today_peak_hours():
    """Get today's most active hours so far"""
    today_str = get_today_key()
    today_data = hourly_activity_data.get(today_str, {})
    
    # Add current hour's activity if any
    current_hour = datetime.now().hour
    if current_hour_activity > 0:
        today_data = today_data.copy()
        today_data[str(current_hour)] = today_data.get(str(current_hour), 0) + current_hour_activity
    
    # Sort by activity
    hourly_activity = [(int(hour), seconds) for hour, seconds in today_data.items()]
    hourly_activity.sort(key=lambda x: x[1], reverse=True)
    
    # Format results
    today_peaks = []
    for hour, seconds in hourly_activity[:3]:  # Top 3 for today
        minutes = seconds / 60
        time_str = f"{hour:02d}:00"
        today_peaks.append({
            "hour": hour,
            "time": time_str,
            "active_minutes": round(minutes, 1),
            "active_seconds": seconds
        })
    
    return today_peaks

daily_usage_data = load_json_file(DATA_FILE, {})
hourly_activity_data = load_json_file(HOURLY_ACTIVITY_FILE, {})
user_settings = load_json_file(SETTINGS_FILE, {
    "awake_time": DEFAULT_AWAKE_TIME,
    "sleep_time": DEFAULT_SLEEP_TIME,
    "wake_times": {},
    "sleep_times": {},
    "goals": {}
})

def update_current_day_data():
    global total_active_time
    today_str = get_today_key()
    if today_str not in daily_usage_data:
        total_active_time = 0
        daily_usage_data[today_str] = {
            "active_seconds": 0
        }
        save_json_file(DATA_FILE, daily_usage_data)
    else:
        total_active_time = daily_usage_data[today_str].get("active_seconds", 0)

def tracking_loop():
    global total_active_time, current_hour_activity
    start_input_listeners()
    last_state = None
    inactive_start = None
    while True:
        update_current_day_data()
        update_hourly_activity()
        time.sleep(1)
        idle_duration = time.time() - last_input_time
        focused_proc = get_focused_window_proc()
        if focused_proc and idle_duration < IDLE_TIMEOUT:
            total_active_time += 1
            current_hour_activity += 1  # Track hourly activity
            last_state = "active"
            inactive_start = None
        else:
            if last_state != "inactive":
                inactive_start = time.time()
                last_state = "inactive"
        today_str = get_today_key()
        daily_usage_data[today_str]["active_seconds"] = total_active_time
        save_json_file(DATA_FILE, daily_usage_data)

def generate_insights():
    today_str = get_today_key()
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    current_week_data = {k: v for k, v in daily_usage_data.items() if k >= week_ago}
    
    total_inactive = sum(day.get("inactive_seconds", 0) for day in current_week_data.values())
    avg_inactive = total_inactive / max(len(current_week_data), 1) / 3600  # Convert to hours
    
    streak = calculate_streak(daily_usage_data)
    highest_streak = max([calculate_streak({k: v for k, v in daily_usage_data.items() if k <= date}) 
                         for date in daily_usage_data.keys()] + [0])
    
    return {
        "weekly_average": round(avg_inactive, 1),
        "current_streak": streak,
        "highest_streak": highest_streak,
        "daily_quote": get_daily_quote(),
        "achievements": calculate_achievements(current_week_data),
        "peak_hours_week": get_peak_activity_hours(7),
        "peak_hours_today": get_today_peak_hours()
    }

@app.route("/")
def index():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return send_from_directory(base_path, 'reclaimtrackerhtml.html')

@app.route("/status")
def status():
    today_str = get_today_key()
    wake, sleep = get_sleepwake_times_for_date(today_str)
    active_seconds = daily_usage_data.get(today_str, {}).get("active_seconds", 0)
    total_since_awake = seconds_between(wake, sleep)
    active_seconds_awake = min(active_seconds, total_since_awake)
    inactive_seconds = max(total_since_awake - active_seconds_awake, 0)
    
    insights = generate_insights()
    
    return jsonify({
        "active_time_seconds": active_seconds,
        "inactive_time_seconds": inactive_seconds,
        "active_time_formatted": format_hms(active_seconds),
        "inactive_time_formatted": format_hms(inactive_seconds),
        "insights": insights
    })

@app.route("/historical_status")
def historical_status():
    filtered_data = {}
    for date, data in daily_usage_data.items():
        wake, sleep = get_sleepwake_times_for_date(date)
        active = data.get("active_seconds", 0)
        period = seconds_between(wake, sleep, now=datetime.strptime(date, "%Y-%m-%d") + timedelta(hours=23, minutes=59), date_str=date)
        inactive = max(period - active, 0)
        if active > 0 or inactive > 0:
            filtered_data[date] = {
                "active_seconds": active,
                "inactive_seconds": inactive
            }
    return jsonify(filtered_data)

@app.route("/peak_activity_hours")
def peak_activity_hours():
    """Endpoint to get peak activity hours data"""
    return jsonify({
        "weekly_peaks": get_peak_activity_hours(7),
        "today_peaks": get_today_peak_hours()
    })

@app.route("/get_goals")
def get_goals():
    return jsonify(user_settings.get("goals", {}))

@app.route("/save_goal", methods=["POST"])
def save_goal():
    req = request.json
    date = req.get("date")
    hours = req.get("hours")
    if not date or not hours:
        return jsonify({"status": "error", "message": "Missing date or hours"}), 400
    try:
        hours = float(hours)
    except:
        return jsonify({"status": "error", "message": "Invalid hours"}), 400
    if hours < 0.5 or hours > 24:
        return jsonify({"status": "error", "message": "Goal must be between 0.5 and 24"}), 400
    user_settings.setdefault("goals", {})[date] = hours
    save_json_file(SETTINGS_FILE, user_settings)
    return jsonify({"status": "success"})

@app.route("/get_sleepwake_times")
def get_sleepwake_times():
    times = {}
    for date in daily_usage_data.keys():
        times[date] = {
            "wake": user_settings.get("wake_times", {}).get(date, user_settings.get("awake_time", DEFAULT_AWAKE_TIME)),
            "sleep": user_settings.get("sleep_times", {}).get(date, user_settings.get("sleep_time", DEFAULT_SLEEP_TIME))
        }
    return jsonify(times)

@app.route("/save_sleepwake_times", methods=["POST"])
def save_sleepwake_times():
    req = request.json
    date = req.get("date")
    wake = req.get("wake")
    sleep = req.get("sleep")
    if not date or not wake or not sleep:
        return jsonify({"status": "error", "message": "Missing date, wake, or sleep"}), 400
    user_settings.setdefault("wake_times", {})[date] = wake
    user_settings.setdefault("sleep_times", {})[date] = sleep
    save_json_file(SETTINGS_FILE, user_settings)
    return jsonify({"status": "success"})

def print_times_loop():
    import sys
    while True:
        today_str = get_today_key()
        active_seconds = daily_usage_data.get(today_str, {}).get("active_seconds", 0)
        wake, sleep = get_sleepwake_times_for_date(today_str)
        total_since_awake = seconds_between(wake, sleep)
        inactive_seconds = max(total_since_awake - active_seconds, 0)
        sys.stdout.write(
            f"\rActive Time: {format_hms(active_seconds)}   Away Time: {format_hms(inactive_seconds)}   "
        )
        sys.stdout.flush()
        time.sleep(5)

import webbrowser
import sys

def open_browser():
    webbrowser.open_new("http://127.0.0.1:8080/")

from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw

def open_dashboard_via_tray(icon, item):
    webbrowser.open_new("http://127.0.0.1:8080/")

def exit_app(icon, item):
    icon.stop()

def create_tray_icon():
    image = Image.new("RGB", (64, 64), "blue")
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, 48, 48), fill="white")

    menu = Menu(
        MenuItem("Open Dashboard", open_dashboard_via_tray),
        MenuItem("Exit", exit_app)
    )
    icon = Icon("DashboardTracker", image, "ScreenTime Tracker", menu)
    tray_thread = threading.Thread(target=icon.run, daemon=True)
    tray_thread.start()

if __name__ == "__main__":
    add_to_startup()
    
    update_current_day_data()
    tracker_thread = threading.Thread(target=tracking_loop, daemon=True)
    tracker_thread.start()
    print_thread = threading.Thread(target=print_times_loop, daemon=True)
    print_thread.start()
    create_tray_icon()
    app.run(debug=False, port=8080)
