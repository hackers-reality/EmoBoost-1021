# EmoBoost-1021
## Emoboost - Mood-Based Productivity Enhancer
Overview
Emoboost is an intelligent application that analyzes your mood through typing patterns and facial recognition, then automatically adjusts your environment to optimize productivity and well-being. It can dim your screen, enable Do Not Disturb mode, and suggest playlists based on your detected emotional state.

Key Features
Mood Detection: Uses typing speed/accuracy and facial recognition to determine your emotional state

Smart Adjustments: Automatically makes changes to your environment:

Screen brightness adjustment

Do Not Disturb mode activation

Curated playlist suggestions

Historical Tracking: Visualizes your mood patterns over time

Privacy-Focused: All processing happens locally on your device

Mood States Detected
Stressed - Dims lights, plays calming music

Tired - Increases brightness, suggests energizing music

Focused - Enables DND mode, plays concentration music

Normal - Maintains current settings

Installation
Ensure you have Python 3.8+ installed

Install required packages:

bash
pip install flet screen-brightness-control plyer opencv-python
Usage
Run the application:

bash
python FINAL_PROTOTYPE.py
Complete the initial calibration by typing the provided text

Subsequent check-ins will compare to your baseline

The app will automatically make adjustments based on your mood

Technical Details
Typing Analysis: Measures WPM and error rate against baseline

Facial Recognition: Uses OpenCV for basic face detection

Automation:

screen-brightness-control for display adjustments

plyer for system notifications

Windows Focus Assist integration for DND mode

Privacy Notice
All data processing occurs locally on your device. No personal data is collected or transmitted to external servers. You can clear all history at any time through the app interface.

Limitations
Requires a webcam for facial recognition features

Currently optimized for Windows systems

Mood detection is based on simulated analysis (proof-of-concept)

Future Enhancements
More sophisticated emotion detection

Cross-platform compatibility improvements

Additional environmental controls

Screenshots
(Would include app interface images here)

License
This project was created for educational/hackathon purposes and is not currently licensed for commercial use.
