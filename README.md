# 🤖 April - Personal AI Assistant

## Overview
April is a fully local, privacy-focused AI desktop assistant for Windows with voice control, wake word detection, intelligent responses, system automation, and more. **Powered by Ollama with Gemma models** - runs completely offline with no API keys needed!

## Quick Start

### Installation
1. **Run the installer:**
   ```batch
   install_april.bat
   ```
   Or manually install dependencies:
   ```batch
   pip install -r requirements.txt
   ```

2. **Install Ollama (for AI chat):**
   - Download from [ollama.com](https://ollama.com)
   - Run: `ollama pull gemma3:1b`
   - try to install leess billion and smart ai locally model for fatser model 

3. **Start April:**
   ```batch
   python april.py
   ```

4. **Start minimized (background mode):**
   ```batch
   python april.py --minimized
   ```

## Features

### 🧠 Intelligent Responses (NEW!)
- **Safe Math Calculator:** "sqrt(144)", "factorial(5)", "sin(pi/2)"
- **Unit Conversions:** "100 kg to lbs", "30°C to fahrenheit", "50 miles to km"
- **Web Search:** "search python tutorials" (uses DuckDuckGo - no API!)
- **Word Definitions:** "define algorithm"
- **System Status:** "system status", "cpu usage", "memory usage"
- **Top Processes:** "what's using memory"
- **Network Info:** "my ip address"

### 🎤 Voice Control
- **Wake Word:** Say "Hey April" to activate
- Voice commands for all features
- Text-to-speech responses
- Voice profile security

### 💬 AI Chat (Ollama + Gemma)
- Local AI - runs on your machine, no internet needed!
- Ask anything: "explain quantum computing"
- Context-aware conversations
- No API keys required

### 🖥️ Application Control
- **Open ANY app:** "open chrome", "open photoshop", "open spotify"
- **Close ANY app:** "close notepad", "close discord"
- Smart detection: Start Menu, Program Files, Windows Search

### 🌐 Web Browsing
- "Open YouTube" / "Open Google"
- "Search for Python tutorials"
- Supports any website

### 📊 Market Data
- Real-time stock prices: "Stock AAPL"
- Cryptocurrency: "Bitcoin price"
- Trend analysis with trading suggestions
- Historical data logging

### 🌤️ Weather (FREE - No API!)
- "Weather in New York"
- Uses wttr.in - no API key needed!
- Daily forecasts

### 📁 File Management
- "Organize my files" - Auto-sorts by type
- "Clean junk files" - Removes temp files
- "Find large files" - Over 100MB
- "Find duplicates" - Same filenames
- Organizes into Videos, Music, Pictures, Documents, Archives, Code

### 💻 System Control
- "Shutdown my laptop"
- "Restart"
- "Lock screen"
- "Volume up/down"
- "Brightness 50"
- "System status" - CPU, RAM, Disk, Battery
- "What's using memory" - Top processes

### 📸 Screen Capture
- "Take a screenshot"
- Screen recording capability
- Saved to Pictures/April Screenshots

### 🎮 Gaming
- "Play Angry Birds"
- Custom game paths in settings
- Steam integration

### ⏰ Task Scheduler
- "Remind me to call mom at 5pm"
- Recurring reminders
- Daily summaries

### 📞 WhatsApp Handling
- Monitors for incoming calls
- Asks "Are you okay, Sai?"
- Auto-responds if busy
- Logs all calls

### 🔒 Security & Privacy
- All data stored locally
- AES encryption for sensitive data
- Voice profile authentication
- No cloud sync
- Safe code sandbox

## Commands Reference

| Command | Action |
|---------|--------|
| **Intelligence** | |
| "what is 5 + 3" | Math calculation |
| "sqrt(144)" | Advanced math functions |
| "100 kg to lbs" | Unit conversion |
| "define [word]" | Word definition |
| "search [query]" | Web search (DuckDuckGo) |
| "system status" | System health |
| "cpu usage" | CPU percentage |
| "memory usage" | RAM status |
| **Apps & System** | |
| "open [any app]" | Open application |
| "close [any app]" | Close application |
| "lock" | Lock screen |
| "shutdown" | Shutdown PC |
| "volume up/down" | Adjust volume |
| **Web & Data** | |
| "open YouTube" | Open website |
| "stock AAPL" | Stock price |
| "weather" | Current weather |
| **Files** | |
| "organize files" | Sort downloads |
| "clean junk" | Remove temp files |
| "screenshot" | Capture screen |
| **Misc** | |
| "tell me a joke" | Random joke |
| "tell me a fact" | Random fact |
| "help" | Show commands |

## Settings

Access settings via the ⚙️ button or say "Open settings"

### AI Configuration
- **Ollama (Recommended):** Runs locally, unlimited, free
- **Gemini API:** Optional fallback

### Preferences
- Default city for weather
- Start with Windows
- Enable/disable wake word
- Voice profile setup

## System Tray

April runs in the system tray when minimized:
- Click tray icon to show
- Right-click for menu
- Enable "Start with Windows"

## Logs

Logs are stored in: `~/.april/logs/`

## Database

Encrypted SQLite database in: `~/.april/april.db`

Stores:
- Command history
- Market data
- Preferences
- Call logs
- Feedback ratings

## Troubleshooting

### Ollama not detected
1. Download from [ollama.com](https://ollama.com)
2. Install and run Ollama
3. Run: `ollama pull gemma3:4b`
4. Restart April

### Microphone not working
1. Check Windows microphone permissions
2. Ensure PyAudio is installed correctly
3. Try: `pip install pipwin && pipwin install pyaudio`

### System status shows limited info
- Install psutil: `pip install psutil`
- This enables CPU, RAM, Disk monitoring

### Voice not recognized
- Speak clearly and directly
- Reduce background noise
- Say "Hey April" to activate

## License
Personal use only. Created for Sai.

---
Made with ❤️ by April
