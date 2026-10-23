# English Voice Transcriber (Windows)

A Python desktop app that listens to English speech through your microphone and places each recognized speech segment on its own separate line. You can export the transcript as TXT or PDF.
# enlace al video 
https://youtu.be/9_2hL3oFRCw

## 1. Requirements

- Windows 10/11
- Python 3.10 or newer
- Microphone
- Internet connection (Google speech recognition is used)

## 2. Install

Open Command Prompt or the VS Code terminal in this folder and run:



If `pip install PyAudio` fails, first try:

```powershell
python -m pip install pipwin
pipwin install pyaudio
```

If `pipwin` does not work with your Python version, install a compatible PyAudio wheel or use a Python version supported by PyAudio.

## 3. Run

```powershell
python app.py
```

Click **Start listening**, speak in English, and pause briefly between phrases. Click **Stop** when finished. Each recognized segment is inserted on a separate line. Choose **Save as TXT** or **Save as PDF** to export.

## Important notes

- Recognition is set to US English (`en-US`). To use another English accent/locale, change `language="en-US"` in `app.py`, for example to `en-GB`.
- Google recognition requires internet and sends audio to Google's recognition service. Do not use it for confidential conversations.
- The system determines phrase boundaries from pauses and audio segments; it cannot always infer punctuation or sentence boundaries perfectly. Pause briefly between complete phrases and review the transcript before exporting.
- This first version is not fully hands-free because the buttons use the mouse. Voice commands can be added as a next step.
