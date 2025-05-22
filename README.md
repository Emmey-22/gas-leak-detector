 # 🧪 Gas Leak Detector (Flask + Twilio)

A simple web-based gas leak detection system simulation using Flask, with alert functionality via SMS using Twilio. Built for lab practice, this project demonstrates IoT concepts, real-time alerting, and basic threshold management.

## 🚀 Features

- ✅ Simulated gas leak detection
- ✅ Configurable gas level threshold
- ✅ Email/SMS alert system using Twilio
- ✅ Alert history with timestamp
- ✅ Reset and manual test options
- ✅ Clean, responsive UI with alerts

## ⚙️ Tech Stack

- Python 3.x
- Flask
- Twilio API
- HTML/CSS + JavaScript
- `python-dotenv` for secret management

## 🔐 Environment Variables

Create a `.env` file in the root of your project with the following:

TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
DESTINATION_PHONE_NUMBER=+234xxxxxxxxxx


> **⚠️ Keep your `.env` file private. It's already in `.gitignore`.**

## 🛠️ Installation

```bash
git clone https://github.com/Emmey-22/gas-leak-detector.git
cd gas-leak-detector
pip install -r requirements.txt
