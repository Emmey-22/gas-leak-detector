import random
import tkinter as tk
from tkinter import messagebox
import time
import csv
import os
import winsound
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv
load_dotenv(dotenv_path="gas.env")

# Environment variables (Twilio parts removed, SMS alert method still present but won't be called)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
TO_PHONE_NUMBER = os.getenv("TO_PHONE_NUMBER")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL") or "temitopeaina2003@gmail.com"
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD") or "azjoftxiijwtvmfq"
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL") or "ainaemmanuel078@gmail.com"

THRESHOLD = 300  # default PPM threshold
LOG_FILE = "gas_log.csv"
MAX_POINTS = 20

BG_COLOR = "#f0f4f8"
SAFE_COLOR = "#2e7d32"
LEAK_COLOR = "#c62828"
BUTTON_COLOR = "#1976d2"
BUTTON_HOVER_COLOR = "#1565c0"
FONT_NAME = "Segoe UI"

class GasLeakDetectorApp:
    def __init__(self, root):
        self.root = root
        root.title("Gas Leak Detector")
        root.configure(bg=BG_COLOR)
        self.center_window(700, 650)

        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Time", "Gas Level (PPM)", "Status"])

        self.gas_levels = deque(maxlen=MAX_POINTS)
        self.timestamps = deque(maxlen=MAX_POINTS)
        self.mode = tk.StringVar(value="auto")

        # Labels
        self.gas_level_label = tk.Label(root, text="Gas Level: -- PPM", font=(FONT_NAME, 28, "bold"), bg=BG_COLOR)
        self.gas_level_label.pack(pady=(30, 10))

        self.status_label = tk.Label(root, text="Status: --", font=(FONT_NAME, 28, "bold"), bg=BG_COLOR)
        self.status_label.pack(pady=(0, 20))

        # Mode selector
        mode_frame = tk.Frame(root, bg=BG_COLOR)
        mode_frame.pack(pady=10)

        tk.Radiobutton(mode_frame, text="Auto Mode", variable=self.mode, value="auto",
                       command=self.mode_changed, font=(FONT_NAME, 14), bg=BG_COLOR,
                       activebackground=BG_COLOR).pack(side="left", padx=20)

        tk.Radiobutton(mode_frame, text="Manual Mode", variable=self.mode, value="manual",
                       command=self.mode_changed, font=(FONT_NAME, 14), bg=BG_COLOR,
                       activebackground=BG_COLOR).pack(side="left", padx=20)

        # Manual mode input
        self.manual_frame = tk.Frame(root, bg=BG_COLOR)
        self.manual_entry = tk.Entry(self.manual_frame, font=(FONT_NAME, 18), width=12, bd=2, relief="groove")
        self.manual_entry.pack(side="left", padx=(0, 10), pady=10)

        self.manual_button = tk.Button(self.manual_frame, text="Set Gas Level", font=(FONT_NAME, 14, "bold"),
                                       bg=BUTTON_COLOR, fg="white", activebackground=BUTTON_HOVER_COLOR,
                                       activeforeground="white", bd=0, padx=15, pady=8,
                                       command=self.manual_update)
        self.manual_button.pack(side="left", pady=10)

        self.manual_frame.pack_forget()

        # Threshold input UI
        threshold_frame = tk.Frame(root, bg=BG_COLOR)
        threshold_frame.pack(pady=(5, 10))

        tk.Label(threshold_frame, text="Danger Threshold (PPM):", font=(FONT_NAME, 12), bg=BG_COLOR).pack(side="left")

        self.threshold_var = tk.StringVar(value=str(THRESHOLD))
        self.threshold_entry = tk.Entry(threshold_frame, textvariable=self.threshold_var, font=(FONT_NAME, 12), width=8, bd=2, relief="groove")
        self.threshold_entry.pack(side="left", padx=5)

        self.threshold_button = tk.Button(threshold_frame, text="Set Threshold", font=(FONT_NAME, 12, "bold"),
                                          bg=BUTTON_COLOR, fg="white", activebackground=BUTTON_HOVER_COLOR,
                                          activeforeground="white", bd=0, padx=10, pady=4,
                                          command=self.update_threshold)
        self.threshold_button.pack(side="left", padx=10)

        # Reset button UI
        reset_button = tk.Button(root, text="Reset Data & Graph", font=(FONT_NAME, 12, "bold"),
                                 bg="#e53935", fg="white", activebackground="#b71c1c",
                                 activeforeground="white", bd=0, padx=15, pady=8,
                                 command=self.reset_data)
        reset_button.pack(pady=(0, 20))

        # Plotting setup
        self.fig, self.ax = plt.subplots(figsize=(6, 3))
        self.line, = self.ax.plot([], [], label="Gas Level (PPM)", color="#1976d2", linewidth=2)
        self.threshold_line = self.ax.axhline(y=THRESHOLD, color=LEAK_COLOR, linestyle='--', label="Danger Threshold")
        self.ax.set_ylim(0, 600)
        self.ax.set_xlabel("Time", fontsize=12, fontname=FONT_NAME)
        self.ax.set_ylabel("PPM", fontsize=12, fontname=FONT_NAME)
        self.ax.set_title("Gas Level Over Time", fontsize=14, fontname=FONT_NAME, weight='bold')
        self.ax.legend()
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(pady=20)

        self.update_gas_level()

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def mode_changed(self):
        if self.mode.get() == "manual":
            self.manual_frame.pack(pady=10)
        else:
            self.manual_frame.pack_forget()
            self.update_gas_level()

    def update_gas_level(self):
        if self.mode.get() == "auto":
            gas_level = random.uniform(100, 500)
            self.process_gas_level(gas_level)
            self.root.after(2000, self.update_gas_level)

    def manual_update(self):
        value = self.manual_entry.get()
        try:
            gas_level = float(value)
            if gas_level < 0:
                raise ValueError("Gas level cannot be negative.")
            self.process_gas_level(gas_level)
        except ValueError as e:
            messagebox.showerror("Invalid input", f"Please enter a valid non-negative number.\nError: {e}")

    def process_gas_level(self, gas_level):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        status = "Leak Detected" if gas_level > THRESHOLD else "Safe"

        self.gas_level_label.config(text=f"Gas Level: {gas_level:.2f} PPM")

        if gas_level >= 700:
            winsound.Beep(1200, 700)
            self.status_label.config(text="Status: Leak Detected", fg="red")
            messagebox.showwarning(
                "Gas Leak Detected",
                f"Warning! Gas level is {gas_level:.2f} PPM.\nImmediate action recommended."
            )

        if status == "Leak Detected":
            self.status_label.config(text="⚠️ Leak Detected!", fg=LEAK_COLOR)

            alert_msg = f"⚠️ Gas leak detected!\nLevel: {gas_level:.2f} PPM\nTime: {timestamp}"

            # SMS alert removed from being called here

            # Send Email alert
            self.send_email_alert("Gas Leak Detected!", alert_msg)
        else:
            self.status_label.config(text="✅ Safe", fg=SAFE_COLOR)

        # Log to CSV file
        with open(LOG_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, f"{gas_level:.2f}", status])

        # Update graph
        self.gas_levels.append(gas_level)
        self.timestamps.append(timestamp[-8:])
        self.line.set_data(range(len(self.gas_levels)), list(self.gas_levels))
        self.ax.set_xticks(range(len(self.timestamps)))
        self.ax.set_xticklabels(list(self.timestamps), rotation=45, ha='right')
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()

    def update_threshold(self):
        value = self.threshold_var.get()
        try:
            new_threshold = float(value)
            if new_threshold <= 0:
                raise ValueError("Threshold must be positive.")
            global THRESHOLD
            THRESHOLD = new_threshold

            # Update threshold line on plot
            self.threshold_line.set_ydata([THRESHOLD, THRESHOLD])
            self.canvas.draw_idle()

            messagebox.showinfo("Threshold Updated", f"Threshold set to {THRESHOLD} PPM.")
        except ValueError as e:
            messagebox.showerror("Invalid input", f"Please enter a valid positive number.\nError: {e}")

    def reset_data(self):
        # Clear CSV log file (overwrite with header)
        with open(LOG_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Time", "Gas Level (PPM)", "Status"])

        # Clear data lists
        self.gas_levels.clear()
        self.timestamps.clear()

        # Reset graph
        self.line.set_data([], [])
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()

        # Reset labels
        self.gas_level_label.config(text="Gas Level: -- PPM")
        self.status_label.config(text="Status: --", fg="black")

        messagebox.showinfo("Reset", "Data and graph have been reset.")

    def send_email_alert(self, subject, body):
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
            server.quit()
            print("Email alert sent.")
        except Exception as e:
            print(f"Failed to send email: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GasLeakDetectorApp(root)
    root.mainloop()
