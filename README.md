# April - Personal AI Assistant

April is a local AI assistant for Windows. It can understand voice commands, answer questions, control your PC, open apps, manage files, and perform other everyday tasks.

April can run AI models locally using Ollama, so you do not need an API key for normal AI conversations.

## Getting Started

### 1. Install April

Run:

```batch
install_april.bat
```

Or install the dependencies manually:

```batch
pip install -r requirements.txt
```

### 2. Install Ollama

Install Ollama and download a small local model:

```batch
ollama pull gemma3:1b
```

For faster performance, use a smaller model that works well on your PC.

### 3. Start April

```batch
python april.py
```

To start April in the background:

```batch
python april.py --minimized
```

## Features

### AI Chat

* Runs AI locally with Ollama
* No API key required
* Works without cloud AI
* Supports normal conversations and questions
* Keeps conversation context

Example:

```text
Explain quantum computing
```

### Voice Control

* Say **Hey April** to activate
* Control April using your voice
* Text-to-speech responses
* Optional voice profile

### Math and Conversions

April can handle simple calculations and conversions.

Examples:

```text
What is 5 + 3
sqrt(144)
factorial(5)
100 kg to lbs
30°C to fahrenheit
50 miles to km
```

### Web Search

You can search the web using simple commands.

```text
Search Python tutorials
Search latest technology news
```

### Application Control

Open or close applications using voice or text.

```text
Open Chrome
Open Spotify
Open Photoshop
Close Notepad
Close Discord
```

April can search common Windows application locations to find installed programs.

### Website Access

Open websites directly:

```text
Open YouTube
Open Google
Open GitHub
```

### System Information

Check your computer status:

```text
System status
CPU usage
Memory usage
What's using memory
```

April can show information such as:

* CPU usage
* RAM usage
* Disk usage
* Battery status
* Running processes

### Weather

Check the weather without an API key.

```text
Weather in New York
Weather today
```

April uses wttr.in for weather information.

### File Management

April can help manage files on your computer.

```text
Organize my files
Clean junk files
Find large files
Find duplicate files
```

Files can be organized into folders such as:

* Documents
* Pictures
* Videos
* Music
* Archives
* Code

### System Control

Control basic Windows functions:

```text
Shutdown
Restart
Lock screen
Volume up
Volume down
Brightness 50
```

### Screenshots

Take screenshots using a command:

```text
Take a screenshot
```

Screenshots are saved in:

```text
Pictures/April Screenshots
```

### Gaming

April can launch games and applications.

```text
Play Angry Birds
Open Steam
```

Game paths can be configured in the settings.

### Reminders

Create reminders using natural commands:

```text
Remind me to call mom at 5pm
```

April can also support recurring reminders.

### Market Data

Check stock and cryptocurrency information:

```text
Stock AAPL
Bitcoin price
```

Historical data can also be stored locally.

## Common Commands

| Command                   | Action                  |
| ------------------------- | ----------------------- |
| `what is 5 + 3`           | Calculate               |
| `sqrt(144)`               | Advanced calculation    |
| `100 kg to lbs`           | Unit conversion         |
| `define algorithm`        | Word definition         |
| `search Python tutorials` | Web search              |
| `system status`           | System information      |
| `cpu usage`               | CPU usage               |
| `memory usage`            | RAM usage               |
| `open Chrome`             | Open an application     |
| `close Discord`           | Close an application    |
| `lock`                    | Lock Windows            |
| `shutdown`                | Shut down the PC        |
| `volume up`               | Increase volume         |
| `volume down`             | Decrease volume         |
| `open YouTube`            | Open a website          |
| `stock AAPL`              | Check stock price       |
| `weather`                 | Check weather           |
| `organize files`          | Organize files          |
| `clean junk`              | Clean temporary files   |
| `screenshot`              | Take a screenshot       |
| `tell me a joke`          | Tell a joke             |
| `tell me a fact`          | Tell a fact             |
| `help`                    | Show available commands |

## Settings

Open settings by clicking the settings button or saying:

```text
Open settings
```

You can configure:

* Ollama model
* Optional Gemini API
* Default weather location
* Start with Windows
* Wake word
* Voice settings
* Other April preferences

## System Tray

When April is minimized it can run from the Windows system tray.

From the tray you can:

* Open April
* Hide April
* Open settings
* Exit April
* Enable startup with Windows

## Privacy

April is designed to keep your data on your computer.

* Local AI through Ollama
* Local database
* Local logs
* No required cloud AI API
* No required API key
* Sensitive information can be encrypted

Some features such as web search, weather, and market data require an internet connection.

## Files and Data

April stores its local data in:

```text
~/.april/
```

Logs:

```text
~/.april/logs/
```

Database:

```text
~/.april/april.db
```

The database can contain:

* Command history
* Preferences
* Market data
* Feedback
* Other April settings

## Troubleshooting

### Ollama is not detected

Make sure Ollama is installed and running.

Then run:

```batch
ollama pull gemma3:1b
```

Restart April after installing the model.

### Microphone is not working

Check:

1. Windows microphone permissions
2. Your microphone connection
3. PyAudio installation

Try:

```batch
pip install pipwin
pipwin install pyaudio
```

### System information is missing

Install psutil:

```batch
pip install psutil
```

### Voice recognition is not working

Try speaking clearly and reduce background noise.

You can also say:

```text
Hey April
```

to activate the assistant.

## License

Personal use only.

Created for Sai.

---

Made with April
