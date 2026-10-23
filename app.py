import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
from datetime import datetime

import speech_recognition as sr
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.units import cm
from xml.sax.saxutils import escape


class EnglishVoiceTranscriber:
    def __init__(self, root):
        self.root = root
        self.root.title("English Voice Transcriber")
        self.root.geometry("900x680")
        self.root.minsize(700, 520)
        self.root.configure(bg="#20242b")

        self.recognizer = sr.Recognizer()
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.listening = False
        self.sentences = []
        self.microphone = None
        self.listener_thread = None
        self.worker_thread = None

        self._configure_styles()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "TButton",
            font=("Segoe UI", 12, "bold"),
            padding=(12, 9),
            background="#267eeb",
            foreground="white",
            borderwidth=0
        )
        style.map("TButton", background=[("active", "#1765c1"), ("disabled", "#555b66")])
        style.configure(
            "TLabel",
            background="#20242b",
            foreground="#f3f5f7",
            font=("Segoe UI", 11)
        )

    def _build_ui(self):
        header = tk.Frame(self.root, bg="#20242b")
        header.pack(fill="x", padx=22, pady=(20, 8))

        tk.Label(
            header, text="ENGLISH VOICE TRANSCRIBER",
            bg="#20242b", fg="#55a6ff",
            font=("Segoe UI", 21, "bold")
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Speak in English. Each recognized phrase will appear on its own line.",
            bg="#20242b", fg="#d4d8de",
            font=("Segoe UI", 11)
        ).pack(anchor="w", pady=(5, 0))

        controls = tk.Frame(self.root, bg="#20242b")
        controls.pack(fill="x", padx=22, pady=12)

        self.start_button = ttk.Button(controls, text="🎙 Start listening", command=self.start_listening)
        self.start_button.pack(side="left", padx=(0, 8))

        self.stop_button = ttk.Button(controls, text="■ Stop", command=self.stop_listening, state="disabled")
        self.stop_button.pack(side="left", padx=8)

        self.txt_button = ttk.Button(controls, text="Save as TXT", command=self.save_txt)
        self.txt_button.pack(side="left", padx=8)

        self.pdf_button = ttk.Button(controls, text="Save as PDF", command=self.save_pdf)
        self.pdf_button.pack(side="left", padx=8)

        self.clear_button = ttk.Button(controls, text="Clear", command=self.clear_text)
        self.clear_button.pack(side="left", padx=8)

        self.status_var = tk.StringVar(value="Ready. Select Start listening and speak in English.")
        tk.Label(
            self.root, textvariable=self.status_var,
            bg="#2b3039", fg="#b9d8ff",
            font=("Segoe UI", 10), anchor="w", padx=12, pady=10
        ).pack(fill="x", padx=22, pady=(2, 10))

        content = tk.Frame(self.root, bg="#20242b")
        content.pack(fill="both", expand=True, padx=22, pady=(0, 18))

        tk.Label(
            content, text="TRANSCRIPT — ONE PHRASE PER LINE",
            bg="#20242b", fg="#f3f5f7",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 8))

        text_frame = tk.Frame(content, bg="#12161c")
        text_frame.pack(fill="both", expand=True)

        self.transcript = tk.Text(
            text_frame,
            wrap="word",
            font=("Segoe UI", 15),
            bg="#12161c",
            fg="#f5f7fa",
            insertbackground="white",
            selectbackground="#267eeb",
            relief="flat",
            padx=16,
            pady=14,
            spacing1=4,
            spacing3=8,
            undo=True
        )
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.transcript.yview)
        self.transcript.configure(yscrollcommand=scrollbar.set)
        self.transcript.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Label(
            self.root,
            text="Note: English speech recognition uses an internet connection. Check the transcript before exporting.",
            bg="#20242b", fg="#aab2bd",
            font=("Segoe UI", 9)
        ).pack(anchor="w", padx=22, pady=(0, 14))

    def start_listening(self):
        if self.listening:
            return
        try:
            self.microphone = sr.Microphone()
        except Exception as exc:
            messagebox.showerror(
                "Microphone error",
                "Could not access a microphone.\n\nCheck that a microphone is connected and that Windows allows desktop apps to use it.\n\nDetails: " + str(exc)
            )
            return

        self.stop_event.clear()
        self.audio_queue = queue.Queue()
        self.listening = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_var.set("Listening… Speak in English. Pause briefly between phrases.")

        self.listener_thread = threading.Thread(target=self._capture_audio, daemon=True)
        self.worker_thread = threading.Thread(target=self._recognize_audio, daemon=True)
        self.listener_thread.start()
        self.worker_thread.start()

    def _capture_audio(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.7)
                while not self.stop_event.is_set():
                    try:
                        audio = self.recognizer.listen(
                            source, timeout=1, phrase_time_limit=12
                        )
                        self.audio_queue.put(audio)
                    except sr.WaitTimeoutError:
                        continue
        except Exception as exc:
            self.root.after(0, lambda error=str(exc): self._show_capture_error(error))
        finally:
            self.audio_queue.put(None)

    def _show_capture_error(self, error):
        self.status_var.set("Microphone error.")
        messagebox.showerror("Microphone error", error)

    def _recognize_audio(self):
        while True:
            audio = self.audio_queue.get()
            if audio is None:
                break
            try:
                # English recognition. Google service requires internet access.
                result = self.recognizer.recognize_google(audio, language="en-US")
                result = " ".join(result.strip().split())
                if result:
                    # Each recognition segment is inserted as its own separate line.
                    self.root.after(0, lambda phrase=result: self.add_phrase(phrase))
            except sr.UnknownValueError:
                self.root.after(0, lambda: self.status_var.set("I couldn't understand that segment. Please repeat it."))
            except sr.RequestError as exc:
                self.root.after(0, lambda error=str(exc): self._show_network_error(error))
            except Exception as exc:
                self.root.after(0, lambda error=str(exc): self.status_var.set("Recognition error: " + error))

        self.root.after(0, self._listening_finished)

    def _show_network_error(self, error):
        self.status_var.set("Speech recognition service unavailable. Check your internet connection.")
        messagebox.showerror(
            "Speech recognition unavailable",
            "Could not contact the speech recognition service. Check your internet connection and try again.\n\nDetails: " + error
        )

    def add_phrase(self, phrase):
        self.sentences.append(phrase)
        self.transcript.insert("end", phrase + "\n")
        self.transcript.see("end")
        self.status_var.set(f"Listening… {len(self.sentences)} phrase(s) captured.")

    def stop_listening(self):
        if not self.listening:
            return
        self.stop_event.set()
        self.status_var.set("Stopping microphone…")
        self.stop_button.configure(state="disabled")

    def _listening_finished(self):
        self.listening = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        if self.sentences:
            self.status_var.set(f"Stopped. {len(self.sentences)} phrase(s) in the transcript.")
        else:
            self.status_var.set("Stopped. No phrases recognized yet.")

    def get_transcript(self):
        return self.transcript.get("1.0", "end-1c").strip()

    def save_txt(self):
        content = self.get_transcript()
        if not content:
            messagebox.showinfo("Nothing to save", "Record or enter some phrases first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save transcript as TXT",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"english_transcript_{datetime.now():%Y%m%d_%H%M}.txt"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as file:
                # Preserve one phrase per line.
                file.write(content + "\n")
            self.status_var.set("TXT file saved successfully.")
            messagebox.showinfo("Saved", f"Transcript saved to:\n{path}")
        except OSError as exc:
            messagebox.showerror("Save error", str(exc))

    def save_pdf(self):
        lines = self.get_transcript().splitlines()
        lines = [line.strip() for line in lines if line.strip()]
        if not lines:
            messagebox.showinfo("Nothing to save", "Record or enter some phrases first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save transcript as PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"english_transcript_{datetime.now():%Y%m%d_%H%M}.pdf"
        )
        if not path:
            return
        try:
            doc = SimpleDocTemplate(
                path, pagesize=A4,
                rightMargin=2 * cm, leftMargin=2 * cm,
                topMargin=2 * cm, bottomMargin=2 * cm
            )
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "TranscriptTitle", parent=styles["Title"],
                fontName="Helvetica-Bold", fontSize=16,
                leading=20, textColor=colors.HexColor("#1765c1"),
                alignment=TA_LEFT, spaceAfter=16
            )
            phrase_style = ParagraphStyle(
                "Phrase", parent=styles["BodyText"],
                fontName="Helvetica", fontSize=12,
                leading=17, spaceAfter=9
            )
            story = [
                Paragraph("English Voice Transcript", title_style),
                Paragraph(
                    f"Created: {datetime.now():%Y-%m-%d %H:%M}",
                    styles["Italic"]
                ),
                Spacer(1, 12)
            ]
            # One Paragraph per phrase guarantees each phrase is on its own line/block.
            for line in lines:
                story.append(Paragraph(escape(line), phrase_style))
            doc.build(story)
            self.status_var.set("PDF file saved successfully.")
            messagebox.showinfo("Saved", f"Transcript saved to:\n{path}")
        except Exception as exc:
            messagebox.showerror("PDF error", str(exc))

    def clear_text(self):
        if self.listening:
            messagebox.showwarning("Still listening", "Stop listening before clearing the transcript.")
            return
        if self.get_transcript() and not messagebox.askyesno("Clear transcript", "Delete all phrases from the transcript?"):
            return
        self.sentences.clear()
        self.transcript.delete("1.0", "end")
        self.status_var.set("Transcript cleared.")

    def close_app(self):
        if self.listening:
            self.stop_event.set()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = EnglishVoiceTranscriber(root)
    root.mainloop()
