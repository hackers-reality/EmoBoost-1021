import flet as ft
import random
import time
from datetime import datetime, timedelta
import os # NEW: Needed to check for the consent file
import cv2  # NEW: For facial recognition

# --- LIBRARIES FOR REAL AUTOMATION ---
# Make sure you have run: pip install screen-brightness-control plyer
import screen_brightness_control as sbc
from plyer import notification
import webbrowser

# --- GLOBAL CONFIGURATION ---
TYPING_TEST_SENTENCES = [
    "Pack my box with five dozen liquor jugs.", "Sphinx of black quartz, judge my vow.",
    "How vexingly quick daft zebras jump!", "Bright vixens jump; dozy fowl quack.",
    "Jived fox nymph grabs quick waltz.", "The five boxing wizards jump quickly.",
    "Waltz, bad nymph, for quick jigs vex.", "Quick wafting zephyrs vex bold Jim.",
    "Two driven jocks help fax my big quiz.", "Crazy Fredrick bought many very exquisite opal jewels."
]

def randomise_typing_sentence():
    return random.choice(TYPING_TEST_SENTENCES)

# Playlist web links
mood_playlists = {
    "Stressed": "https://open.spotify.com/playlist/37i9dQZF1DWXe9gFZP0gtP?si=D_5dDmXpTtuM8JE4dRQ-4w",
    "Tired": "https://open.spotify.com/playlist/37i9dQZF1DX4dyzvuaRJ0n",
    "Focused": "https://open.spotify.com/playlist/2VeZCFG2ufqcDuMGJNrcVP",
    
}

def main(page: ft.Page):
    # --- App Setup ---
    colors = {
        "background": "#161C24", "card_bg": "#1F2937", "accent": "#2DD4BF", "text_primary": "#F3F4F6", "text_secondary": "#9CA3AF",
        "focused_color": "#34D399", "stressed_color": "#FBBF24", "tired_color": "#60A5FA", "normal_color": "#E5E7EB"
    }
    page.title = "Emoboost"; page.window_width = 420; page.window_height = 800; page.window_resizable = False; page.theme_mode = ft.ThemeMode.DARK; page.bgcolor = colors["background"]
    
    # --- App Memory & Calibration State ---
    mood_history = []
    last_mood_result = None
    baseline_wpm = 0.0
    baseline_error_rate = 0.0

    def create_card(content):
        return ft.Container(content=content, bgcolor=colors["card_bg"], border_radius=12, padding=ft.padding.all(18))

    # --- REAL AUTOMATION FUNCTIONS ---
    def set_brightness(level):
        try: sbc.set_brightness(level); print(f"Brightness set to {level}%")
        except Exception as e: print(f"Could not control screen brightness. Error: {e}")

    def send_real_notification(title, message):
        try: notification.notify(title=title, message=message, app_name="Emoboost", timeout=10); print("OS notification sent.")
        except Exception as e: print(f"Could not send OS notification. Error: {e}")

    def open_mood_playlist(mood):
        try:
            playlist_url = mood_playlists.get(mood)
            if playlist_url: webbrowser.open(playlist_url); print(f"Opening '{mood}' playlist in web browser.")
        except Exception as e: print(f"Could not open playlist in browser. Error: {e}")

    def recognize_mood_from_face():
        """
        Attempts to recognize mood from facial expressions using the webcam.
        Returns a string mood ("Happy", "Sad", "Neutral", etc.) or raises an error if no camera is found.
        """
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise RuntimeError("No camera detected. Please connect a webcam to use facial mood recognition.")
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            mood = "Neutral"
            detected = False
            for _ in range(30):  # Try for ~1 second (30 frames)
                ret, frame = cap.read()
                if not ret:
                    continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                if len(faces) > 0:
                    detected = True
                    # Placeholder: In a real app, use a deep learning model for emotion detection here.
                    mood = "Neutral"
                    break
            cap.release()
            if not detected:
                raise RuntimeError("Face not detected. Please ensure your face is visible to the camera.")
            return mood
        except Exception as e:
            try:
                notification.notify(
                    title="Emoboost: Camera Error",
                    message=str(e),
                    app_name="Emoboost",
                    timeout=8
                )
            except Exception:
                pass
            print(f"Facial recognition error: {e}")
            return None

    # --- Check-in View ---
    typing_field_ref = ft.Ref[ft.TextField](); typing_start_time = 0
    typing_test_text = randomise_typing_sentence()

    # Webcam video streaming for Flet (using OpenCV and base64)
    import threading
    import base64
    from io import BytesIO
    from PIL import Image

    webcam_image_ref = ft.Ref[ft.Image]()
    webcam_running = {"active": False}

    def webcam_stream_loop():
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            webcam_running["active"] = False
            return
        while webcam_running["active"]:
            ret, frame = cap.read()
            if not ret:
                continue
            # Convert frame to RGB and resize for UI
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (320, 240))
            img_pil = Image.fromarray(frame)
            buf = BytesIO()
            img_pil.save(buf, format="JPEG")
            img_bytes = buf.getvalue()
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            if webcam_image_ref.current:
                webcam_image_ref.current.src_base64 = img_b64
                webcam_image_ref.current.update()
            time.sleep(0.05)
        cap.release()

    def start_webcam():
        if not webcam_running["active"]:
            webcam_running["active"] = True
            threading.Thread(target=webcam_stream_loop, daemon=True).start()

    def stop_webcam():
        webcam_running["active"] = False

    def analyze_and_submit(e):
        nonlocal typing_start_time, last_mood_result, baseline_wpm, baseline_error_rate, typing_test_text
        stop_webcam()  # Stop webcam stream before facial recognition
        # Activate facial recognition during check-in/calibration
        face_mood = recognize_mood_from_face()
        if face_mood is None:
            page.snack_bar = ft.SnackBar(content=ft.Text("Facial recognition failed. Please check your camera."), bgcolor=colors["card_bg"])
            page.snack_bar.open = True
            page.update()
            # Ask again for facial recognition during check-in
            start_webcam()
            face_mood_retry = recognize_mood_from_face()
            stop_webcam()
            if face_mood_retry is None:
                page.snack_bar = ft.SnackBar(content=ft.Text("Facial recognition failed again. Skipping facial mood detection."), bgcolor=colors["card_bg"])
                page.snack_bar.open = True
                page.update()
            else:
                face_mood = face_mood_retry
        # Continue with typing analysis regardless of facial recognition result
        typed_text = typing_field_ref.current.value or ""
        end_time = time.time(); time_taken = end_time - typing_start_time if typing_start_time > 0 else 0
        word_count = len(typed_text.split()); wpm = (word_count / time_taken * 60) if time_taken > 0 else 0
        errors = sum(1 for i, char in enumerate(typed_text) if i >= len(typing_test_text) or char != typing_test_text[i])
        error_rate = (errors / len(typing_test_text)) * 100 if typed_text else 0
        mood = "Normal"
        if baseline_wpm == 0:
            baseline_wpm = wpm; baseline_error_rate = error_rate if error_rate > 0 else 1.0; mood = "Calibrated"
            print(f"CALIBRATION COMPLETE: Baseline WPM={baseline_wpm:.1f}, Baseline Error Rate={baseline_error_rate:.1f}%")
        else:
            is_slower = wpm < baseline_wpm * 0.75; is_faster = wpm > baseline_wpm * 0.50
            is_sloppy = error_rate > baseline_error_rate * 2 and error_rate > 5
            is_accurate = error_rate < baseline_error_rate * 0.7
            if is_slower and is_sloppy: mood = "Tired"
            elif is_faster and is_sloppy: mood = "Stressed"
            elif is_faster and is_accurate: mood = "Focused"
        # Optionally, combine face_mood with typing mood here
        print(f"Analysis: WPM={wpm:.1f}, Error Rate={error_rate:.1f}%, Typing Mood={mood}, Facial Mood={face_mood}")
        if mood != "Calibrated": mood_history.append({'timestamp': datetime.now(), 'mood': mood, 'value': random.randint(1, 10)})
        last_mood_result = mood
        if mood == "Stressed":
            set_brightness(30); open_mood_playlist("Stressed"); send_real_notification("Emoboost: Stress Detected", "We're dimming the lights and opening a calming playlist for you.")
        elif mood == "Tired":
            set_brightness(80); open_mood_playlist("Tired"); send_real_notification("Emoboost: Tiredness Detected", "Let's get some energy! Opening a playlist to wake you up.")
        elif mood == "Focused":
            open_mood_playlist("Focused")
            try:
                import subprocess; subprocess.run(["powershell", "-Command", "[Windows.UI.Notifications.Management.UserNotificationListener, Windows.Foundation.UniversalApiContract, ContentType=WindowsRuntime];$listener = [Windows.UI.Notifications.Management.UserNotificationListener]::Current;$listener.RequestAccessAsync() | Out-Null;[Windows.UI.Notifications.Management.UserNotificationListenerAccessStatus]::Allowed;New-ItemProperty -Path HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings -Name NOC_GLOBAL_SETTING_TOASTS_ENABLED -Value 0 -PropertyType DWord -Force | Out-Null"], shell=True)
                print("DND mode enabled (Windows Focus Assist).")
            except Exception as e: print(f"Could not enable DND mode: {e}")
            send_real_notification("Emoboost: Focus Mode", "DND (Focus Assist) enabled for your productivity.")
        page.go("/")

    def on_typing_start(e):
        nonlocal typing_start_time
        if typing_start_time == 0: typing_start_time = time.time()

    def create_checkin_view():
        nonlocal typing_test_text
        typing_test_text = randomise_typing_sentence()
        start_webcam()
        return ft.View(
            "/checkin",
            [
                ft.AppBar(
                    title=ft.Text("First-Time Calibration" if baseline_wpm == 0 else "Mood Check-in"),
                    bgcolor=colors["background"],
                    leading=ft.IconButton(icon="arrow_back_ios_new_rounded", tooltip="Go Back", on_click=lambda _: (stop_webcam(), page.go("/")))
                ),
                ft.Column([
                    create_card(
                        ft.Column([
                            ft.Text("Facial Recognition (Live)", weight=ft.FontWeight.BOLD),
                            # FIX: Remove 'border' argument, keep only supported ones
                            ft.Image(
                                ref=webcam_image_ref,
                                width=320,
                                height=240,
                                fit=ft.ImageFit.CONTAIN,
                                border_radius=8
                            ),
                            ft.Text("Please keep your face visible to the camera for mood detection.", color=colors["text_secondary"], size=12),
                            ft.Divider(height=10, color="transparent"),
                            ft.Text("Typing Analysis", weight=ft.FontWeight.BOLD),
                            ft.Text(
                                "Please type the paragraph below at a comfortable, normal pace." if baseline_wpm == 0 else "Please type the paragraph below.",
                                color=colors["text_secondary"], size=13
                            ),
                            ft.Text(f'"{typing_test_text}"', italic=True, size=14),
                            ft.TextField(ref=typing_field_ref, multiline=True, min_lines=3, on_change=on_typing_start, border_color=colors["accent"]),
                        ])
                    ),
                    ft.ElevatedButton("Analyze & Submit Mood", icon="science", on_click=analyze_and_submit, bgcolor=colors["accent"], color=colors["background"], height=50, expand=True)
                ], spacing=15, scroll=ft.ScrollMode.ADAPTIVE, expand=True)
            ]
        )

    # --- Dashboard View ---
    def create_dashboard_view():
        nonlocal last_mood_result
        def reset_history(e):
            nonlocal last_mood_result, baseline_wpm, baseline_error_rate; mood_history.clear(); last_mood_result = None; baseline_wpm = 0.0; baseline_error_rate = 0.0
            if os.path.exists("consent.txt"): os.remove("consent.txt")
            page.snack_bar = ft.SnackBar(content=ft.Text("App has been reset to factory settings!"), bgcolor=colors["card_bg"]); page.snack_bar.open = True; page.go("/terms")
        mood_actions = { "Stressed": {"icon": "local_fire_department", "color": colors["stressed_color"], "actions": ["Dimming screen brightness", "Opening a calming playlist", "Sending helpful notification"]}, "Tired": {"icon": "bedtime", "color": colors["tired_color"], "actions": ["Opening an energizing playlist", "Suggesting a short break", "Increasing screen brightness"]}, "Focused": {"icon": "psychology", "color": colors["focused_color"], "actions": ["Opening your focus playlist", "Silencing non-critical notifications"]}, "Normal": {"icon": "sentiment_satisfied", "color": colors["normal_color"], "actions": ["Everything looks great!", "Keeping your environment stable.", "Have a productive day!"]}, "Calibrated": {"icon": "verified_user", "color": colors["accent"], "actions": ["Your personal baseline has been set.", "Future check-ins will be compared to this.", "You can reset this any time."]} }
        top_card_content = None
        if not last_mood_result:
            top_card_content = create_card(ft.Column([ft.Text("Ready to calibrate?", size=16), ft.Text("Perform your first check-in to set your personal baseline.", size=13, color=colors["text_secondary"]), ft.Divider(height=15, color="transparent"), ft.ElevatedButton(text="Start Calibration", icon="sensors", on_click=lambda _: page.go("/checkin"), bgcolor=colors["accent"], color=colors["background"], height=50)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8))
        else:
            current_mood_data = mood_actions[last_mood_result]; actions_list_view = ft.Column([ft.Row([ft.Icon("check_circle_outline", color=colors["text_secondary"], size=16), ft.Text(action, color=colors["text_secondary"], size=13)]) for action in current_mood_data["actions"]])
            top_card_content = create_card(ft.Column([ft.Row([ft.Icon(name=current_mood_data["icon"], color=current_mood_data["color"]), ft.Text("Emoboost Bot's Analysis", weight=ft.FontWeight.BOLD)]), ft.Divider(height=10), ft.Text(f"Calibration Complete!" if last_mood_result == "Calibrated" else f"You seem to be feeling: {last_mood_result}", size=18, weight=ft.FontWeight.W_500), ft.Text("Based on this, we're making the following adjustments:", size=12, color=colors["text_secondary"]), ft.Divider(height=10), actions_list_view]))
        dashboard_app_bar = ft.AppBar(title=ft.Text("Emoboost Dashboard"), bgcolor=colors["background"], actions=[ft.IconButton(icon="published_with_changes", icon_color=colors["accent"], tooltip="Start a new check-in", on_click=lambda _: page.go("/checkin"))])
        chart_content = None
        if not mood_history:
            chart_content = ft.Column([ft.Icon(name="bar_chart_4_bars_rounded", size=40, color=colors["text_secondary"]), ft.Text("No mood history yet.", color=colors["text_secondary"]), ft.Text("Complete a check-in to see your chart.", size=12, color=colors["text_secondary"]),], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        else:
            sorted_history = sorted(mood_history, key=lambda x: x['timestamp']); focused_points, stressed_points, tired_points, normal_points, bottom_axis_labels = [], [], [], [], [];
            def add_point_to_series(entry, point):
                if entry['mood'] == 'Focused': focused_points.append(point)
                elif entry['mood'] == 'Stressed': stressed_points.append(point)
                elif entry['mood'] == 'Tired': tired_points.append(point)
                elif entry['mood'] == 'Normal': normal_points.append(point)
            for i, entry in enumerate(sorted_history):
                real_point = ft.LineChartDataPoint(entry['timestamp'].timestamp(), entry['value']); add_point_to_series(entry, real_point); bottom_axis_labels.append(ft.ChartAxisLabel(value=entry['timestamp'].timestamp(), label=ft.Text(entry['timestamp'].strftime('%H:%M'), size=10, color=colors["text_secondary"])))
                if i < len(sorted_history) - 1: next_entry = sorted_history[i+1]; bridging_point = ft.LineChartDataPoint(next_entry['timestamp'].timestamp(), entry['value']); add_point_to_series(entry, bridging_point)
            if sorted_history: last_entry = sorted_history[-1]; final_bridging_point = ft.LineChartDataPoint(datetime.now().timestamp(), last_entry['value']); add_point_to_series(last_entry, final_bridging_point)
            def create_legend_item(color, name): return ft.Row([ft.Container(width=12, height=12, bgcolor=color, border_radius=6), ft.Text(name, size=12, color=colors["text_secondary"])], spacing=8)
            legend = ft.Row([create_legend_item(colors["normal_color"], "Normal"), create_legend_item(colors["focused_color"], "Focused"), create_legend_item(colors["stressed_color"], "Stressed"), create_legend_item(colors["tired_color"], "Tired")], alignment=ft.MainAxisAlignment.SPACE_EVENLY)
            chart = ft.LineChart(data_series=[ft.LineChartData(data_points=normal_points, stroke_width=3, color=colors["normal_color"]), ft.LineChartData(data_points=focused_points, stroke_width=3, color=colors["focused_color"]), ft.LineChartData(data_points=stressed_points, stroke_width=3, color=colors["stressed_color"]), ft.LineChartData(data_points=tired_points, stroke_width=3, color=colors["tired_color"]),], left_axis=ft.ChartAxis(labels_interval=2, title_size=0, labels_size=12), bottom_axis=ft.ChartAxis(labels=bottom_axis_labels, labels_size=12), min_y=0, max_y=10, border=ft.border.all(1, colors["text_secondary"]), expand=True, horizontal_grid_lines=ft.ChartGridLines(interval=2, color=f"{colors['text_secondary']}33"), tooltip_bgcolor="#1F2937CC")
            chart_content = ft.Column([chart, ft.Divider(height=5, color="transparent"), legend], expand=True, spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        history_card_title = ft.Row([ft.Text(f"MOOD HISTORY ({datetime.now().strftime('%b %d')})", size=11, weight=ft.FontWeight.BOLD, color=colors["text_secondary"]), ft.Container(expand=True), ft.IconButton(icon="delete_sweep_outlined", on_click=reset_history, tooltip="Clear History", icon_size=16, icon_color=colors["text_secondary"])])
        history_card = create_card(ft.Column([history_card_title, ft.Divider(height=5, color="transparent"), chart_content], expand=True, spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER,))
        return ft.View("/", [dashboard_app_bar, ft.Column([top_card_content, history_card], spacing=15, scroll=ft.ScrollMode.ADAPTIVE, expand=True)])

    # --- NEW: Terms and Conditions View ---
    def create_terms_view():
        continue_button_ref = ft.Ref[ft.ElevatedButton]()
        def on_checkbox_change(e):
            continue_button_ref.current.disabled = not e.control.value; page.update()
        def on_continue(e):
            try:
                with open("consent.txt", "w") as f: f.write("accepted")
                page.go("/")
            except Exception as ex: print(f"Error creating consent file: {ex}")
        terms_text = "Welcome to Emoboost.\n\n1. Privacy and Data:\nThis app performs a typing test to simulate mood analysis. This data is processed locally on your device and is not sent to any server. App history is also stored locally.\n\n2. Disclaimer:\nEmoboost is a proof-of-concept project for a hackathon. It is not a medical device and should not be used for diagnosing or treating any health conditions.\n\n3. Consent:\nBy checking this box and clicking 'Continue', you acknowledge that you have read and understood these terms."
        return ft.View("/terms", [ft.AppBar(title=ft.Text("Terms and Conditions"), bgcolor=colors["background"]), ft.Column([create_card(ft.Column([ft.Text(terms_text, color=colors["text_secondary"]), ft.Checkbox(label="I have read and agree to the Terms and Conditions.", on_change=on_checkbox_change), ft.ElevatedButton("Continue", ref=continue_button_ref, disabled=True, on_click=on_continue, bgcolor=colors["accent"], color=colors["background"], expand=True)], spacing=20))], spacing=15, scroll=ft.ScrollMode.ADAPTIVE, expand=True)])

    # --- Navigation Logic ---
    def route_change(route):
        page.views.clear()
        if page.route == "/terms": page.views.append(create_terms_view())
        elif page.route == "/checkin": page.views.append(create_dashboard_view()); page.views.append(create_checkin_view())
        else: page.views.append(create_dashboard_view())
        page.update()
    def view_pop(view):
        page.views.pop(); top_view = page.views[-1]; page.go(top_view.route)
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # --- NEW: Startup Logic ---
    if not os.path.exists("consent.txt"):
        page.go("/terms")
    else:
        page.go("/")

ft.app(target=main)

