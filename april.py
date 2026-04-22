"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                              APRIL - Personal AI Assistant                      ║
║                         Voice-Controlled Desktop Assistant for Windows          ║
║                                    Version 1.0.0                                ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Author: Created for Sai
Features: Voice control, Wake word detection, Market data, System control,
          WhatsApp handling, File management, Weather, Screen capture, and more.
"""

import os
import sys
import json
import time
import random
import sqlite3
import hashlib
import logging
import threading
import subprocess
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
import base64
import re

# Hide console window on Windows
if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

APP_NAME = "April"
APP_VERSION = "1.0.0"
WAKE_WORD = "hey april"
USER_NAME = "Sai"

# Paths
USER_HOME = Path.home()
APP_DATA_DIR = USER_HOME / ".april"
DATABASE_PATH = APP_DATA_DIR / "april.db"
LOG_PATH = APP_DATA_DIR / "logs" / "april.log"
CONFIG_PATH = APP_DATA_DIR / "config.json"
VOICE_PROFILE_PATH = APP_DATA_DIR / "voice_profile.dat"

# Default folders for file organization
DEFAULT_FOLDERS: Dict[str, List[str]] = {
    'Videos': ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm'],
    'Music': ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a'],
    'Pictures': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico'],
    'Documents': ['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'ppt', 'pptx', 'odt'],
    'Downloads': []  # Default for unrecognized files
}

# Junk file patterns
JUNK_PATTERNS = ['*.tmp', '*.temp', '~*', '*.bak', 'Thumbs.db', 'desktop.ini', '*.log']

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS CHECK AND AUTO-INSTALL
# ═══════════════════════════════════════════════════════════════════════════════

def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    required_packages: Dict[str, str] = {
        'speech_recognition': 'SpeechRecognition',
        'pyttsx3': 'pyttsx3',
        'PIL': 'Pillow',
        'pystray': 'pystray',
        'cryptography': 'cryptography',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'requests': 'requests',
        'pyautogui': 'pyautogui',
        'mss': 'mss',
        'cv2': 'opencv-python',
        'schedule': 'schedule',
        'yfinance': 'yfinance',
    }
    
    missing: List[str] = []
    for module, package in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("\n" + "="*60)
        print("  MISSING DEPENDENCIES - Please run install_april.bat first!")
        print("="*60)
        print(f"\nMissing packages: {', '.join(missing)}")
        print("\nTo install, double-click: install_april.bat")
        print("Or run in Command Prompt:")
        print(f"  pip install {' '.join(missing)}")
        print("\n" + "="*60)
        input("\nPress Enter to exit...")
        return False
    return True

# Check dependencies before importing
if not check_dependencies():
    sys.exit(0)

# Now import all dependencies
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import speech_recognition as sr  # type: ignore
import pyttsx3  # type: ignore
from PIL import Image, ImageDraw, ImageTk  # type: ignore
import pystray  # type: ignore
from cryptography.fernet import Fernet  # type: ignore
from cryptography.hazmat.primitives import hashes  # type: ignore
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # type: ignore
import pandas as pd  # type: ignore
import numpy as np  # type: ignore
import requests  # type: ignore
import pyautogui  # type: ignore
import mss  # type: ignore
import cv2  # type: ignore
import schedule  # type: ignore
import yfinance as yf  # type: ignore

# Windows-specific imports
try:
    import win32api  # type: ignore
    import win32con  # type: ignore
    import win32gui  # type: ignore
    WINDOWS_AVAILABLE = True
except ImportError:
    win32api = None  # type: ignore
    win32con = None  # type: ignore
    win32gui = None  # type: ignore
    WINDOWS_AVAILABLE = False
    print("Warning: pywin32 not available. Some system features will be limited.")

try:
    import screen_brightness_control as sbc  # type: ignore
    BRIGHTNESS_AVAILABLE = True
except ImportError:
    sbc = None  # type: ignore
    BRIGHTNESS_AVAILABLE = False

# Audio backend detection
AUDIO_BACKEND = None
try:
    import pyaudio  # type: ignore
    AUDIO_BACKEND = 'pyaudio'
except ImportError:
    try:
        import sounddevice  # type: ignore
        AUDIO_BACKEND = 'sounddevice'
    except ImportError:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING SETUP
# ═══════════════════════════════════════════════════════════════════════════════

class AprilLogger:
    """Custom logger for April with file and console output."""
    
    def __init__(self):
        self.log_dir = APP_DATA_DIR / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('April')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        file_handler = logging.FileHandler(
            self.log_dir / f"april_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, msg): self.logger.info(msg)
    def error(self, msg): self.logger.error(msg)
    def warning(self, msg): self.logger.warning(msg)
    def debug(self, msg): self.logger.debug(msg)

logger = AprilLogger()

# ═══════════════════════════════════════════════════════════════════════════════
# ENCRYPTION MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class EncryptionManager:
    """Handles encryption/decryption of sensitive data."""
    
    def __init__(self, password: str = "april_secure_key"):
        self.salt = b'april_salt_2024'
        self.key = self._derive_key(password)
        self.fernet = Fernet(self.key)
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt encrypted data."""
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return encrypted_data  # Return as-is if decryption fails

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class DatabaseManager:
    """Manages SQLite database with encryption support."""
    
    def __init__(self):
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.db_path = DATABASE_PATH
        self.encryption = EncryptionManager()
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """Initialize database and create tables."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        
        # Command history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                command TEXT NOT NULL,
                response TEXT,
                success INTEGER DEFAULT 1
            )
        ''')
        
        # Market data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                data_type TEXT NOT NULL,
                price REAL,
                change_percent REAL,
                volume REAL,
                raw_data TEXT
            )
        ''')
        
        # Trading suggestions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                suggestion TEXT NOT NULL,
                confidence REAL,
                actual_outcome TEXT,
                user_rating INTEGER
            )
        ''')
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                encrypted INTEGER DEFAULT 0
            )
        ''')
        
        # Call logs table (for WhatsApp)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS call_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                caller_name TEXT,
                caller_number TEXT,
                action_taken TEXT,
                call_duration INTEGER
            )
        ''')
        
        # Task scheduler table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                schedule_time TEXT,
                recurrence TEXT,
                command TEXT,
                active INTEGER DEFAULT 1,
                last_run TEXT
            )
        ''')
        
        # Feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                feature TEXT NOT NULL,
                rating INTEGER,
                comment TEXT
            )
        ''')
        
        # Voice profile table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                profile_data TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Daily summaries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                summary_type TEXT NOT NULL,
                content TEXT NOT NULL
            )
        ''')
        
        self.conn.commit()
        logger.info("Database initialized successfully")
    
    def log_command(self, command: str, response: str, success: bool = True):
        """Log a command and its response."""
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO command_history (timestamp, command, response, success) VALUES (?, ?, ?, ?)',
            (datetime.now().isoformat(), command, response, int(success))
        )
        self.conn.commit()
    
    def log_market_data(self, symbol: str, data_type: str, price: float, 
                        change_percent: float = 0, volume: float = 0, raw_data: dict = None):
        """Log market data."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO market_data (timestamp, symbol, data_type, price, change_percent, volume, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), symbol, data_type, price, change_percent, volume, 
              json.dumps(raw_data) if raw_data else None))
        self.conn.commit()
    
    def log_call(self, caller_name: str, caller_number: str, action: str, duration: int = 0):
        """Log a WhatsApp call."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO call_logs (timestamp, caller_name, caller_number, action_taken, call_duration)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), caller_name, caller_number, action, duration))
        self.conn.commit()
    
    def save_preference(self, key: str, value: str, encrypt: bool = False):
        """Save a user preference."""
        cursor = self.conn.cursor()
        stored_value = self.encryption.encrypt(value) if encrypt else value
        cursor.execute('''
            INSERT OR REPLACE INTO preferences (key, value, encrypted) VALUES (?, ?, ?)
        ''', (key, stored_value, int(encrypt)))
        self.conn.commit()
    
    def get_preference(self, key: str, default: str = None) -> Optional[str]:
        """Get a user preference."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT value, encrypted FROM preferences WHERE key = ?', (key,))
        row = cursor.fetchone()
        if row:
            return self.encryption.decrypt(row['value']) if row['encrypted'] else row['value']
        return default
    
    def log_feedback(self, feature: str, rating: int, comment: str = ""):
        """Log user feedback."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO feedback (timestamp, feature, rating, comment) VALUES (?, ?, ?, ?)
        ''', (datetime.now().isoformat(), feature, rating, comment))
        self.conn.commit()
    
    def get_command_history(self, limit: int = 50) -> List[Dict]:
        """Get recent command history."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM command_history ORDER BY timestamp DESC LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def search_commands(self, query: str) -> List[Dict]:
        """Search command history."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM command_history WHERE command LIKE ? ORDER BY timestamp DESC
        ''', (f'%{query}%',))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_market_history(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Get market data history for a symbol."""
        cursor = self.conn.cursor()
        since = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute('''
            SELECT * FROM market_data WHERE symbol = ? AND timestamp > ? ORDER BY timestamp
        ''', (symbol, since))
        rows = cursor.fetchall()
        return pd.DataFrame([dict(row) for row in rows])
    
    def add_scheduled_task(self, name: str, task_type: str, schedule_time: str, 
                          recurrence: str, command: str):
        """Add a scheduled task."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO scheduled_tasks (task_name, task_type, schedule_time, recurrence, command)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, task_type, schedule_time, recurrence, command))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_active_tasks(self) -> List[Dict]:
        """Get active scheduled tasks."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM scheduled_tasks WHERE active = 1')
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

# ═══════════════════════════════════════════════════════════════════════════════
# VOICE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class VoiceEngine:
    """Handles speech recognition and text-to-speech."""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self._configure_engine()
        self.is_listening = False
        self.microphone = None
        self.audio_backend = AUDIO_BACKEND
        self.silence_threshold = 500  # Default, can be calibrated
        
        # Recognizer settings for better accuracy
        self.recognizer.energy_threshold = 300  # Minimum audio energy for speech
        self.recognizer.dynamic_energy_threshold = True  # Auto-adjust
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 0.8  # Seconds of silence before phrase ends
        self.recognizer.phrase_threshold = 0.3  # Minimum seconds for valid phrase
        self.recognizer.non_speaking_duration = 0.5  # Seconds before speech starts
        
        self._init_microphone()
    
    def _configure_engine(self):
        """Configure TTS engine."""
        try:
            voices = self.engine.getProperty('voices')
            # Try to use a female voice for April
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
            self.engine.setProperty('rate', 175)  # Speed
            self.engine.setProperty('volume', 1.0)  # Full volume
            logger.info("TTS engine configured successfully")
        except Exception as e:
            logger.error(f"TTS configuration error: {e}")
    
    def _init_microphone(self):
        """Initialize microphone."""
        if self.audio_backend == 'pyaudio':
            try:
                self.microphone = sr.Microphone()
                with self.microphone as source:
                    # Longer ambient noise adjustment for better accuracy
                    self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                logger.info(f"Microphone initialized (PyAudio), energy_threshold={self.recognizer.energy_threshold}")
            except Exception as e:
                logger.warning(f"PyAudio microphone failed: {e}")
                self.microphone = None
        elif self.audio_backend == 'sounddevice':
            try:
                import sounddevice as sd
                import numpy as np
                
                # Check if we have input devices
                devices = sd.query_devices()
                has_input = any(d['max_input_channels'] > 0 for d in devices)
                
                if not has_input:
                    logger.warning("No input devices found")
                    self.microphone = None
                    return
                
                # Test if microphone actually works (Windows privacy check)
                try:
                    default_device = sd.default.device[0]
                    device_info = sd.query_devices(default_device)
                    sample_rate = int(device_info['default_samplerate'])
                    
                    # Quick test recording
                    test_audio = sd.rec(int(0.2 * sample_rate), samplerate=sample_rate, 
                                       channels=1, dtype='int16', blocking=True)
                    
                    if test_audio is not None and len(test_audio) > 0:
                        self.microphone = 'sounddevice'
                        logger.info(f"Microphone initialized (sounddevice, device {default_device})")
                    else:
                        logger.warning("Microphone test failed - no audio data")
                        self.microphone = None
                except Exception as e:
                    logger.warning(f"Microphone access denied or not working: {e}")
                    logger.warning("Check Windows Settings > Privacy > Microphone")
                    self.microphone = None
                    
            except Exception as e:
                logger.warning(f"Sounddevice init failed: {e}")
                self.microphone = None
        else:
            logger.warning("No audio backend available. Voice input disabled.")
            self.microphone = None
    
    def _init_tts_queue(self):
        """Initialize TTS queue for thread-safe speaking."""
        if not hasattr(self, '_tts_queue'):
            import queue
            self._tts_queue = queue.Queue()
            self._tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
            self._tts_thread.start()
    
    def _tts_worker(self):
        """Background worker that processes TTS queue."""
        while True:
            try:
                text = self._tts_queue.get()
                if text is None:  # Shutdown signal
                    break
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except RuntimeError as e:
                    logger.warning(f"TTS RuntimeError, reinitializing: {e}")
                    try:
                        self.engine = pyttsx3.init()
                        self._configure_engine()
                        self.engine.say(text)
                        self.engine.runAndWait()
                    except:
                        pass
                except Exception as e:
                    logger.error(f"TTS worker error: {e}")
                self._tts_queue.task_done()
            except Exception as e:
                logger.error(f"TTS queue error: {e}")
    
    def speak(self, text: str, callback: Callable = None):
        """Speak text using TTS (blocks until done)."""
        logger.info(f"April: {text}")
        try:
            self._init_tts_queue()
            self._tts_queue.put(text)
            self._tts_queue.join()  # Wait for speech to complete
            if callback:
                callback()
        except Exception as e:
            logger.error(f"TTS error: {e}")
    
    def speak_async(self, text: str):
        """Speak text asynchronously (non-blocking)."""
        logger.info(f"April: {text}")
        try:
            self._init_tts_queue()
            self._tts_queue.put(text)
        except Exception as e:
            logger.error(f"TTS async error: {e}")
    
    def listen(self, timeout: int = 8, phrase_limit: int = 15) -> Optional[str]:
        """Listen for voice input and return recognized text."""
        if not self.microphone:
            logger.warning("No microphone available")
            return None
        
        try:
            if self.audio_backend == 'sounddevice':
                import sounddevice as sd
                import tempfile
                import wave as wave_module
                import numpy as np
                
                # Use native sample rate of 44100 for most mics, then resample
                sample_rate = 44100
                target_rate = 16000  # Google Speech API prefers 16kHz
                
                # Record for the specified duration
                duration = min(phrase_limit, 6)  # Cap at 6 seconds for responsiveness
                
                logger.debug(f"Recording for {duration} seconds at {sample_rate}Hz...")
                
                try:
                    # Record audio
                    audio_data = sd.rec(int(duration * sample_rate), 
                                       samplerate=sample_rate, 
                                       channels=1, 
                                       dtype='int16',
                                       blocking=True)
                except Exception as e:
                    logger.error(f"Recording error: {e}")
                    return None
                
                # Check if we got any audio with content
                if audio_data is None or len(audio_data) == 0:
                    logger.debug("No audio recorded")
                    return None
                
                # Check max volume (peak detection is more reliable than average)
                max_volume = np.abs(audio_data).max()
                avg_volume = np.abs(audio_data).mean()
                logger.debug(f"Audio: avg={avg_volume:.0f}, max={max_volume}")
                
                # Only process if there's significant audio (peak > 500)
                if max_volume < 300:
                    logger.debug("Audio too quiet (no significant peaks)")
                    return None
                
                # Resample to 16kHz for speech recognition
                # Simple decimation - take every Nth sample
                resample_factor = sample_rate // target_rate
                audio_resampled = audio_data[::resample_factor]
                
                # Save to temp WAV file
                temp_path = None
                try:
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                        temp_path = f.name
                    
                    with wave_module.open(temp_path, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(target_rate)
                        wf.writeframes(audio_resampled.tobytes())
                    
                    # Use speech recognition on the file
                    with sr.AudioFile(temp_path) as source:
                        audio = self.recognizer.record(source)
                    
                    text = self.recognizer.recognize_google(audio)
                    logger.info(f"Recognized: {text}")
                    return text.lower()
                    
                finally:
                    # Clean up temp file
                    if temp_path and os.path.exists(temp_path):
                        try:
                            os.unlink(temp_path)
                        except:
                            pass
            else:
                # Use PyAudio microphone
                with self.microphone as source:
                    logger.debug("Listening with PyAudio...")
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
                
                text = self.recognizer.recognize_google(audio)
                logger.info(f"Recognized: {text}")
                return text.lower()
        
        except sr.WaitTimeoutError:
            logger.debug("Listen timeout")
            return None
        except sr.UnknownValueError:
            logger.debug("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Google Speech Recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Listen error: {e}")
            return None
    
    def listen_for_wake_word(self, callback: Callable) -> bool:
        """Listen specifically for the wake word."""
        text = self.listen(timeout=2, phrase_limit=3)
        if text and WAKE_WORD in text:
            callback()
            return True
        return False
    
    def calibrate_microphone(self) -> dict:
        """Calibrate microphone by measuring ambient noise level."""
        if self.audio_backend != 'sounddevice':
            return {'success': False, 'message': 'Calibration requires sounddevice backend'}
        
        try:
            import sounddevice as sd
            import numpy as np
            
            sample_rate = 16000
            duration = 2  # 2 seconds of ambient noise
            
            logger.info("Calibrating microphone - measuring ambient noise...")
            audio_data = sd.rec(int(duration * sample_rate), 
                               samplerate=sample_rate, 
                               channels=1, 
                               dtype='int16')
            sd.wait()
            
            # Calculate noise statistics
            noise_level = np.abs(audio_data).mean()
            noise_max = np.abs(audio_data).max()
            
            # Set threshold to 2x the average noise + some margin
            self.silence_threshold = int(noise_level * 2.5 + 100)
            
            logger.info(f"Calibration complete: noise={noise_level:.0f}, max={noise_max:.0f}, threshold={self.silence_threshold}")
            
            return {
                'success': True,
                'noise_level': int(noise_level),
                'noise_max': int(noise_max),
                'threshold': self.silence_threshold,
                'message': f'Calibrated! Noise level: {noise_level:.0f}, Threshold set to: {self.silence_threshold}'
            }
        except Exception as e:
            logger.error(f"Calibration error: {e}")
            return {'success': False, 'message': str(e)}
    
    def set_sensitivity(self, level: str) -> dict:
        """Set microphone sensitivity level.
        
        Args:
            level: 'low', 'medium', 'high', or 'very_high'
        """
        settings = {
            'low': {'energy': 400, 'pause': 1.0, 'phrase': 0.5},
            'medium': {'energy': 300, 'pause': 0.8, 'phrase': 0.3},
            'high': {'energy': 200, 'pause': 0.6, 'phrase': 0.2},
            'very_high': {'energy': 100, 'pause': 0.5, 'phrase': 0.1},
        }
        
        if level not in settings:
            return {'success': False, 'message': f'Invalid level. Use: {list(settings.keys())}'}
        
        s = settings[level]
        self.recognizer.energy_threshold = s['energy']
        self.recognizer.pause_threshold = s['pause']
        self.recognizer.phrase_threshold = s['phrase']
        
        logger.info(f"Sensitivity set to {level}: energy={s['energy']}, pause={s['pause']}")
        return {
            'success': True,
            'level': level,
            'energy_threshold': s['energy'],
            'message': f'Sensitivity set to {level}'
        }
    
    def recalibrate(self) -> dict:
        """Recalibrate microphone for current environment."""
        if self.audio_backend == 'pyaudio' and self.microphone:
            try:
                with self.microphone as source:
                    logger.info("Recalibrating microphone (stay quiet for 2 seconds)...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=2.0)
                logger.info(f"Recalibration complete, energy_threshold={self.recognizer.energy_threshold}")
                return {
                    'success': True,
                    'energy_threshold': int(self.recognizer.energy_threshold),
                    'message': f'Recalibrated! Energy threshold: {int(self.recognizer.energy_threshold)}'
                }
            except Exception as e:
                logger.error(f"Recalibration error: {e}")
                return {'success': False, 'message': str(e)}
        else:
            return self.calibrate_microphone()

# ═══════════════════════════════════════════════════════════════════════════════
# VOICE PROFILE MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class VoiceProfileManager:
    """Manages voice profile for security."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.profile_exists = self._check_profile()
    
    def _check_profile(self) -> bool:
        """Check if voice profile exists."""
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM voice_profile WHERE user_name = ?', (USER_NAME,))
        return cursor.fetchone() is not None
    
    def create_profile(self, voice_samples: List[str]) -> bool:
        """Create voice profile from samples (simplified version)."""
        # In a full implementation, this would analyze voice characteristics
        # For now, we store a hash of the samples
        profile_hash = hashlib.sha256(''.join(voice_samples).encode()).hexdigest()
        
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO voice_profile (user_name, profile_data, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (USER_NAME, profile_hash, datetime.now().isoformat(), datetime.now().isoformat()))
        self.db.conn.commit()
        self.profile_exists = True
        logger.info("Voice profile created")
        return True
    
    def verify_voice(self, sample: str) -> bool:
        """Verify voice matches profile (simplified)."""
        # In a full implementation, this would compare voice characteristics
        # For now, we just check if a profile exists
        return self.profile_exists

# ═══════════════════════════════════════════════════════════════════════════════
# WAKE WORD DETECTOR
# ═══════════════════════════════════════════════════════════════════════════════

class WakeWordDetector:
    """Detects wake word in background."""
    
    def __init__(self, voice_engine: VoiceEngine, on_wake: Callable):
        self.voice_engine = voice_engine
        self.on_wake = on_wake
        self.is_running = False
        self.is_processing = False  # Prevent concurrent processing
        self.thread = None
    
    def start(self):
        """Start wake word detection."""
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.thread.start()
        logger.info("Wake word detection started")
    
    def stop(self):
        """Stop wake word detection."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("Wake word detection stopped")
    
    def pause(self):
        """Pause detection while processing a command."""
        self.is_processing = True
    
    def resume(self):
        """Resume detection after processing."""
        self.is_processing = False
    
    def _detection_loop(self):
        """Main detection loop."""
        # Check if microphone is available before starting loop
        if not self.voice_engine.microphone:
            logger.warning("Wake word detection disabled - no microphone available")
            self.is_running = False
            return
            
        while self.is_running:
            try:
                # Skip if currently processing a command
                if self.is_processing:
                    time.sleep(0.5)
                    continue
                    
                text = self.voice_engine.listen(timeout=2, phrase_limit=3)
                if text and WAKE_WORD in text:
                    logger.info("Wake word detected!")
                    self.is_processing = True  # Prevent re-triggering
                    self.on_wake()
                    self.is_processing = False
            except Exception as e:
                logger.debug(f"Wake word detection error: {e}")
                time.sleep(1)  # Wait before retrying

# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND PARSER
# ═══════════════════════════════════════════════════════════════════════════════

class CommandParser:
    """Parses natural language commands."""
    
    # Command patterns
    PATTERNS = {
        'open_app': [
            # Specific common apps (for faster matching)
            r'open\s+(camera|calculator|calc|notepad|paint|cmd|powershell|terminal|command\s+prompt|explorer|file\s+explorer|task\s+manager|control\s+panel|settings|word|excel|powerpoint|outlook|chrome|firefox|edge|browser|spotify|discord|slack|teams|zoom|skype|vlc|media\s+player|photos|snipping\s+tool|clock|calendar|mail|store|onenote|onedrive|steam|epic\s+games|whatsapp|telegram|code|visual\s+studio|vs\s+code|vscode)(?:\s+app)?',
            # Generic pattern: "open [anything]" - captures ANY app name
            r'open\s+(.+?)\s+(?:app|application)$',
            r'launch\s+(.+?)\s+(?:app|application)$',
            r'start\s+(.+?)\s+(?:app|application)$',
            r'run\s+(.+?)\s+(?:app|application)$',
            # Ultra-generic: "open [anything]" - used by fallback in process_command
        ],
        'close_app': [
            # Close any app - captures the app name
            r'close\s+(.+?)(?:\s+app|\s+application)?$',
            r'kill\s+(.+?)(?:\s+app|\s+application)?$',
            r'stop\s+(.+?)(?:\s+app|\s+application)?$',
            r'quit\s+(.+?)(?:\s+app|\s+application)?$',
            r'exit\s+(.+?)(?:\s+app|\s+application)?$',
            r'terminate\s+(.+?)(?:\s+app|\s+application)?$',
            r'end\s+(.+?)(?:\s+app|\s+application)?$',
        ],
        'smart_search': [
            r'search\s+for\s+(.+)',
            r'search\s+(.+)',
            r'google\s+(.+)',
            r'look\s+up\s+(.+)',
            r'find\s+info\s+(on|about)\s+(.+)',
        ],
        'open_website': [
            r'open\s+(.+)',
            r'go\s+to\s+(.+)',
            r'browse\s+(.+)',
            r'launch\s+(.+)',
            r'show\s+me\s+(.+)',
        ],
        'shutdown': [
            r'shutdown',
            r'shut\s*down',
            r'turn\s+off',
            r'power\s+off',
        ],
        'restart': [
            r'restart',
            r'reboot',
        ],
        'lock': [
            r'lock\s*(screen|computer|laptop)?',
            r'lock$',
        ],
        'volume': [
            r'(increase|decrease|raise|lower|set)\s+volume\s*(to\s+)?(\d+)?',
            r'volume\s+(up|down|mute)',
            r'mute',
            r'unmute',
        ],
        'brightness': [
            r'(increase|decrease|set)\s+brightness\s*(to\s+)?(\d+)?',
            r'brightness\s+(up|down)',
        ],
        'weather': [
            r'weather\s*(in\s+)?(.+)?',
            r"what's\s+the\s+weather",
            r'forecast',
            r"how's\s+the\s+weather",
        ],
        'stock': [
            r'(stock|price|quote)\s+(of\s+)?(.+)',
            r'how\s+is\s+(.+)\s+(stock|doing)',
        ],
        'crypto': [
            r'(bitcoin|ethereum|crypto)\s*(price)?',
            r'(btc|eth)\s+price',
        ],
        'time': [
            r"what\s+time\s+is\s+it",
            r'current\s+time',
            r"what's\s+the\s+time",
            r'time\s*$',
        ],
        'date': [
            r"what's\s+the\s+date",
            r"what\s+day\s+is\s+it",
            r'current\s+date',
            r'date\s*$',
        ],
        'screenshot': [
            r'screenshot',
            r'screen\s*shot',
            r'capture\s+screen',
            r'take\s+a\s+screenshot',
        ],
        'organize_files': [
            r'organi[sz]e\s+(my\s+)?files(\s+and\s+folders)?',
            r'organi[sz]e\s+(my\s+)?folders(\s+and\s+files)?',
            r'clean\s+(up\s+)?(my\s+)?files',
            r'sort\s+(my\s+)?files',
            r'move\s+(all\s+)?(my\s+)?(pictures|photos|images)\s+(from\s+)?downloads?\s+(to\s+)?pictures?',
            r'move\s+(all\s+)?(my\s+)?files',
            r'move\s+pictures',
            r'move\s+photos',
            r'organi[sz]e\s+downloads',
        ],
        'clean_junk': [
            r'clean\s+junk',
            r'remove\s+temp(orary)?\s+files',
            r'delete\s+junk',
            r'delete\s+temp',
            r'clean\s+temp',
        ],
        'delete_files': [
            r'delete\s+(all\s+)?(my\s+)?(pictures|photos|images)',
            r'delete\s+files',
            r'remove\s+files',
        ],
        # New intelligent commands
        'system_status': [
            r'system\s+status',
            r'system\s+info',
            r'pc\s+status',
            r'computer\s+status',
            r'how\s+is\s+my\s+(computer|pc|system)',
            r'system\s+health',
        ],
        'cpu_status': [
            r'cpu\s+(usage|status)',
            r'processor\s+usage',
        ],
        'memory_status': [
            r'memory\s+usage',
            r'ram\s+usage',
            r'how\s+much\s+ram',
        ],
        'disk_status': [
            r'disk\s+(space|usage)',
            r'storage\s+space',
            r'how\s+much\s+space',
        ],
        'battery_status': [
            r'battery(\s+status)?',
            r'power\s+status',
            r'charging(\s+status)?',
        ],
        'process_list': [
            r'(top\s+)?processes',
            r"what's\s+running",
            r'running\s+processes',
            r'(what\s+is\s+)?using\s+memory',
            r'memory\s+hogs',
        ],
        'network_status': [
            r'network\s+(info|status)',
            r'(my\s+)?ip\s+address',
            r'my\s+ip',
        ],
        'web_search': [
            r'search\s+(.+)',
            r'look\s+up\s+(.+)',
            r'find\s+info\s+(.+)',
        ],
        'define_word': [
            r'define\s+(.+)',
            r'(what\s+is\s+the\s+)?meaning\s+of\s+(.+)',
            r'definition\s+of\s+(.+)',
        ],
        'unit_convert': [
            r'(\d+)\s*(?:°?c|celsius)\s+(?:to|in)\s+(?:°?f|fahrenheit)',
            r'(\d+)\s*(?:°?f|fahrenheit)\s+(?:to|in)\s+(?:°?c|celsius)',
            r'(\d+)\s*(?:km|kilometers?)\s+(?:to|in)\s+(?:mi|miles?)',
            r'(\d+)\s*(?:mi|miles?)\s+(?:to|in)\s+(?:km|kilometers?)',
            r'(\d+)\s*(?:kg|kilograms?)\s+(?:to|in)\s+(?:lb|lbs?|pounds?)',
            r'(\d+)\s*(?:lb|lbs?|pounds?)\s+(?:to|in)\s+(?:kg|kilograms?)',
        ],
        'run_code': [
            r'run\s+code\s+(.+)',
            r'execute\s+(.+)',
        ],
        'game': [
            r'play\s+(.+)',
            r'launch\s+game\s+(.+)',
            r'start\s+(.+)\s+game',
        ],
        'reminder': [
            r'remind\s+me\s+to\s+(.+)\s+(in|at)\s+(.+)',
            r'set\s+reminder\s+(.+)',
        ],
        'summary': [
            r'daily\s+summary',
            r'morning\s+summary',
            r'market\s+summary',
        ],
        'history': [
            r'command\s+history',
            r'what\s+did\s+i\s+(ask|say)',
            r'search\s+history\s+(.+)',
        ],
        'help': [
            r'help',
            r'what\s+can\s+you\s+do',
            r'commands',
        ],
        'feedback': [
            r'feedback',
            r'rate\s+(.+)',
        ],
        'greeting': [
            r'hello',
            r'hi\s*$',
            r'hey\s*$',
            r'good\s+(morning|afternoon|evening)',
        ],
        'name': [
            r"what's\s+your\s+name",
            r"what\s+is\s+your\s+name",
            r'who\s+are\s+you',
            r'your\s+name',
        ],
        'thanks': [
            r'thank\s*you',
            r'thanks',
        ],
    }
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse command text and return action with parameters."""
        text = text.lower().strip()
        
        for action, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return {
                        'action': action,
                        'params': match.groups(),
                        'raw_text': text
                    }
        
        return {
            'action': 'unknown',
            'params': (),
            'raw_text': text
        }

# ═══════════════════════════════════════════════════════════════════════════════
# LOCAL INTELLIGENCE - Built-in smart responses without API
# ═══════════════════════════════════════════════════════════════════════════════

class LocalIntelligence:
    """Built-in intelligence for math, general knowledge, and conversational queries."""
    
    def __init__(self):
        self.math_keywords = ['what is', 'calculate', 'compute', 'solve', 'evaluate', 
                              'how much is', "what's", 'equals', 'plus', 'minus', 
                              'times', 'divided', 'multiply', 'add', 'subtract']
        
        # Initialize advanced components
        self.safe_calculator = SafeCalculator()
        self.web_search = WebSearchEngine()
        self.system_monitor = SystemMonitor()
        self.code_sandbox = CodeSandbox()
        self.conversation_memory = ConversationMemory()
        
        # Knowledge base for common questions
        self.knowledge_base = {
            # General knowledge
            'who is the president of usa': "As of my knowledge, the current US President is Donald Trump (since January 2025).",
            'who is the president of america': "As of my knowledge, the current US President is Donald Trump (since January 2025).",
            'who is the prime minister of india': "As of my knowledge, the Prime Minister of India is Narendra Modi.",
            'what is the capital of': self._get_capital,
            'how many days in': self._get_days_in_month,
            'how many states in usa': "The United States has 50 states.",
            'how many continents': "There are 7 continents: Africa, Antarctica, Asia, Australia/Oceania, Europe, North America, and South America.",
            'who invented': self._get_inventor,
            'what is pi': "Pi (π) is approximately 3.14159265359. It's the ratio of a circle's circumference to its diameter.",
            'what is the speed of light': "The speed of light is approximately 299,792,458 meters per second (about 186,282 miles per second).",
            'what is gravity': "Gravity is a fundamental force that attracts objects with mass toward each other. Earth's gravity is about 9.8 m/s².",
            
            # Conversational
            'how are you': f"I'm doing great, {USER_NAME}! Ready to help you with anything.",
            'are you real': f"I'm April, your AI assistant! I'm software, but I'm here to help you for real, {USER_NAME}.",
            'do you have feelings': "I don't have feelings like humans do, but I'm designed to be helpful and friendly!",
            'tell me a joke': self._get_joke,
            'tell me a fact': self._get_random_fact,
            'what can you do': "I can help with math calculations, open apps, control your system (volume, brightness), get weather and stock info, take screenshots, organize files, and chat with you!",
            'who made you': f"I was created as a personal AI assistant for {USER_NAME}. I'm April, nice to meet you!",
            'who created you': f"I was created as a personal AI assistant for {USER_NAME}. I'm April, nice to meet you!",
            
            # Fun responses
            'meaning of life': "The meaning of life? 42, according to Douglas Adams! But really, it's what you make of it. 😊",
            'are you smart': "I try my best! I can do math, answer questions, and help with your computer. What would you like to know?",
            'i love you': f"Aww, that's sweet! I'm here for you anytime, {USER_NAME}! 💙",
            'thank you': f"You're welcome, {USER_NAME}! Happy to help!",
        }
        
        # Capitals database
        self.capitals = {
            'usa': 'Washington, D.C.', 'america': 'Washington, D.C.', 'united states': 'Washington, D.C.',
            'india': 'New Delhi', 'uk': 'London', 'united kingdom': 'London', 'england': 'London',
            'france': 'Paris', 'germany': 'Berlin', 'japan': 'Tokyo', 'china': 'Beijing',
            'russia': 'Moscow', 'brazil': 'Brasília', 'australia': 'Canberra', 'canada': 'Ottawa',
            'italy': 'Rome', 'spain': 'Madrid', 'mexico': 'Mexico City', 'south korea': 'Seoul',
            'egypt': 'Cairo', 'south africa': 'Pretoria', 'argentina': 'Buenos Aires',
            'indonesia': 'Jakarta', 'turkey': 'Ankara', 'saudi arabia': 'Riyadh',
            'netherlands': 'Amsterdam', 'switzerland': 'Bern', 'sweden': 'Stockholm',
            'norway': 'Oslo', 'denmark': 'Copenhagen', 'finland': 'Helsinki',
            'poland': 'Warsaw', 'austria': 'Vienna', 'belgium': 'Brussels',
            'portugal': 'Lisbon', 'greece': 'Athens', 'israel': 'Jerusalem',
            'uae': 'Abu Dhabi', 'pakistan': 'Islamabad', 'bangladesh': 'Dhaka',
            'thailand': 'Bangkok', 'vietnam': 'Hanoi', 'singapore': 'Singapore',
            'malaysia': 'Kuala Lumpur', 'philippines': 'Manila', 'new zealand': 'Wellington',
        }
        
        # Inventors database
        self.inventors = {
            'telephone': 'Alexander Graham Bell invented the telephone in 1876.',
            'light bulb': 'Thomas Edison is credited with inventing the practical light bulb in 1879.',
            'lightbulb': 'Thomas Edison is credited with inventing the practical light bulb in 1879.',
            'electricity': 'Electricity was discovered and studied by many scientists including Benjamin Franklin and Michael Faraday.',
            'computer': 'Charles Babbage is considered the father of the computer, designing the Analytical Engine in the 1830s.',
            'internet': 'The Internet was developed by ARPANET researchers in the late 1960s, with Tim Berners-Lee creating the World Wide Web in 1989.',
            'airplane': 'The Wright Brothers (Orville and Wilbur) invented the first successful airplane in 1903.',
            'car': 'Karl Benz is credited with inventing the first practical automobile in 1885.',
            'automobile': 'Karl Benz is credited with inventing the first practical automobile in 1885.',
            'radio': 'Guglielmo Marconi is credited with inventing the practical radio in the 1890s.',
            'television': 'Philo Farnsworth invented the first fully electronic television in 1927.',
            'steam engine': 'James Watt significantly improved the steam engine in 1769.',
        }
        
        # Jokes list
        self.jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
            "Why did the computer go to the doctor? Because it had a virus! 💻",
            "What do you call a computer that sings? A-Dell! 🎤",
            "Why was the math book sad? It had too many problems! 📚",
            "What's a computer's favorite snack? Microchips! 🍟",
            "Why do Java developers wear glasses? Because they can't C#! 👓",
            "How does a computer get drunk? It takes screenshots! 📸",
            "Why did the PowerPoint presentation cross the road? To get to the other slide! 📊",
        ]
        
        # Facts list
        self.facts = [
            "Honey never spoils. Archaeologists have found 3000-year-old honey in Egyptian tombs that was still edible!",
            "Octopuses have three hearts and blue blood.",
            "A day on Venus is longer than a year on Venus.",
            "The shortest war in history lasted only 38-45 minutes (Anglo-Zanzibar War, 1896).",
            "Bananas are berries, but strawberries aren't!",
            "The human brain uses about 20% of the body's total energy.",
            "There are more possible iterations of a game of chess than atoms in the observable universe.",
            "Dolphins sleep with one eye open.",
            "The Eiffel Tower can grow up to 6 inches taller during hot summer days due to thermal expansion.",
            "A group of flamingos is called a 'flamboyance'.",
        ]
    
    def process(self, text: str) -> Optional[str]:
        """Process the query and return a response if possible."""
        text_lower = text.lower().strip()
        
        # Try special commands first
        special_response = self._try_special_commands(text_lower, text)
        if special_response:
            return special_response
        
        # Try math using safe AST calculator
        math_result = self._try_math(text_lower)
        if math_result:
            return math_result
        
        # Try knowledge base (exact matches first)
        for key, value in self.knowledge_base.items():
            if key in text_lower:
                if callable(value):
                    result = value(text_lower)
                    if result:
                        return result
                else:
                    return value
        
        # Try partial matches for questions
        response = self._try_question(text_lower)
        if response:
            return response
        
        return None
    
    def _try_special_commands(self, text_lower: str, original_text: str) -> Optional[str]:
        """Handle special intelligent commands."""
        
        # System status / info
        if any(kw in text_lower for kw in ['system status', 'system info', 'pc status', 'computer status', 
                                            'how is my computer', 'system health', 'pc info']):
            return self._get_system_status()
        
        # Memory / RAM usage
        if any(kw in text_lower for kw in ['memory usage', 'ram usage', 'how much ram', 'memory status']):
            return self._get_memory_status()
        
        # CPU usage
        if any(kw in text_lower for kw in ['cpu usage', 'processor usage', 'cpu status']):
            return self._get_cpu_status()
        
        # Disk space
        if any(kw in text_lower for kw in ['disk space', 'storage space', 'how much space', 'disk usage']):
            return self._get_disk_status()
        
        # Battery status
        if any(kw in text_lower for kw in ['battery', 'power status', 'charging']):
            return self._get_battery_status()
        
        # Top processes / what's running
        if any(kw in text_lower for kw in ['top processes', "what's running", 'running processes', 
                                            'show processes', 'memory hogs', 'what is using memory']):
            return self._get_top_processes()
        
        # Network info
        if any(kw in text_lower for kw in ['network info', 'ip address', 'my ip', 'network status']):
            return self._get_network_status()
        
        # Web search (DuckDuckGo - no API needed!)
        if text_lower.startswith('search ') or text_lower.startswith('look up ') or text_lower.startswith('find info'):
            query = re.sub(r'^(search|look up|find info about|find info on|find info)\s*', '', text_lower).strip()
            if query:
                return self._do_web_search(query)
        
        # Word definition
        if text_lower.startswith('define ') or 'meaning of ' in text_lower or 'definition of ' in text_lower:
            word = re.sub(r'^(define|what is the meaning of|meaning of|definition of)\s*', '', text_lower).strip().rstrip('?')
            if word:
                return self._get_definition(word)
        
        # Free weather (no API key!)
        if 'weather' in text_lower and not any(kw in text_lower for kw in ['help', 'how to']):
            # Extract location
            location = None
            for pattern in [r'weather (?:in|for|at) (.+?)(?:\?|$)', r'weather (.+?)(?:\?|$)']:
                match = re.search(pattern, text_lower)
                if match:
                    location = match.group(1).strip()
                    break
            
            if location:
                return self._get_free_weather(location)
            else:
                return self._get_free_weather('auto')  # Auto-detect
        
        # Run Python code
        if text_lower.startswith('run code ') or text_lower.startswith('execute '):
            code = original_text
            for prefix in ['run code ', 'execute ']:
                if code.lower().startswith(prefix):
                    code = code[len(prefix):]
                    break
            if code:
                return self._run_code(code)
        
        # Date and time queries
        if any(kw in text_lower for kw in ['what time', 'current time', "what's the time", 'time now']):
            return f"🕐 The current time is {datetime.now().strftime('%I:%M %p')}"
        
        if any(kw in text_lower for kw in ['what date', "today's date", 'current date', 'what day']):
            return f"📅 Today is {datetime.now().strftime('%A, %B %d, %Y')}"
        
        if 'what year' in text_lower:
            return f"📅 The current year is {datetime.now().year}"
        
        # Unit conversions
        conversion_result = self._try_conversion(text_lower)
        if conversion_result:
            return conversion_result
        
        return None
    
    def _get_system_status(self) -> str:
        """Get overall system status."""
        info = self.system_monitor.get_system_info()
        
        parts = [f"💻 **System Status for {info.get('hostname', 'your PC')}**\n"]
        
        if 'cpu_percent' in info:
            cpu_emoji = "🔥" if info['cpu_percent'] > 80 else "✅"
            parts.append(f"{cpu_emoji} CPU: {info['cpu_percent']}% ({info.get('cpu_count', '?')} cores)")
        
        if 'memory_percent' in info:
            mem_emoji = "🔥" if info['memory_percent'] > 80 else "✅"
            parts.append(f"{mem_emoji} RAM: {info['memory_used_gb']}/{info['memory_total_gb']} GB ({info['memory_percent']}%)")
        
        if 'disk_percent' in info:
            disk_emoji = "⚠️" if info['disk_percent'] > 90 else "✅"
            parts.append(f"{disk_emoji} Disk: {info['disk_used_gb']}/{info['disk_total_gb']} GB ({info['disk_percent']}%)")
        
        if 'battery_percent' in info:
            batt = info['battery_percent']
            plug = "🔌" if info.get('battery_plugged') else "🔋"
            batt_emoji = "⚠️" if batt < 20 else "✅"
            parts.append(f"{batt_emoji} Battery: {batt}% {plug}")
        
        parts.append(f"\n🖥️ {info.get('os', 'Unknown OS')}")
        
        return '\n'.join(parts)
    
    def _get_memory_status(self) -> str:
        """Get memory status."""
        info = self.system_monitor.get_system_info()
        
        if 'memory_percent' not in info:
            return "Unable to get memory info. Try installing psutil: pip install psutil"
        
        emoji = "🔥" if info['memory_percent'] > 80 else "✅"
        return f"{emoji} **Memory Usage**\n" \
               f"Used: {info['memory_used_gb']} GB / {info['memory_total_gb']} GB ({info['memory_percent']}%)"
    
    def _get_cpu_status(self) -> str:
        """Get CPU status."""
        info = self.system_monitor.get_system_info()
        
        if 'cpu_percent' not in info:
            return "Unable to get CPU info. Try installing psutil: pip install psutil"
        
        emoji = "🔥" if info['cpu_percent'] > 80 else "✅"
        return f"{emoji} **CPU Usage**: {info['cpu_percent']}%\n" \
               f"Cores: {info.get('cpu_count', 'Unknown')}\n" \
               f"Processor: {info.get('processor', 'Unknown')}"
    
    def _get_disk_status(self) -> str:
        """Get disk status."""
        info = self.system_monitor.get_system_info()
        
        if 'disk_percent' not in info:
            return "Unable to get disk info."
        
        free = info['disk_total_gb'] - info['disk_used_gb']
        emoji = "⚠️" if info['disk_percent'] > 90 else "✅"
        return f"{emoji} **Disk Space**\n" \
               f"Used: {info['disk_used_gb']} GB / {info['disk_total_gb']} GB ({info['disk_percent']}%)\n" \
               f"Free: {round(free, 2)} GB"
    
    def _get_battery_status(self) -> str:
        """Get battery status."""
        info = self.system_monitor.get_system_info()
        
        if 'battery_percent' not in info:
            return "🔌 No battery detected (desktop PC) or psutil not installed."
        
        batt = info['battery_percent']
        plugged = info.get('battery_plugged', False)
        plug_text = "Charging 🔌" if plugged else "On battery 🔋"
        
        emoji = "⚠️" if batt < 20 else "✅"
        return f"{emoji} **Battery**: {batt}% - {plug_text}"
    
    def _get_top_processes(self) -> str:
        """Get top resource-using processes."""
        processes = self.system_monitor.get_running_processes()
        
        if not processes:
            return "Unable to get process list."
        
        lines = ["📊 **Top Processes by Memory**\n"]
        for i, proc in enumerate(processes[:10], 1):
            name = proc.get('name', 'Unknown')[:20]
            mem = proc.get('memory', 0)
            lines.append(f"{i}. {name}: {mem}%")
        
        return '\n'.join(lines)
    
    def _get_network_status(self) -> str:
        """Get network info."""
        info = self.system_monitor.get_network_info()
        
        if not info:
            return "Unable to get network info."
        
        parts = ["🌐 **Network Info**\n"]
        
        if 'hostname' in info:
            parts.append(f"Hostname: {info['hostname']}")
        if 'local_ip' in info:
            parts.append(f"Local IP: {info['local_ip']}")
        if 'bytes_sent_mb' in info:
            parts.append(f"Data Sent: {info['bytes_sent_mb']} MB")
            parts.append(f"Data Received: {info['bytes_recv_mb']} MB")
        
        return '\n'.join(parts)
    
    def _do_web_search(self, query: str) -> str:
        """Perform web search using DuckDuckGo."""
        results = self.web_search.search(query, num_results=5)
        
        if not results:
            return f"Couldn't find results for '{query}'. Try a different search term."
        
        lines = [f"🔍 **Search results for '{query}'**\n"]
        for i, result in enumerate(results[:5], 1):
            title = result.get('title', 'No title')[:50]
            snippet = result.get('snippet', '')[:100]
            url = result.get('url', '')
            
            lines.append(f"**{i}. {title}**")
            if snippet:
                lines.append(f"   {snippet}...")
            if url:
                lines.append(f"   🔗 {url[:60]}...")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _get_definition(self, word: str) -> str:
        """Get word definition."""
        definition = self.web_search.get_definition(word)
        
        if definition:
            return f"📖 {definition}"
        else:
            return f"Couldn't find a definition for '{word}'."
    
    def _get_free_weather(self, location: str) -> str:
        """Get weather using free wttr.in service."""
        if location == 'auto':
            location = ''  # wttr.in auto-detects location
        
        weather = self.web_search.get_weather_free(location)
        
        if weather:
            return f"🌤️ {weather}"
        else:
            return "Couldn't get weather. Try specifying a city name."
    
    def _run_code(self, code: str) -> str:
        """Run Python code in sandbox."""
        result = self.code_sandbox.execute(code)
        
        if result['success']:
            return f"✅ **Code Output:**\n```\n{result['output']}\n```"
        else:
            return f"❌ **Error:**\n{result['output']}"
    
    def _try_conversion(self, text: str) -> Optional[str]:
        """Try unit conversions."""
        # Temperature conversions
        celsius_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:°?c|celsius|centigrade)\s*(?:to|in)\s*(?:°?f|fahrenheit)', text)
        if celsius_match:
            c = float(celsius_match.group(1))
            f = (c * 9/5) + 32
            return f"🌡️ {c}°C = {round(f, 2)}°F"
        
        fahrenheit_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:°?f|fahrenheit)\s*(?:to|in)\s*(?:°?c|celsius)', text)
        if fahrenheit_match:
            f = float(fahrenheit_match.group(1))
            c = (f - 32) * 5/9
            return f"🌡️ {f}°F = {round(c, 2)}°C"
        
        # Length conversions
        km_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:km|kilometers?|kilometres?)\s*(?:to|in)\s*(?:mi|miles?)', text)
        if km_match:
            km = float(km_match.group(1))
            mi = km * 0.621371
            return f"📏 {km} km = {round(mi, 2)} miles"
        
        miles_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:mi|miles?)\s*(?:to|in)\s*(?:km|kilometers?)', text)
        if miles_match:
            mi = float(miles_match.group(1))
            km = mi * 1.60934
            return f"📏 {mi} miles = {round(km, 2)} km"
        
        # Weight conversions
        kg_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|kilograms?|kilos?)\s*(?:to|in)\s*(?:lb|lbs?|pounds?)', text)
        if kg_match:
            kg = float(kg_match.group(1))
            lb = kg * 2.20462
            return f"⚖️ {kg} kg = {round(lb, 2)} lbs"
        
        lb_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lb|lbs?|pounds?)\s*(?:to|in)\s*(?:kg|kilograms?)', text)
        if lb_match:
            lb = float(lb_match.group(1))
            kg = lb * 0.453592
            return f"⚖️ {lb} lbs = {round(kg, 2)} kg"
        
        return None
    
    def _try_math(self, text: str) -> Optional[str]:
        """Try to evaluate as a math expression using safe AST calculator."""
        # Check if it looks like a math question
        has_math_keyword = any(kw in text for kw in self.math_keywords)
        has_numbers = bool(re.search(r'\d', text))
        has_operators = bool(re.search(r'[\+\-\*\/\^]', text) or 
                            any(op in text for op in ['plus', 'minus', 'times', 'divided', 'multiply', 'power']))
        has_functions = bool(re.search(r'\b(sqrt|sin|cos|tan|log|exp|abs|round|floor|ceil|factorial)\s*\(', text))
        
        if not (has_math_keyword or (has_numbers and has_operators) or has_functions):
            return None
        
        # Use the safe AST calculator
        result = self.safe_calculator.evaluate(text)
        
        if result is not None:
            # Format result nicely
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 10)
            return f"The answer is {result} 🧮"
        
        # Fallback to old regex-based method for complex expressions
        try:
            # Extract and normalize the math expression
            expr = text
            
            # Remove common question prefixes
            for prefix in ['what is', "what's", 'calculate', 'compute', 'solve', 'evaluate', 'how much is']:
                expr = re.sub(rf'^{prefix}\s*', '', expr, flags=re.IGNORECASE)
            
            # Convert word operators to symbols
            expr = re.sub(r'\bplus\b', '+', expr)
            expr = re.sub(r'\bminus\b', '-', expr)
            expr = re.sub(r'\btimes\b', '*', expr)
            expr = re.sub(r'\bmultiplied\s+by\b', '*', expr)
            expr = re.sub(r'\bmultiply\s+by\b', '*', expr)
            expr = re.sub(r'\bdivided\s+by\b', '/', expr)
            expr = re.sub(r'\bover\b', '/', expr)
            expr = re.sub(r'\bto\s+the\s+power\s+of\b', '**', expr)
            expr = re.sub(r'\bpower\b', '**', expr)
            expr = re.sub(r'\bsquared\b', '**2', expr)
            expr = re.sub(r'\bcubed\b', '**3', expr)
            expr = re.sub(r'\bsquare\s+root\s+of\b', 'sqrt', expr)
            expr = re.sub(r'\bsqrt\b', 'math.sqrt', expr)
            expr = re.sub(r'\bmod\b', '%', expr)
            expr = re.sub(r'\bpercent\s+of\b', '/100*', expr)
            expr = re.sub(r'%\s+of\b', '/100*', expr)
            
            # Clean up - keep only valid math characters
            expr = expr.strip().rstrip('?.')
            
            # Extract just the math part
            math_match = re.search(r'[\d\.\+\-\*\/\(\)\^\s]+', expr.replace('math.sqrt', 'SQRT'))
            if math_match:
                expr = math_match.group().replace('SQRT', 'math.sqrt')
            
            # Handle 'x' as multiplication (e.g., "5 x 3")
            expr = re.sub(r'(\d)\s*x\s*(\d)', r'\1*\2', expr)
            
            # Replace ^ with **
            expr = expr.replace('^', '**')
            
            # Validate: only allow safe characters
            if not re.match(r'^[\d\.\+\-\*\/\(\)\s\*math\.sqrt]+$', expr):
                return None
            
            # Evaluate safely
            import math
            allowed_names = {"math": math, "sqrt": math.sqrt, "pi": math.pi, "e": math.e}
            result = eval(expr, {"__builtins__": {}}, allowed_names)
            
            # Format result nicely
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 10)  # Avoid floating point weirdness
            
            return f"The answer is {result} 🧮"
            
        except Exception as e:
            return None
    
    def _get_capital(self, text: str) -> Optional[str]:
        """Get capital city of a country."""
        # Extract country name
        match = re.search(r'capital\s+of\s+(.+?)(?:\?|$)', text)
        if match:
            country = match.group(1).strip().lower()
            if country in self.capitals:
                return f"The capital of {country.title()} is {self.capitals[country]}."
        return None
    
    def _get_days_in_month(self, text: str) -> Optional[str]:
        """Get days in a month."""
        months = {
            'january': 31, 'february': '28 (or 29 in leap years)', 'march': 31,
            'april': 30, 'may': 31, 'june': 30, 'july': 31, 'august': 31,
            'september': 30, 'october': 31, 'november': 30, 'december': 31,
            'year': 365, 'week': 7
        }
        for month, days in months.items():
            if month in text:
                return f"There are {days} days in {month.title()}."
        return None
    
    def _get_inventor(self, text: str) -> Optional[str]:
        """Get inventor of something."""
        for item, answer in self.inventors.items():
            if item in text:
                return answer
        return None
    
    def _get_joke(self, text: str) -> str:
        """Return a random joke."""
        return random.choice(self.jokes)
    
    def _get_random_fact(self, text: str) -> str:
        """Return a random fact."""
        return "🌟 Fun fact: " + random.choice(self.facts)
    
    def _try_question(self, text: str) -> Optional[str]:
        """Try to answer common question patterns."""
        # What is X?
        if text.startswith('what is ') or text.startswith("what's "):
            query = re.sub(r"^what'?s?\s+", '', text).rstrip('?')
            
            # Check capitals
            if 'capital' in query:
                return self._get_capital(text)
            
            # Days in month/year
            if 'days in' in query:
                return self._get_days_in_month(text)
        
        # Who invented X?
        if 'who invented' in text or 'invented the' in text:
            return self._get_inventor(text)
        
        # How many X?
        if text.startswith('how many'):
            if 'states' in text and ('usa' in text or 'america' in text or 'us' in text):
                return "The United States has 50 states."
            if 'continent' in text:
                return "There are 7 continents: Africa, Antarctica, Asia, Australia/Oceania, Europe, North America, and South America."
            if 'planet' in text:
                return "There are 8 planets in our solar system: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune."
            if 'ocean' in text:
                return "There are 5 oceans: Pacific, Atlantic, Indian, Southern (Antarctic), and Arctic."
        
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCED INTELLIGENCE - AST-Safe Calculator & Enhanced Features
# ═══════════════════════════════════════════════════════════════════════════════

class SafeCalculator:
    """AST-based safe calculator - prevents code injection."""
    
    def __init__(self):
        import ast
        import operator
        import math
        
        # Safe operators
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        
        # Safe functions
        self.functions = {
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'abs': abs,
            'round': round,
            'floor': math.floor,
            'ceil': math.ceil,
            'factorial': math.factorial,
        }
        
        # Safe constants
        self.constants = {
            'pi': math.pi,
            'e': math.e,
            'tau': math.tau,
        }
    
    def evaluate(self, expression: str) -> Optional[float]:
        """Safely evaluate a math expression using AST."""
        import ast
        
        # Normalize the expression
        expr = expression.lower().strip()
        
        # Replace word operators
        replacements = [
            (r'\bplus\b', '+'), (r'\bminus\b', '-'), (r'\btimes\b', '*'),
            (r'\bdivided\s*by\b', '/'), (r'\bover\b', '/'), (r'\bmod\b', '%'),
            (r'\bto\s*the\s*power\s*of\b', '**'), (r'\bsquared\b', '**2'),
            (r'\bcubed\b', '**3'), (r'\bx\b', '*'),
        ]
        for pattern, replacement in replacements:
            expr = re.sub(pattern, replacement, expr)
        
        # Remove question words
        for prefix in ['what is', "what's", 'calculate', 'compute', 'solve', 'evaluate', 'how much is']:
            expr = re.sub(rf'^{prefix}\s*', '', expr, flags=re.IGNORECASE)
        
        expr = expr.strip().rstrip('?.')
        
        try:
            tree = ast.parse(expr, mode='eval')
            return self._eval_node(tree.body)
        except Exception:
            return None
    
    def _eval_node(self, node):
        """Recursively evaluate AST nodes."""
        import ast
        
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Invalid constant")
        
        # Python 3.7 compatibility (ast.Num was removed in Python 3.14)
        elif hasattr(ast, 'Num') and isinstance(node, ast.Num):
            return node.n
        
        elif isinstance(node, ast.Name):
            name = node.id.lower()
            if name in self.constants:
                return self.constants[name]
            raise ValueError(f"Unknown constant: {name}")
        
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)
            if op_type not in self.operators:
                raise ValueError(f"Unsupported operator: {op_type}")
            return self.operators[op_type](left, right)
        
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_type = type(node.op)
            if op_type not in self.operators:
                raise ValueError(f"Unsupported unary operator: {op_type}")
            return self.operators[op_type](operand)
        
        elif isinstance(node, ast.Call):
            func_name = node.func.id.lower() if isinstance(node.func, ast.Name) else None
            if func_name not in self.functions:
                raise ValueError(f"Unknown function: {func_name}")
            args = [self._eval_node(arg) for arg in node.args]
            return self.functions[func_name](*args)
        
        else:
            raise ValueError(f"Unsupported AST node: {type(node)}")


class WebSearchEngine:
    """Free web search using DuckDuckGo (no API key needed!)."""
    
    def __init__(self):
        self.ddg_url = "https://html.duckduckgo.com/html/"
        self.wttr_url = "https://wttr.in"
    
    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Search DuckDuckGo and return results."""
        try:
            import requests
            from urllib.parse import urlencode
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.post(
                self.ddg_url,
                data={'q': query, 'b': ''},
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                return []
            
            # Parse results from HTML
            results = []
            html = response.text
            
            # Simple regex extraction (more robust than BeautifulSoup for basic use)
            import re
            
            # Find result blocks
            result_pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
            snippet_pattern = r'<a class="result__snippet"[^>]*>([^<]+)</a>'
            
            links = re.findall(result_pattern, html)
            snippets = re.findall(snippet_pattern, html)
            
            for i, (url, title) in enumerate(links[:num_results]):
                snippet = snippets[i] if i < len(snippets) else ""
                # Clean up DuckDuckGo redirect URL
                if 'uddg=' in url:
                    from urllib.parse import unquote, parse_qs, urlparse
                    try:
                        parsed = urlparse(url)
                        params = parse_qs(parsed.query)
                        url = unquote(params.get('uddg', [url])[0])
                    except:
                        pass
                
                results.append({
                    'title': title.strip(),
                    'url': url,
                    'snippet': snippet.strip()
                })
            
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    def get_weather_free(self, location: str) -> str:
        """Get weather from wttr.in (no API key needed!)."""
        try:
            import requests
            
            # Clean location
            location = location.strip().replace(' ', '+')
            
            # wttr.in returns nice text format
            response = requests.get(
                f"{self.wttr_url}/{location}?format=3",
                timeout=10,
                headers={'User-Agent': 'curl/7.0'}
            )
            
            if response.status_code == 200:
                return response.text.strip()
            
            # Try detailed format
            response = requests.get(
                f"{self.wttr_url}/{location}?format=%l:+%c+%t+%h+%w",
                timeout=10,
                headers={'User-Agent': 'curl/7.0'}
            )
            
            if response.status_code == 200:
                return response.text.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Weather fetch error: {e}")
            return None
    
    def get_definition(self, word: str) -> str:
        """Get word definition from free API."""
        try:
            import requests
            
            response = requests.get(
                f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    meanings = data[0].get('meanings', [])
                    if meanings:
                        definition = meanings[0].get('definitions', [{}])[0].get('definition', '')
                        part_of_speech = meanings[0].get('partOfSpeech', '')
                        return f"**{word}** ({part_of_speech}): {definition}"
            
            return None
            
        except Exception as e:
            logger.error(f"Definition fetch error: {e}")
            return None


class SystemMonitor:
    """Monitor system resources and processes."""
    
    def get_system_info(self) -> Dict:
        """Get comprehensive system information."""
        import platform
        
        info = {
            'os': platform.system(),
            'os_version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'hostname': platform.node(),
        }
        
        # Get memory info
        try:
            import psutil
            mem = psutil.virtual_memory()
            info['memory_total_gb'] = round(mem.total / (1024**3), 2)
            info['memory_used_gb'] = round(mem.used / (1024**3), 2)
            info['memory_percent'] = mem.percent
            
            # CPU info
            info['cpu_percent'] = psutil.cpu_percent(interval=1)
            info['cpu_count'] = psutil.cpu_count()
            
            # Disk info
            disk = psutil.disk_usage('/')
            info['disk_total_gb'] = round(disk.total / (1024**3), 2)
            info['disk_used_gb'] = round(disk.used / (1024**3), 2)
            info['disk_percent'] = round(disk.percent, 1)
            
            # Battery (if available)
            battery = psutil.sensors_battery()
            if battery:
                info['battery_percent'] = battery.percent
                info['battery_plugged'] = battery.power_plugged
                
        except ImportError:
            # psutil not available, use basic methods
            pass
        except Exception as e:
            logger.debug(f"System info error: {e}")
        
        return info
    
    def get_running_processes(self, sort_by: str = 'memory') -> List[Dict]:
        """Get list of running processes sorted by resource usage."""
        processes = []
        
        try:
            import psutil
            
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
                try:
                    info = proc.info
                    if info['name'] and info['memory_percent']:
                        processes.append({
                            'pid': info['pid'],
                            'name': info['name'],
                            'memory': round(info['memory_percent'], 2),
                            'cpu': round(info.get('cpu_percent', 0), 2)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by memory or CPU
            if sort_by == 'memory':
                processes.sort(key=lambda x: x['memory'], reverse=True)
            else:
                processes.sort(key=lambda x: x['cpu'], reverse=True)
            
        except ImportError:
            # Fallback to tasklist
            try:
                result = subprocess.run(
                    ['tasklist', '/fo', 'csv', '/nh'],
                    capture_output=True, text=True
                )
                for line in result.stdout.strip().split('\n')[:20]:
                    parts = line.strip('"').split('","')
                    if len(parts) >= 5:
                        processes.append({
                            'name': parts[0],
                            'pid': int(parts[1]) if parts[1].isdigit() else 0,
                            'memory': parts[4].replace(' K', '').replace(',', '')
                        })
            except:
                pass
        
        return processes[:20]  # Top 20
    
    def kill_process_by_name(self, name: str) -> bool:
        """Kill a process by name."""
        try:
            import psutil
            
            killed = False
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    if name.lower() in proc.info['name'].lower():
                        proc.kill()
                        killed = True
                        logger.info(f"Killed process: {proc.info['name']} (PID: {proc.info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return killed
            
        except ImportError:
            # Fallback to taskkill
            try:
                subprocess.run(['taskkill', '/f', '/im', f'{name}*'], capture_output=True)
                return True
            except:
                return False
    
    def get_network_info(self) -> Dict:
        """Get network information."""
        info = {}
        
        try:
            import psutil
            import socket
            
            # Get hostname and IP
            info['hostname'] = socket.gethostname()
            try:
                info['local_ip'] = socket.gethostbyname(info['hostname'])
            except:
                pass
            
            # Network stats
            net_io = psutil.net_io_counters()
            info['bytes_sent_mb'] = round(net_io.bytes_sent / (1024**2), 2)
            info['bytes_recv_mb'] = round(net_io.bytes_recv / (1024**2), 2)
            
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Network info error: {e}")
        
        return info


class CodeSandbox:
    """Safe Python code execution in isolated environment."""
    
    # Dangerous patterns to block
    BLOCKED_PATTERNS = [
        'os.system', 'os.popen', 'subprocess', 'shutil.rmtree',
        'os.remove', 'os.unlink', 'os.rmdir', '__import__',
        'eval(', 'exec(', 'compile(', 'open(',
        'import os', 'import sys', 'import subprocess',
        'import shutil', 'from os', 'from sys', 'from subprocess',
    ]
    
    def __init__(self, timeout: int = 10, max_output: int = 5000):
        self.timeout = timeout
        self.max_output = max_output
    
    def execute(self, code: str) -> Dict:
        """Execute Python code safely."""
        # Security check
        for pattern in self.BLOCKED_PATTERNS:
            if pattern in code:
                return {
                    'success': False,
                    'output': f"Blocked: code contains prohibited pattern '{pattern}'",
                    'error': True
                }
        
        try:
            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            output = result.stdout
            if result.stderr:
                output += ('\n' if output else '') + result.stderr
            
            if len(output) > self.max_output:
                output = output[:self.max_output] + '\n... (output truncated)'
            
            return {
                'success': result.returncode == 0,
                'output': output or '(no output)',
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': f'Execution timed out after {self.timeout} seconds.',
                'error': True
            }
        except Exception as e:
            return {
                'success': False,
                'output': f'Execution error: {e}',
                'error': True
            }


class ConversationMemory:
    """Short-term conversation memory for context awareness."""
    
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.history: List[Dict] = []
        self.user_preferences: Dict = {}
        self.topics_discussed: List[str] = []
    
    def add_turn(self, user_input: str, assistant_response: str):
        """Add a conversation turn."""
        self.history.append({
            'user': user_input,
            'assistant': assistant_response,
            'timestamp': datetime.now()
        })
        
        # Keep only recent turns
        if len(self.history) > self.max_turns:
            self.history = self.history[-self.max_turns:]
        
        # Track topics (simple keyword extraction)
        self._extract_topics(user_input)
    
    def _extract_topics(self, text: str):
        """Extract potential topics from text."""
        topic_keywords = ['weather', 'stock', 'music', 'video', 'file', 'app', 
                         'screenshot', 'volume', 'brightness', 'search']
        
        text_lower = text.lower()
        for keyword in topic_keywords:
            if keyword in text_lower and keyword not in self.topics_discussed[-5:]:
                self.topics_discussed.append(keyword)
                if len(self.topics_discussed) > 20:
                    self.topics_discussed = self.topics_discussed[-20:]
    
    def get_context(self) -> str:
        """Get conversation context for AI."""
        if not self.history:
            return ""
        
        context_parts = []
        for turn in self.history[-3:]:  # Last 3 turns
            context_parts.append(f"User: {turn['user']}")
            context_parts.append(f"April: {turn['assistant']}")
        
        return "\n".join(context_parts)
    
    def remember_preference(self, key: str, value: str):
        """Remember a user preference."""
        self.user_preferences[key] = value
    
    def get_preference(self, key: str) -> Optional[str]:
        """Get a remembered preference."""
        return self.user_preferences.get(key)


# ═══════════════════════════════════════════════════════════════════════════════
# FILE MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class FileManager:
    """Advanced file organization and cleanup manager."""
    
    def __init__(self):
        self.base_paths = {
            'Videos': USER_HOME / 'Videos',
            'Music': USER_HOME / 'Music',
            'Pictures': USER_HOME / 'Pictures',
            'Documents': USER_HOME / 'Documents',
            'Downloads': USER_HOME / 'Downloads',
        }
        
        # Extended file type mappings
        self.file_types = {
            'Videos': ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'm4v', '3gp', 'mpeg', 'mpg'],
            'Music': ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus', 'aiff'],
            'Pictures': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico', 'tiff', 'raw', 'heic', 'heif'],
            'Documents': ['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp', 'rtf', 'csv', 'epub', 'md'],
            'Archives': ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz'],
            'Code': ['py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'h', 'cs', 'php', 'rb', 'go', 'rs', 'ts', 'json', 'xml', 'yaml', 'yml', 'sh', 'bat', 'ps1'],
            'Installers': ['exe', 'msi', 'dmg', 'deb', 'rpm', 'apk'],
        }
    
    def organize_folder(self, source_folder: Path = None, organize_all: bool = False) -> Dict[str, int]:
        """Organize files in a folder by type - smart detection."""
        if source_folder is None:
            source_folder = USER_HOME / 'Downloads'
        
        moved = {folder: 0 for folder in self.file_types.keys()}
        moved['Downloads'] = 0
        
        # Create Archives and Code folders if they don't exist
        archives_path = USER_HOME / 'Documents' / 'Archives'
        code_path = USER_HOME / 'Documents' / 'Code'
        installers_path = USER_HOME / 'Downloads' / 'Installers'
        
        extended_paths = {
            'Archives': archives_path,
            'Code': code_path,
            'Installers': installers_path,
        }
        
        try:
            for item in source_folder.iterdir():
                if item.is_file():
                    ext = item.suffix.lower().lstrip('.')
                    dest_folder = self._get_destination(ext)
                    
                    if dest_folder and dest_folder != 'Downloads':
                        # Determine destination path
                        if dest_folder in extended_paths:
                            dest_path = extended_paths[dest_folder]
                        elif dest_folder in self.base_paths:
                            dest_path = self.base_paths[dest_folder]
                        else:
                            continue
                        
                        dest_path.mkdir(parents=True, exist_ok=True)
                        
                        new_path = dest_path / item.name
                        # Handle duplicate names
                        counter = 1
                        while new_path.exists():
                            stem = item.stem
                            new_path = dest_path / f"{stem}_{counter}{item.suffix}"
                            counter += 1
                        
                        item.rename(new_path)
                        moved[dest_folder] += 1
                        logger.info(f"Moved {item.name} to {dest_folder}")
        except Exception as e:
            logger.error(f"File organization error: {e}")
        
        return moved
    
    def organize_desktop(self) -> Dict[str, int]:
        """Organize files on Desktop."""
        desktop = USER_HOME / 'Desktop'
        return self.organize_folder(desktop)
    
    def _get_destination(self, extension: str) -> Optional[str]:
        """Get destination folder for file extension."""
        for folder, extensions in self.file_types.items():
            if extension in extensions:
                return folder
        return 'Downloads'
    
    def find_large_files(self, folder: Path = None, min_size_mb: int = 100) -> List[Dict]:
        """Find large files that might need cleanup."""
        if folder is None:
            folder = USER_HOME
        
        large_files = []
        min_size = min_size_mb * 1024 * 1024  # Convert to bytes
        
        try:
            for item in folder.rglob('*'):
                if item.is_file():
                    try:
                        size = item.stat().st_size
                        if size >= min_size:
                            large_files.append({
                                'path': str(item),
                                'name': item.name,
                                'size_mb': round(size / (1024 * 1024), 2)
                            })
                    except:
                        pass
        except:
            pass
        
        # Sort by size descending
        large_files.sort(key=lambda x: x['size_mb'], reverse=True)
        return large_files[:20]  # Return top 20
    
    def find_duplicate_files(self, folder: Path = None) -> List[List[str]]:
        """Find duplicate files by name (quick check)."""
        if folder is None:
            folder = USER_HOME / 'Downloads'
        
        files_by_name = {}
        try:
            for item in folder.iterdir():
                if item.is_file():
                    name_lower = item.name.lower()
                    if name_lower not in files_by_name:
                        files_by_name[name_lower] = []
                    files_by_name[name_lower].append(str(item))
        except:
            pass
        
        # Return only duplicates
        return [paths for paths in files_by_name.values() if len(paths) > 1]
    
    def clean_junk(self, folder: Path = None) -> int:
        """Remove junk and temporary files."""
        if folder is None:
            folder = USER_HOME
        
        deleted = 0
        temp_extensions = ['.tmp', '.temp', '.bak', '.old', '.log', '.cache']
        temp_prefixes = ['~', 'temp_', 'tmp_']
        junk_names = ['thumbs.db', 'desktop.ini', '.ds_store', 'ethumbs.db']
        
        # Also clean common cache locations
        cache_folders = [
            USER_HOME / 'AppData' / 'Local' / 'Temp',
        ]
        
        folders_to_clean = [folder] + [f for f in cache_folders if f.exists()]
        
        try:
            for clean_folder in folders_to_clean:
                for item in clean_folder.rglob('*'):
                    if item.is_file():
                        name = item.name.lower()
                        ext = item.suffix.lower()
                        
                        # Check if it's a junk file
                        is_junk = (
                            ext in temp_extensions or
                            any(name.startswith(p) for p in temp_prefixes) or
                            name in junk_names
                        )
                        
                        if is_junk:
                            try:
                                item.unlink()
                                deleted += 1
                                logger.info(f"Deleted junk file: {item}")
                            except PermissionError:
                                pass
        except Exception as e:
            logger.error(f"Junk cleanup error: {e}")
        
        return deleted
    
    def empty_recycle_bin(self) -> bool:
        """Empty the Windows Recycle Bin."""
        try:
            if WINDOWS_AVAILABLE:
                import ctypes
                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x0007)
                logger.info("Recycle Bin emptied")
                return True
        except Exception as e:
            logger.error(f"Could not empty Recycle Bin: {e}")
        return False
    
    def get_folder_stats(self, folder: Path = None) -> Dict:
        """Get statistics about a folder."""
        if folder is None:
            folder = USER_HOME / 'Downloads'
        
        stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'by_type': {}
        }
        
        try:
            for item in folder.iterdir():
                if item.is_file():
                    stats['total_files'] += 1
                    stats['total_size_mb'] += item.stat().st_size / (1024 * 1024)
                    ext = item.suffix.lower().lstrip('.')
                    if ext not in stats['by_type']:
                        stats['by_type'][ext] = 0
                    stats['by_type'][ext] += 1
        except:
            pass
        
        stats['total_size_mb'] = round(stats['total_size_mb'], 2)
        return stats

# ═══════════════════════════════════════════════════════════════════════════════
# WEB BROWSER
# ═══════════════════════════════════════════════════════════════════════════════

class WebBrowser:
    """Handles web browsing commands."""
    
    SHORTCUTS = {
        'youtube': 'https://www.youtube.com',
        'google': 'https://www.google.com',
        'gmail': 'https://mail.google.com',
        'facebook': 'https://www.facebook.com',
        'twitter': 'https://twitter.com',
        'x': 'https://x.com',
        'instagram': 'https://www.instagram.com',
        'linkedin': 'https://www.linkedin.com',
        'github': 'https://github.com',
        'reddit': 'https://www.reddit.com',
        'amazon': 'https://www.amazon.com',
        'netflix': 'https://www.netflix.com',
        'spotify': 'https://open.spotify.com',
        'whatsapp': 'https://web.whatsapp.com',
    }
    
    def open(self, target: str) -> bool:
        """Open a website or search query."""
        logger.info(f"[DEBUG] WebBrowser.open() called with target: '{target}'")
        target = target.lower().strip()
        
        # Check shortcuts
        if target in self.SHORTCUTS:
            url = self.SHORTCUTS[target]
            logger.info(f"[DEBUG] Matched shortcut '{target}' -> {url}")
        elif target.startswith('http://') or target.startswith('https://'):
            url = target
            logger.info(f"[DEBUG] Using direct URL: {url}")
        elif '.' in target and ' ' not in target:
            url = f'https://{target}'
            logger.info(f"[DEBUG] Adding https:// -> {url}")
        else:
            # Search Google
            url = f'https://www.google.com/search?q={target.replace(" ", "+")}'
            logger.info(f"[DEBUG] Searching Google: {url}")
        
        try:
            logger.info(f"[DEBUG] Calling webbrowser.open('{url}')")
            result = webbrowser.open(url)
            logger.info(f"[DEBUG] webbrowser.open returned: {result}")
            return True
        except Exception as e:
            logger.error(f"[DEBUG] Browser error: {e}")
            return False

# ═══════════════════════════════════════════════════════════════════════════════
# GEMINI AI - CONVERSATIONAL ASSISTANT
# ═══════════════════════════════════════════════════════════════════════════════

class GeminiAI:
    """Conversational AI using Ollama (local) as primary, Gemini as fallback."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.client = None
        self.model_name = "gemini-2.0-flash"
        self.conversation_history = []
        
        # API key rotation support
        self.api_keys = []
        self.current_key_index = 0
        self.key_error_counts = {}  # Track errors per key
        self.max_errors_per_key = 3  # Switch key after this many errors
        
        # Ollama (local AI) support - PRIMARY option
        self.ollama_available = False
        self.ollama_model = "gemma3:4b"  # Local model - Gemma 3 (fast)
        self.use_ollama = True  # ENABLED BY DEFAULT - no API needed!
        self._check_ollama()
        
        self._load_api_keys()
        self._init_client()
    
    def _check_ollama(self):
        """Check if Ollama is installed and running."""
        # Try HTTP API first (no package needed)
        try:
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            if response.status_code == 200:
                data = response.json()
                self.ollama_available = True
                
                # Check if we have any models
                if data and 'models' in data and len(data['models']) > 0:
                    # Prefer gemma3 if available, otherwise use first model
                    available_models = [m['name'] for m in data['models']]
                    gemma_models = [m for m in available_models if 'gemma' in m.lower()]
                    if gemma_models:
                        self.ollama_model = gemma_models[0]
                    else:
                        self.ollama_model = available_models[0]
                    logger.info(f"Ollama available via HTTP with model: {self.ollama_model}")
                else:
                    logger.info("Ollama running but no models installed. Run: ollama pull gemma3:4b")
                
                # Always prefer Ollama by default (no API key needed!)
                self.use_ollama = True
                return
        except:
            pass
        
        # Fallback: try ollama package
        try:
            import ollama
            models = ollama.list()
            self.ollama_available = True
            
            if models and 'models' in models and len(models['models']) > 0:
                available_models = [m['name'] for m in models['models']]
                gemma_models = [m for m in available_models if 'gemma' in m.lower()]
                if gemma_models:
                    self.ollama_model = gemma_models[0]
                else:
                    self.ollama_model = available_models[0]
                logger.info(f"Ollama available with model: {self.ollama_model}")
            else:
                logger.info("Ollama running but no models installed. Run: ollama pull gemma3:4b")
        except ImportError:
            logger.debug("Ollama package not installed and HTTP check failed")
            self.ollama_available = False
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            self.ollama_available = False
        
        # Always prefer Ollama by default
        self.use_ollama = True
    
    def _ollama_chat(self, message: str) -> str:
        """Get response from Ollama (local AI) via HTTP API."""
        try:
            import requests
            
            # Build messages with context
            messages = []
            
            # System context
            messages.append({
                'role': 'system',
                'content': f"You are April, a friendly AI assistant for {USER_NAME}. Be helpful, warm and concise."
            })
            
            # Add conversation history (last 5 messages)
            for i, msg in enumerate(self.conversation_history[-5:]):
                role = 'user' if i % 2 == 0 else 'assistant'
                messages.append({'role': role, 'content': msg})
            
            # Add current message
            messages.append({'role': 'user', 'content': message})
            
            # Call Ollama HTTP API
            response = requests.post(
                'http://localhost:11434/api/chat',
                json={
                    'model': self.ollama_model,
                    'messages': messages,
                    'stream': False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['message']['content'].strip()
            else:
                logger.error(f"Ollama HTTP error: {response.status_code}")
                return None
            
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return None
    
    def _load_api_keys(self):
        """Load all API keys (supports multiple keys separated by comma)."""
        keys_str = self.db.get_preference('gemini_api_key', '')
        
        if keys_str:
            # Split by comma and clean up
            self.api_keys = [k.strip() for k in keys_str.split(',') if k.strip()]
            # Initialize error counts
            for key in self.api_keys:
                self.key_error_counts[key] = 0
        
        logger.info(f"Loaded {len(self.api_keys)} Gemini API key(s)")
    
    def _get_current_key(self) -> str:
        """Get the current API key."""
        if not self.api_keys:
            return ''
        return self.api_keys[self.current_key_index % len(self.api_keys)]
    
    def _rotate_key(self, mark_error: bool = True):
        """Rotate to the next API key."""
        if len(self.api_keys) <= 1:
            return False
        
        if mark_error:
            current_key = self._get_current_key()
            self.key_error_counts[current_key] = self.key_error_counts.get(current_key, 0) + 1
        
        old_index = self.current_key_index
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        
        logger.info(f"Rotated API key: {old_index + 1} → {self.current_key_index + 1} of {len(self.api_keys)}")
        
        # Reinitialize client with new key
        self._init_client()
        return True
    
    def _init_client(self):
        """Initialize Gemini client."""
        api_key = self._get_current_key()
        
        if not api_key:
            logger.info("Gemini API key not configured - AI chat disabled")
            return
        
        try:
            from google import genai
            
            self.client = genai.Client(api_key=api_key)
            self.chat = self.client.chats.create(model=self.model_name)
            
            key_num = self.current_key_index + 1
            total_keys = len(self.api_keys)
            logger.info(f"Gemini AI initialized successfully (key {key_num}/{total_keys})")
        except Exception as e:
            logger.error(f"Gemini initialization failed: {e}")
            self.client = None
            self.chat = None
    
    def is_available(self) -> bool:
        """Check if any AI (Ollama or Gemini) is available."""
        return self.ollama_available or self.client is not None
    
    def get_key_status(self) -> str:
        """Get current API key status for display."""
        status_parts = []
        
        if self.use_ollama and self.ollama_available:
            status_parts.append(f"🏠 Ollama: {self.ollama_model} (Local - Unlimited)")
        
        if self.api_keys:
            status_parts.append(f"☁️ Gemini: key {self.current_key_index + 1}/{len(self.api_keys)}")
        
        if not status_parts:
            return "No AI configured"
        
        return " | ".join(status_parts)
    
    def chat_response(self, message: str) -> str:
        """Get a conversational response - uses Ollama if enabled, otherwise Gemini."""
        
        # If user prefers Ollama and it's available, use it first
        if self.use_ollama and self.ollama_available:
            response = self._ollama_chat(message)
            if response:
                self.conversation_history.append(message)
                return response
            # If Ollama fails, fall through to Gemini
        
        # Use Gemini
        if not self.is_available():
            # Last resort: try Ollama even if not preferred
            if self.ollama_available:
                response = self._ollama_chat(message)
                if response:
                    self.conversation_history.append(message)
                    return response
            return None
        
        try:
            # Add context about being April
            if not self.conversation_history:
                context = f"You are April, a friendly AI assistant for {USER_NAME}. Be helpful, warm and concise. "
                message = context + message
            
            response = self.chat.send_message(message)
            self.conversation_history.append(message)
            
            # Reset error count on success
            current_key = self._get_current_key()
            self.key_error_counts[current_key] = 0
            
            return response.text.strip()
        except Exception as e:
            error_str = str(e)
            logger.error(f"Gemini chat error: {e}")
            
            # Check if rate limited or quota exceeded
            if "429" in error_str or "quota" in error_str.lower() or "resource" in error_str.lower():
                # Try rotating to next key
                if self._rotate_key(mark_error=True):
                    logger.info("Rate limited - trying next API key...")
                    return self.chat_response(message)
                
                # All keys exhausted - try Ollama as fallback
                if self.ollama_available:
                    logger.info("All API keys exhausted - falling back to Ollama")
                    response = self._ollama_chat(message)
                    if response:
                        self.conversation_history.append(message)
                        return response
                
                return "Sorry, all API keys have hit their limit. Install Ollama for unlimited local AI!"
            
            elif "401" in error_str or "invalid" in error_str.lower():
                if self._rotate_key(mark_error=True):
                    return self.chat_response(message)
                return "My API key seems invalid. Please check Settings and update it."
            
            return f"Sorry, I had trouble with that. Try again?"
    
    def quick_response(self, message: str) -> str:
        """Get a one-off response without chat history."""
        if not self.client:
            return None
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=message
            )
            return response.text.strip()
        except Exception as e:
            error_str = str(e)
            logger.error(f"Gemini quick response error: {e}")
            
            # Try rotating on rate limit
            if "429" in error_str or "quota" in error_str.lower():
                if self._rotate_key(mark_error=True):
                    return self.quick_response(message)
            return None
    
    def reload_api_key(self):
        """Reload API keys and reinitialize client."""
        self.conversation_history = []
        self.current_key_index = 0
        self._load_api_keys()
        self._init_client()

# ═══════════════════════════════════════════════════════════════════════════════
# MARKET DATA
# ═══════════════════════════════════════════════════════════════════════════════

class MarketData:
    """Fetches and analyzes market data."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.api_key = db.get_preference('alpha_vantage_key', '')
    
    def get_stock(self, symbol: str) -> Dict[str, Any]:
        """Get stock price and info."""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            hist = stock.history(period='1d')
            
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                open_price = hist['Open'].iloc[-1]
                change = ((price - open_price) / open_price) * 100
                
                data = {
                    'symbol': symbol.upper(),
                    'price': round(price, 2),
                    'change_percent': round(change, 2),
                    'name': info.get('shortName', symbol),
                    'volume': hist['Volume'].iloc[-1],
                    'high': hist['High'].iloc[-1],
                    'low': hist['Low'].iloc[-1],
                }
                
                # Log to database
                self.db.log_market_data(
                    symbol.upper(), 'stock', price, change, 
                    data['volume'], data
                )
                
                return data
        except Exception as e:
            logger.error(f"Stock data error for {symbol}: {e}")
        
        return None
    
    def get_crypto(self, symbol: str = 'BTC-USD') -> Dict[str, Any]:
        """Get cryptocurrency price."""
        return self.get_stock(symbol)
    
    def get_forex(self, pair: str = 'EURUSD=X') -> Dict[str, Any]:
        """Get forex rate."""
        return self.get_stock(pair)
    
    def get_commodity(self, commodity: str = 'GC=F') -> Dict[str, Any]:
        """Get commodity price (GC=F for Gold, SI=F for Silver)."""
        return self.get_stock(commodity)
    
    def analyze_trend(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """Analyze price trend and suggest trading opportunities."""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=f'{days}d')
            
            if hist.empty:
                return None
            
            # Calculate indicators
            prices = hist['Close'].values
            sma_short = np.mean(prices[-5:])  # 5-day SMA
            sma_long = np.mean(prices[-20:]) if len(prices) >= 20 else np.mean(prices)
            
            # Simple trend analysis
            trend = 'bullish' if sma_short > sma_long else 'bearish'
            
            # Calculate RSI (simplified)
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else np.mean(gains)
            avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else np.mean(losses)
            rs = avg_gain / avg_loss if avg_loss != 0 else 100
            rsi = 100 - (100 / (1 + rs))
            
            # Generate suggestion
            if rsi < 30:
                suggestion = f"{symbol} appears oversold (RSI: {rsi:.1f}). Consider buying opportunity."
                confidence = 0.7
            elif rsi > 70:
                suggestion = f"{symbol} appears overbought (RSI: {rsi:.1f}). Consider taking profits."
                confidence = 0.7
            elif trend == 'bullish':
                suggestion = f"{symbol} shows bullish trend. Short-term MA above long-term MA."
                confidence = 0.5
            else:
                suggestion = f"{symbol} shows bearish trend. Consider waiting for reversal."
                confidence = 0.5
            
            return {
                'symbol': symbol,
                'trend': trend,
                'rsi': round(rsi, 1),
                'sma_short': round(sma_short, 2),
                'sma_long': round(sma_long, 2),
                'suggestion': suggestion,
                'confidence': confidence
            }
            
        except Exception as e:
            logger.error(f"Trend analysis error: {e}")
            return None
    
    def get_market_summary(self) -> str:
        """Get daily market summary."""
        indices = {
            '^GSPC': 'S&P 500',
            '^DJI': 'Dow Jones',
            '^IXIC': 'NASDAQ',
            'BTC-USD': 'Bitcoin',
            'GC=F': 'Gold',
        }
        
        summary_parts = ["📊 Market Summary:\n"]
        
        for symbol, name in indices.items():
            data = self.get_stock(symbol)
            if data:
                arrow = '📈' if data['change_percent'] > 0 else '📉'
                summary_parts.append(
                    f"{arrow} {name}: ${data['price']:,.2f} ({data['change_percent']:+.2f}%)"
                )
        
        return '\n'.join(summary_parts)

# ═══════════════════════════════════════════════════════════════════════════════
# WEATHER SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class WeatherService:
    """Provides weather information."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.api_key = db.get_preference('openweather_key', '')
    
    def get_weather(self, city: str = 'New York') -> Dict[str, Any]:
        """Get current weather for a city."""
        if not self.api_key:
            # Use a free weather API that doesn't require key
            return self._get_weather_fallback(city)
        
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric'
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            return {
                'city': data['name'],
                'temp': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'description': data['weather'][0]['description'],
                'humidity': data['main']['humidity'],
                'wind': data['wind']['speed']
            }
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return None
    
    def _get_weather_fallback(self, city: str) -> Dict[str, Any]:
        """Fallback weather using wttr.in."""
        try:
            url = f"https://wttr.in/{city}?format=j1"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            current = data['current_condition'][0]
            return {
                'city': city,
                'temp': float(current['temp_C']),
                'feels_like': float(current['FeelsLikeC']),
                'description': current['weatherDesc'][0]['value'],
                'humidity': int(current['humidity']),
                'wind': float(current['windspeedKmph'])
            }
        except Exception as e:
            logger.error(f"Weather fallback error: {e}")
            return None
    
    def get_forecast(self, city: str = 'New York') -> str:
        """Get weather forecast."""
        try:
            url = f"https://wttr.in/{city}?format=3"
            response = requests.get(url, timeout=10)
            return response.text.strip()
        except:
            return "Weather forecast unavailable"

# ═══════════════════════════════════════════════════════════════════════════════
# GOOGLE SEARCH SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class GoogleSearchService:
    """Provides Google Custom Search API integration."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.api_key = db.get_preference('google_api_key', '')
        self.search_engine_id = db.get_preference('google_cse_id', '')
    
    def is_available(self) -> bool:
        """Check if Google Search API is configured."""
        return bool(self.api_key)
    
    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Perform a Google search and return results."""
        if not self.api_key:
            return []
        
        try:
            # Use Google Custom Search JSON API
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id if self.search_engine_id else '017576662512468239146:omuauf_gy2o',  # Public CSE
                'q': query,
                'num': min(num_results, 10)
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            results = []
            if 'items' in data:
                for item in data['items']:
                    results.append({
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                    })
            
            logger.info(f"Google Search: Found {len(results)} results for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Google Search API error: {e}")
            return []
    
    def search_summary(self, query: str) -> str:
        """Get a formatted summary of search results."""
        results = self.search(query, num_results=3)
        
        if not results:
            return f"No results found for '{query}'. Opening browser search instead."
        
        summary_parts = [f"🔍 Search results for '{query}':\n"]
        for i, result in enumerate(results, 1):
            summary_parts.append(f"{i}. **{result['title']}**")
            summary_parts.append(f"   {result['snippet']}")
            summary_parts.append(f"   🔗 {result['link']}\n")
        
        return '\n'.join(summary_parts)
    
    def reload_api_key(self):
        """Reload API key from database."""
        self.api_key = self.db.get_preference('google_api_key', '')
        self.search_engine_id = self.db.get_preference('google_cse_id', '')

# ═══════════════════════════════════════════════════════════════════════════════
# SCREEN CAPTURE
# ═══════════════════════════════════════════════════════════════════════════════

class ScreenCapture:
    """Handles screenshot and screen recording."""
    
    def __init__(self):
        self.screenshots_dir = USER_HOME / 'Pictures' / 'April Screenshots'
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.recording = False
        self.recording_thread = None
    
    def take_screenshot(self) -> Path:
        """Take a screenshot and save it."""
        try:
            with mss.mss() as sct:
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                filepath = self.screenshots_dir / filename
                sct.shot(output=str(filepath))
                logger.info(f"Screenshot saved: {filepath}")
                return filepath
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return None
    
    def analyze_screen(self) -> str:
        """Take screenshot and provide basic analysis."""
        screenshot_path = self.take_screenshot()
        if screenshot_path:
            # In a full implementation, this would use OCR or image recognition
            return f"Screenshot captured and saved to {screenshot_path}. Visual analysis would require additional AI integration."
        return "Failed to capture screenshot."
    
    def start_recording(self, duration: int = 30) -> bool:
        """Start screen recording."""
        if self.recording:
            return False
        
        self.recording = True
        self.recording_thread = threading.Thread(
            target=self._record_screen, 
            args=(duration,),
            daemon=True
        )
        self.recording_thread.start()
        return True
    
    def stop_recording(self):
        """Stop screen recording."""
        self.recording = False
    
    def _record_screen(self, duration: int):
        """Record screen for specified duration."""
        try:
            filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
            filepath = self.screenshots_dir / filename
            
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                width = monitor['width']
                height = monitor['height']
                
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                out = cv2.VideoWriter(str(filepath), fourcc, 10.0, (width, height))
                
                start_time = time.time()
                while self.recording and (time.time() - start_time) < duration:
                    img = np.array(sct.grab(monitor))
                    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    out.write(frame)
                
                out.release()
                logger.info(f"Recording saved: {filepath}")
                
        except Exception as e:
            logger.error(f"Recording error: {e}")
        finally:
            self.recording = False

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM CONTROL
# ═══════════════════════════════════════════════════════════════════════════════

class SystemControl:
    """Controls system functions."""
    
    def shutdown(self, delay: int = 5) -> bool:
        """Shutdown the computer."""
        try:
            os.system(f'shutdown /s /t {delay}')
            logger.info(f"System will shutdown in {delay} seconds")
            return True
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
            return False
    
    def restart(self, delay: int = 5) -> bool:
        """Restart the computer."""
        try:
            os.system(f'shutdown /r /t {delay}')
            logger.info(f"System will restart in {delay} seconds")
            return True
        except Exception as e:
            logger.error(f"Restart error: {e}")
            return False
    
    def cancel_shutdown(self) -> bool:
        """Cancel pending shutdown."""
        try:
            os.system('shutdown /a')
            return True
        except:
            return False
    
    def lock(self) -> bool:
        """Lock the screen."""
        try:
            if WINDOWS_AVAILABLE:
                import ctypes
                ctypes.windll.user32.LockWorkStation()
            else:
                os.system('rundll32.exe user32.dll,LockWorkStation')
            logger.info("Screen locked")
            return True
        except Exception as e:
            logger.error(f"Lock error: {e}")
            return False
    
    def set_volume(self, level: int = None, action: str = None) -> bool:
        """Set or adjust system volume."""
        try:
            if WINDOWS_AVAILABLE:
                if action == 'mute':
                    for _ in range(50):  # Mute by setting to 0
                        win32api.keybd_event(win32con.VK_VOLUME_DOWN, 0)
                        win32api.keybd_event(win32con.VK_VOLUME_DOWN, 0, win32con.KEYEVENTF_KEYUP)
                elif action == 'up':
                    for _ in range(5):
                        win32api.keybd_event(win32con.VK_VOLUME_UP, 0)
                        win32api.keybd_event(win32con.VK_VOLUME_UP, 0, win32con.KEYEVENTF_KEYUP)
                elif action == 'down':
                    for _ in range(5):
                        win32api.keybd_event(win32con.VK_VOLUME_DOWN, 0)
                        win32api.keybd_event(win32con.VK_VOLUME_DOWN, 0, win32con.KEYEVENTF_KEYUP)
                logger.info(f"Volume adjusted: {action or level}")
                return True
            else:
                # Use nircmd as fallback
                if level is not None:
                    os.system(f'nircmd.exe setsysvolume {level * 655}')
                return True
        except Exception as e:
            logger.error(f"Volume error: {e}")
            return False
    
    def set_brightness(self, level: int) -> bool:
        """Set screen brightness."""
        try:
            if BRIGHTNESS_AVAILABLE:
                sbc.set_brightness(level)
                logger.info(f"Brightness set to {level}%")
                return True
        except Exception as e:
            logger.error(f"Brightness error: {e}")
        return False
    
    def open_application(self, app_name: str) -> bool:
        """Open ANY application - smart detection with multiple fallback methods."""
        app_map = {
            # Windows built-in apps (UWP/Modern)
            'camera': 'microsoft.windows.camera:',
            'photos': 'ms-photos:',
            'calendar': 'outlookcal:',
            'mail': 'outlookmail:',
            'store': 'ms-windows-store:',
            'clock': 'ms-clock:',
            'calculator': 'calculator:',
            'calc': 'calculator:',
            'snipping tool': 'ms-screenclip:',
            'settings': 'ms-settings:',
            'maps': 'bingmaps:',
            'weather': 'bingweather:',
            'onenote': 'onenote:',
            
            # Classic Windows apps
            'notepad': 'notepad.exe',
            'paint': 'mspaint.exe',
            'cmd': 'cmd.exe',
            'command prompt': 'cmd.exe',
            'terminal': 'wt.exe',
            'powershell': 'powershell.exe',
            'explorer': 'explorer.exe',
            'file explorer': 'explorer.exe',
            'task manager': 'taskmgr.exe',
            'control panel': 'control.exe',
            'media player': 'wmplayer.exe',
            'vlc': 'vlc.exe',
            
            # Microsoft Office
            'word': 'winword.exe',
            'excel': 'excel.exe',
            'powerpoint': 'powerpnt.exe',
            'outlook': 'outlook.exe',
            
            # Browsers
            'chrome': 'chrome.exe',
            'firefox': 'firefox.exe',
            'edge': 'msedge.exe',
            'browser': 'msedge.exe',  # Default browser
            
            # Communication
            'discord': 'discord.exe',
            'slack': 'slack.exe',
            'teams': 'teams.exe',
            'zoom': 'zoom.exe',
            'skype': 'skype.exe',
            'whatsapp': 'whatsapp.exe',
            'telegram': 'telegram.exe',
            
            # Development
            'code': 'code.exe',
            'visual studio': 'devenv.exe',
            'vs code': 'code.exe',
            'vscode': 'code.exe',
            
            # Entertainment
            'spotify': 'spotify.exe',
            'steam': 'steam.exe',
            'epic games': 'EpicGamesLauncher.exe',
            
            # Cloud storage
            'onedrive': 'onedrive.exe',
        }
        
        app_name = app_name.lower().strip()
        
        try:
            # Method 1: Check if it's a known app
            if app_name in app_map:
                target = app_map[app_name]
                if target.endswith(':'):
                    # UWP/Modern app URI scheme
                    os.startfile(target)
                    logger.info(f"Opened UWP app: {app_name}")
                    return True
                else:
                    # Traditional executable
                    try:
                        os.startfile(target)
                        logger.info(f"Opened app: {app_name}")
                        return True
                    except FileNotFoundError:
                        # Try running via shell
                        subprocess.Popen(target, shell=True)
                        return True
            
            # Method 2: Smart search for ANY application
            app_clean = app_name.replace(' ', '')
            found = False
            
            # 2a: Try direct exe name
            for exe_name in [f'{app_name}.exe', f'{app_clean}.exe']:
                try:
                    subprocess.Popen(exe_name, shell=True)
                    logger.info(f"Opened via shell: {exe_name}")
                    found = True
                    return True
                except:
                    pass
            
            # 2b: Search Start Menu shortcuts (fastest way to find apps)
            start_menu_paths = [
                os.path.expandvars(r'%APPDATA%\Microsoft\Windows\Start Menu\Programs'),
                os.path.expandvars(r'%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs'),
            ]
            
            for start_path in start_menu_paths:
                if os.path.exists(start_path):
                    for root, dirs, files in os.walk(start_path):
                        for f in files:
                            if f.lower().endswith('.lnk'):
                                # Check if shortcut name matches
                                shortcut_name = f[:-4].lower()  # Remove .lnk
                                if app_clean in shortcut_name or app_name in shortcut_name:
                                    shortcut_path = os.path.join(root, f)
                                    os.startfile(shortcut_path)
                                    logger.info(f"Opened via Start Menu shortcut: {shortcut_path}")
                                    return True
            
            # 2c: Search in common installation paths
            common_paths = [
                os.path.expandvars(r'%LOCALAPPDATA%\Programs'),
                os.path.expandvars(r'%PROGRAMFILES%'),
                os.path.expandvars(r'%PROGRAMFILES(X86)%'),
                os.path.expandvars(r'%APPDATA%'),
                os.path.expandvars(r'%LOCALAPPDATA%'),
            ]
            
            for base_path in common_paths:
                if os.path.exists(base_path):
                    for root, dirs, files in os.walk(base_path):
                        for f in files:
                            if f.lower().endswith('.exe'):
                                f_lower = f.lower()[:-4]  # Remove .exe
                                if app_clean in f_lower or f_lower in app_clean or app_name.split()[0] in f_lower:
                                    try:
                                        exe_path = os.path.join(root, f)
                                        os.startfile(exe_path)
                                        logger.info(f"Opened via search: {exe_path}")
                                        return True
                                    except:
                                        pass
                        # Only search top 3 levels to avoid slowdown
                        if root.count(os.sep) - base_path.count(os.sep) >= 3:
                            dirs.clear()
            
            # Method 3: Use Windows search via pyautogui (last resort - always works!)
            import pyautogui
            pyautogui.hotkey('win')
            time.sleep(0.5)
            pyautogui.typewrite(app_name.replace(' ', ''), interval=0.03)
            time.sleep(0.8)
            pyautogui.press('enter')
            logger.info(f"Opened via Windows search: {app_name}")
            return True
                    
        except Exception as e:
            logger.error(f"Open application error: {e}")
            return False
    
    def close_application(self, app_name: str) -> bool:
        """Close ANY application by name - smart process detection."""
        # Map friendly names to actual process names
        process_map = {
            'camera': 'WindowsCamera',
            'calculator': 'Calculator',
            'calc': 'Calculator',
            'notepad': 'notepad',
            'paint': 'mspaint',
            'chrome': 'chrome',
            'firefox': 'firefox',
            'edge': 'msedge',
            'browser': 'msedge',
            'spotify': 'Spotify',
            'discord': 'Discord',
            'slack': 'slack',
            'teams': 'Teams',
            'zoom': 'Zoom',
            'skype': 'Skype',
            'vlc': 'vlc',
            'photos': 'Microsoft.Photos',
            'explorer': 'explorer',
            'file explorer': 'explorer',
            'word': 'WINWORD',
            'excel': 'EXCEL',
            'powerpoint': 'POWERPNT',
            'outlook': 'OUTLOOK',
            'code': 'Code',
            'visual studio': 'devenv',
            'vs code': 'Code',
            'vscode': 'Code',
            'steam': 'steam',
            'whatsapp': 'WhatsApp',
            'telegram': 'Telegram',
            'onenote': 'ONENOTE',
        }
        
        try:
            app_lower = app_name.lower().strip()
            
            # Check if we have a known mapping
            if app_lower in process_map:
                process_name = process_map[app_lower]
                result = os.system(f'taskkill /IM {process_name}.exe /F 2>nul')
                if result == 0:
                    logger.info(f"Closed application: {app_name} (process: {process_name})")
                    return True
            
            # Method 1: Try the app name directly as process name
            result = os.system(f'taskkill /IM {app_name}.exe /F 2>nul')
            if result == 0:
                logger.info(f"Closed application: {app_name}")
                return True
            
            # Method 2: Try without spaces
            app_clean = app_name.replace(' ', '')
            result = os.system(f'taskkill /IM {app_clean}.exe /F 2>nul')
            if result == 0:
                logger.info(f"Closed application: {app_clean}")
                return True
            
            # Method 3: Find and kill by window title (partial match)
            try:
                # Get list of running processes and find matching ones
                import subprocess
                output = subprocess.check_output('tasklist /FO CSV /NH', shell=True, text=True)
                for line in output.strip().split('\n'):
                    if line:
                        parts = line.split('","')
                        if len(parts) >= 2:
                            proc_name = parts[0].strip('"').lower()
                            if app_lower in proc_name or app_clean in proc_name:
                                # Found a matching process
                                actual_name = parts[0].strip('"')
                                result = os.system(f'taskkill /IM "{actual_name}" /F 2>nul')
                                if result == 0:
                                    logger.info(f"Closed via process scan: {actual_name}")
                                    return True
            except:
                pass
            
            # Method 4: Kill by window title
            try:
                result = os.system(f'taskkill /FI "WINDOWTITLE eq *{app_name}*" /F 2>nul')
                if result == 0:
                    logger.info(f"Closed by window title: {app_name}")
                    return True
            except:
                pass
            
            logger.warning(f"Could not find process for: {app_name}")
            return False
            
        except Exception as e:
            logger.error(f"Close application error: {e}")
            return False
    
    def get_running_processes(self) -> List[str]:
        """Get list of running processes."""
        try:
            result = subprocess.run(
                ['tasklist', '/FO', 'CSV', '/NH'],
                capture_output=True, text=True
            )
            processes = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    name = line.split(',')[0].strip('"')
                    if name not in processes:
                        processes.append(name)
            return processes
        except:
            return []

# ═══════════════════════════════════════════════════════════════════════════════
# GAMING LAUNCHER
# ═══════════════════════════════════════════════════════════════════════════════

class GamingLauncher:
    """Launches games."""
    
    # Common game locations
    GAME_PATHS = {
        'angry birds': [
            r'C:\Program Files\Angry Birds',
            r'C:\Program Files (x86)\Angry Birds',
            r'C:\Games\Angry Birds',
        ],
        'minecraft': [
            r'C:\Program Files (x86)\Minecraft Launcher\MinecraftLauncher.exe',
        ],
    }
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.custom_games = {}
        self._load_custom_games()
    
    def _load_custom_games(self):
        """Load custom game paths from database."""
        games_json = self.db.get_preference('custom_games', '{}')
        try:
            self.custom_games = json.loads(games_json)
        except:
            self.custom_games = {}
    
    def add_game(self, name: str, path: str):
        """Add a custom game path."""
        self.custom_games[name.lower()] = path
        self.db.save_preference('custom_games', json.dumps(self.custom_games))
    
    def launch(self, game_name: str) -> bool:
        """Launch a game."""
        game_name = game_name.lower().strip()
        
        # Check custom games first
        if game_name in self.custom_games:
            try:
                os.startfile(self.custom_games[game_name])
                logger.info(f"Launched game: {game_name}")
                return True
            except:
                pass
        
        # Check known game paths
        if game_name in self.GAME_PATHS:
            for path in self.GAME_PATHS[game_name]:
                if os.path.exists(path):
                    try:
                        os.startfile(path)
                        logger.info(f"Launched game: {game_name}")
                        return True
                    except:
                        continue
        
        # Try to launch via Steam if available
        try:
            steam_url = f'steam://run/{game_name}'
            webbrowser.open(steam_url)
            return True
        except:
            pass
        
        logger.warning(f"Game not found: {game_name}")
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# WHATSAPP HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

class WhatsAppHandler:
    """Handles WhatsApp call interception (simplified version)."""
    
    def __init__(self, db: DatabaseManager, voice_engine: VoiceEngine):
        self.db = db
        self.voice_engine = voice_engine
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start monitoring for WhatsApp calls."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("WhatsApp monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring = False
    
    def _monitor_loop(self):
        """Monitor for incoming WhatsApp calls."""
        while self.monitoring:
            try:
                # Check for WhatsApp notification window
                # This is a simplified implementation
                # Full implementation would use Windows notification APIs
                if WINDOWS_AVAILABLE:
                    window = win32gui.FindWindow(None, "WhatsApp")
                    if window:
                        # Check for incoming call indicators
                        # This would need more sophisticated detection
                        pass
            except Exception as e:
                logger.error(f"WhatsApp monitoring error: {e}")
            
            time.sleep(1)
    
    def handle_incoming_call(self, caller_name: str) -> bool:
        """Handle incoming call with voice prompt."""
        self.voice_engine.speak(f"Are you okay, {USER_NAME}?")
        
        # Wait for response
        response = self.voice_engine.listen(timeout=5)
        
        if response and ('yes' in response or 'yeah' in response or 'okay' in response):
            self.db.log_call(caller_name, "", "accepted", 0)
            return True  # Let call through
        else:
            # Auto-answer with message
            self.voice_engine.speak(
                f"Hi, I am April, {USER_NAME}'s personal assistant. "
                f"{USER_NAME} is currently busy, please call back later."
            )
            self.db.log_call(caller_name, "", "auto_declined", 0)
            return False  # Decline call

# ═══════════════════════════════════════════════════════════════════════════════
# TASK SCHEDULER
# ═══════════════════════════════════════════════════════════════════════════════

class TaskScheduler:
    """Manages scheduled tasks and reminders."""
    
    def __init__(self, db: DatabaseManager, voice_engine: VoiceEngine):
        self.db = db
        self.voice_engine = voice_engine
        self.running = False
        self.scheduler_thread = None
    
    def start(self):
        """Start the scheduler."""
        if self.running:
            return
        
        self.running = True
        self._load_tasks()
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Task scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        schedule.clear()
    
    def _load_tasks(self):
        """Load tasks from database."""
        tasks = self.db.get_active_tasks()
        for task in tasks:
            self._schedule_task(task)
    
    def _schedule_task(self, task: Dict):
        """Schedule a task."""
        try:
            if task['recurrence'] == 'daily':
                schedule.every().day.at(task['schedule_time']).do(
                    self._execute_task, task['command'], task['task_name']
                )
            elif task['recurrence'] == 'hourly':
                schedule.every().hour.do(
                    self._execute_task, task['command'], task['task_name']
                )
            elif task['recurrence'] == 'once':
                # Schedule once - will be handled differently
                pass
        except Exception as e:
            logger.error(f"Task scheduling error: {e}")
    
    def _execute_task(self, command: str, name: str):
        """Execute a scheduled task."""
        logger.info(f"Executing scheduled task: {name}")
        self.voice_engine.speak(f"Reminder: {command}")
    
    def _run_scheduler(self):
        """Run the schedule loop."""
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def add_reminder(self, message: str, time_str: str) -> bool:
        """Add a reminder."""
        try:
            task_id = self.db.add_scheduled_task(
                f"Reminder: {message[:30]}",
                'reminder',
                time_str,
                'once',
                message
            )
            logger.info(f"Reminder added: {message} at {time_str}")
            return True
        except Exception as e:
            logger.error(f"Add reminder error: {e}")
            return False

# ═══════════════════════════════════════════════════════════════════════════════
# FEEDBACK SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class FeedbackSystem:
    """Collects user feedback to improve suggestions."""
    
    def __init__(self, db: DatabaseManager, voice_engine: VoiceEngine):
        self.db = db
        self.voice_engine = voice_engine
    
    def request_feedback(self, feature: str) -> Optional[int]:
        """Request feedback from user."""
        self.voice_engine.speak(
            f"How would you rate my {feature} suggestion? "
            "Say a number from 1 to 5, where 5 is excellent."
        )
        
        response = self.voice_engine.listen(timeout=5)
        if response:
            # Extract number from response
            numbers = re.findall(r'\d', response)
            if numbers:
                rating = int(numbers[0])
                if 1 <= rating <= 5:
                    self.db.log_feedback(feature, rating)
                    self.voice_engine.speak("Thank you for your feedback!")
                    return rating
        
        return None
    
    def get_average_rating(self, feature: str) -> float:
        """Get average rating for a feature."""
        cursor = self.db.conn.cursor()
        cursor.execute(
            'SELECT AVG(rating) FROM feedback WHERE feature = ?',
            (feature,)
        )
        result = cursor.fetchone()[0]
        return result if result else 0.0

# ═══════════════════════════════════════════════════════════════════════════════
# WINDOWS STARTUP MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class StartupManager:
    """Manages Windows startup integration."""
    
    STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    def add_to_startup(self) -> bool:
        """Add April to Windows startup."""
        try:
            if WINDOWS_AVAILABLE:
                import winreg
                
                script_path = os.path.abspath(sys.argv[0])
                python_path = sys.executable
                
                # Create command
                command = f'"{python_path}" "{script_path}" --minimized'
                
                # Open registry key
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    self.STARTUP_KEY,
                    0,
                    winreg.KEY_SET_VALUE
                )
                
                winreg.SetValueEx(key, "April", 0, winreg.REG_SZ, command)
                winreg.CloseKey(key)
                
                logger.info("Added to Windows startup")
                return True
        except Exception as e:
            logger.error(f"Startup registration error: {e}")
        return False
    
    def remove_from_startup(self) -> bool:
        """Remove April from Windows startup."""
        try:
            if WINDOWS_AVAILABLE:
                import winreg
                
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    self.STARTUP_KEY,
                    0,
                    winreg.KEY_SET_VALUE
                )
                
                winreg.DeleteValue(key, "April")
                winreg.CloseKey(key)
                
                logger.info("Removed from Windows startup")
                return True
        except Exception as e:
            logger.error(f"Startup removal error: {e}")
        return False
    
    def is_in_startup(self) -> bool:
        """Check if April is in startup."""
        try:
            if WINDOWS_AVAILABLE:
                import winreg
                
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    self.STARTUP_KEY,
                    0,
                    winreg.KEY_READ
                )
                
                try:
                    winreg.QueryValueEx(key, "April")
                    return True
                except FileNotFoundError:
                    return False
                finally:
                    winreg.CloseKey(key)
        except:
            pass
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# APRIL MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

class AprilApp:
    """Main April application with GUI and voice control."""
    
    def __init__(self, start_minimized: bool = False):
        self.start_minimized = start_minimized
        
        # Initialize components
        self.db = DatabaseManager()
        self.voice_engine = VoiceEngine()
        self.command_parser = CommandParser()
        self.voice_profile = VoiceProfileManager(self.db)
        self.local_intelligence = LocalIntelligence()  # Built-in smart responses
        
        # Initialize features
        self.file_manager = FileManager()
        self.web_browser = WebBrowser()
        self.market_data = MarketData(self.db)
        self.weather_service = WeatherService(self.db)
        self.google_search = GoogleSearchService(self.db)  # Google Search API
        self.screen_capture = ScreenCapture()
        self.system_control = SystemControl()
        self.gaming_launcher = GamingLauncher(self.db)
        self.whatsapp_handler = WhatsAppHandler(self.db, self.voice_engine)
        self.gemini_ai = GeminiAI(self.db)  # Conversational AI
        self.task_scheduler = TaskScheduler(self.db, self.voice_engine)
        self.feedback_system = FeedbackSystem(self.db, self.voice_engine)
        self.startup_manager = StartupManager()
        
        # Wake word detector
        self.wake_word_detector = WakeWordDetector(self.voice_engine, self.on_wake_word)
        
        # State
        self.is_active = False
        self.is_minimized = False
        self.continuous_listening = False  # Continuous listening mode
        self.listening_thread = None
        
        # Debounce: prevent duplicate commands
        self._last_command = ""
        self._last_command_time = 0
        self._command_cooldown = 3.0  # seconds to ignore duplicate commands
        
        # Create GUI
        self._create_gui()
        
        # Create system tray
        self._create_tray_icon()
    
    def _create_gui(self):
        """Create the main GUI."""
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} - Personal AI Assistant")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Dark mode colors
        self.colors = {
            'bg': '#1a1a2e',
            'secondary_bg': '#16213e',
            'accent': '#0f3460',
            'text': '#e94560',
            'text_light': '#ffffff',
            'text_muted': '#888888',
            'success': '#00ff88',
            'warning': '#ffcc00',
            'error': '#ff4444',
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.style.configure('TFrame', background=self.colors['bg'])
        self.style.configure('TLabel', 
                           background=self.colors['bg'], 
                           foreground=self.colors['text_light'])
        self.style.configure('TButton', 
                           background=self.colors['accent'],
                           foreground=self.colors['text_light'])
        self.style.configure('Header.TLabel',
                           font=('Segoe UI', 24, 'bold'),
                           foreground=self.colors['text'])
        self.style.configure('Status.TLabel',
                           font=('Segoe UI', 10),
                           foreground=self.colors['success'])
        
        # Main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="🤖 April", style='Header.TLabel').pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(header_frame, text="● Listening", style='Status.TLabel')
        self.status_label.pack(side=tk.RIGHT)
        
        # Chat display
        chat_frame = ttk.Frame(self.main_frame)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=('Consolas', 11),
            bg=self.colors['secondary_bg'],
            fg=self.colors['text_light'],
            insertbackground=self.colors['text'],
            selectbackground=self.colors['accent'],
            relief=tk.FLAT,
            padx=15,
            pady=15
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)
        
        # Input frame
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.input_entry = tk.Entry(
            input_frame,
            font=('Segoe UI', 12),
            bg=self.colors['secondary_bg'],
            fg=self.colors['text_light'],
            insertbackground=self.colors['text'],
            relief=tk.FLAT
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=8)
        self.input_entry.bind('<Return>', self.on_text_input)
        
        # Voice button (toggle continuous listening)
        self.voice_btn = tk.Button(
            input_frame,
            text="🎤",
            font=('Segoe UI', 14),
            bg=self.colors['error'],  # Red when not listening
            fg=self.colors['text_light'],
            relief=tk.FLAT,
            width=4,
            command=self.toggle_continuous_listening
        )
        self.voice_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Settings button
        settings_btn = tk.Button(
            input_frame,
            text="⚙️",
            font=('Segoe UI', 14),
            bg=self.colors['accent'],
            fg=self.colors['text_light'],
            relief=tk.FLAT,
            width=4,
            command=self.open_settings
        )
        settings_btn.pack(side=tk.LEFT)
        
        # Button frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        quick_buttons = [
            ("📊 Market", lambda: self.process_command("market summary")),
            ("🌤️ Weather", lambda: self.process_command("weather")),
            ("📁 Organize", lambda: self.process_command("organize files")),
            ("📸 Screenshot", lambda: self.process_command("screenshot")),
            ("📜 History", lambda: self.process_command("command history")),
        ]
        
        for text, command in quick_buttons:
            btn = tk.Button(
                button_frame,
                text=text,
                font=('Segoe UI', 10),
                bg=self.colors['accent'],
                fg=self.colors['text_light'],
                relief=tk.FLAT,
                padx=15,
                pady=5,
                command=command
            )
            btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        
        # Initial message - check microphone and AI status
        ai_status = "AI chat enabled!" if self.gemini_ai.is_available() else "Add Gemini API key in Settings for AI chat"
        
        if self.voice_engine.microphone:
            self._add_message("April", f"Hello {USER_NAME}! I'm April, your personal AI assistant.\n"
                             f"{ai_status}\n\n"
                             "Say 'Hey April' or type anything to chat with me!")
        else:
            self._add_message("April", f"Hello {USER_NAME}! I'm April, your personal AI assistant.\n"
                             f"{ai_status}\n\n"
                             "NOTE: Microphone not available. Voice input disabled.\n"
                             "To enable voice: Windows Settings > Privacy > Microphone\n\n"
                             "You can still type anything to chat with me!")
    
    def _create_tray_icon(self):
        """Create system tray icon."""
        try:
            # Create icon image
            icon_size = 64
            image = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Draw a simple "A" icon
            draw.ellipse([4, 4, icon_size-4, icon_size-4], fill='#e94560')
            draw.text((icon_size//2 - 10, icon_size//2 - 15), "A", fill='white')
            
            # Create menu
            menu = pystray.Menu(
                pystray.MenuItem("Show April", self.show_window),
                pystray.MenuItem("Settings", self.open_settings),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Start with Windows", self.toggle_startup, checked=lambda _: self.startup_manager.is_in_startup()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", self.quit_app)
            )
            
            self.tray_icon = pystray.Icon("April", image, "April - AI Assistant", menu)
            
        except Exception as e:
            logger.error(f"Tray icon creation error: {e}")
            self.tray_icon = None
    
    def _add_message(self, sender: str, message: str):
        """Add a message to the chat display."""
        self.chat_display.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M")
        
        if sender == "April":
            prefix = f"🤖 [{timestamp}] April: "
        else:
            prefix = f"👤 [{timestamp}] You: "
        
        self.chat_display.insert(tk.END, f"\n{prefix}{message}\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def on_text_input(self, event=None):
        """Handle text input."""
        text = self.input_entry.get().strip()
        if text:
            self.input_entry.delete(0, tk.END)
            self._add_message("You", text)
            self.process_command(text)
    
    def on_voice_input(self):
        """Handle voice input button click."""
        # Check if microphone is available
        if not self.voice_engine.microphone:
            self.status_label.config(text="Microphone not available", foreground=self.colors['error'])
            self._add_message("April", "Microphone access is blocked or not available.\n"
                             "Please check: Windows Settings > Privacy > Microphone")
            return
        
        # Pause wake word detection while we're listening
        self.wake_word_detector.pause()
        
        self.status_label.config(text="Listening... (speak now)", foreground=self.colors['warning'])
        self.root.update()
        
        try:
            # Use longer timeout for voice button - 5 seconds of recording
            text = self.voice_engine.listen(timeout=8, phrase_limit=5)
            
            if text:
                self.status_label.config(text=f"Heard: {text[:40]}", foreground=self.colors['accent'])
                self.root.update()
                self._add_message("You", text)
                self.process_command(text)
                self.status_label.config(text="Ready", foreground=self.colors['success'])
            else:
                self.status_label.config(text="Didn't catch that - speak louder", foreground=self.colors['error'])
                self.root.after(3000, lambda: self.status_label.config(
                    text="Ready", foreground=self.colors['success']))
        finally:
            # Resume wake word detection
            self.wake_word_detector.resume()
    
    def toggle_continuous_listening(self):
        """Toggle continuous listening mode on/off."""
        if not self.voice_engine.microphone:
            self.status_label.config(text="Microphone not available", foreground=self.colors['error'])
            self._add_message("April", "Microphone access is blocked or not available.\n"
                             "Please check: Windows Settings > Privacy > Microphone")
            return
        
        if self.continuous_listening:
            # Stop continuous listening
            self.continuous_listening = False
            self.voice_btn.config(bg=self.colors['error'])  # Red = not listening
            self.status_label.config(text="Ready", foreground=self.colors['success'])
            self.wake_word_detector.resume()
            logger.info("Continuous listening stopped")
        else:
            # Start continuous listening
            self.continuous_listening = True
            self.voice_btn.config(bg=self.colors['success'])  # Green = listening
            self.status_label.config(text="Listening... (speak now)", foreground=self.colors['warning'])
            self.wake_word_detector.pause()
            logger.info("Continuous listening started")
            
            # Start listening thread
            self.listening_thread = threading.Thread(target=self._continuous_listen_loop, daemon=True)
            self.listening_thread.start()
    
    def _continuous_listen_loop(self):
        """Background loop for continuous listening."""
        while self.continuous_listening:
            try:
                # Update UI to show listening
                self.root.after(0, lambda: self.status_label.config(
                    text="Listening... (speak now)", foreground=self.colors['warning']))
                
                # Listen for speech
                text = self.voice_engine.listen(timeout=5, phrase_limit=8)
                
                if text and self.continuous_listening:
                    # Update UI with what was heard
                    self.root.after(0, lambda t=text: self._handle_continuous_input(t))
                    
                    # Longer pause after a command to prevent re-triggering
                    time.sleep(2.0)
                elif self.continuous_listening:
                    # No speech detected, continue listening
                    time.sleep(0.3)
                    
            except Exception as e:
                logger.error(f"Continuous listening error: {e}")
                time.sleep(1)
        
        # Clean up when stopped
        self.root.after(0, lambda: self.status_label.config(
            text="Ready", foreground=self.colors['success']))
    
    def _handle_continuous_input(self, text: str):
        """Handle input from continuous listening (runs on main thread)."""
        # Debounce: skip if same command was just executed
        current_time = time.time()
        text_normalized = text.lower().strip()
        
        if (text_normalized == self._last_command and 
            current_time - self._last_command_time < self._command_cooldown):
            logger.debug(f"Debounced duplicate command: {text}")
            return
        
        # Update last command tracking
        self._last_command = text_normalized
        self._last_command_time = current_time
        
        self.status_label.config(text=f"Heard: {text[:40]}", foreground=self.colors['accent'])
        self._add_message("You", text)
        self.process_command(text)
        
        # Check if still in continuous mode
        if self.continuous_listening:
            self.status_label.config(text="Listening... (speak now)", foreground=self.colors['warning'])
    
    def on_wake_word(self):
        """Handle wake word detection."""
        self.is_active = True
        self.show_window()
        self.status_label.config(text="● Wake word detected!", foreground=self.colors['success'])
        self.root.update()
        
        self.voice_engine.speak(f"Yes {USER_NAME}?")
        
        # Listen for command
        self.status_label.config(text="● Listening for command...", foreground=self.colors['warning'])
        self.root.update()
        
        text = self.voice_engine.listen(timeout=8, phrase_limit=8)
        if text:
            self._add_message("You", text)
            self.process_command(text)
        else:
            self._add_message("April", "I didn't catch that. Try again!")
            self.voice_engine.speak("I didn't catch that. Please try again.")
        
        self.status_label.config(text="● Ready", foreground=self.colors['success'])
        self.is_active = False
    
    def process_command(self, text: str):
        """Process a command."""
        # DEBUG: Log the input
        logger.info(f"[DEBUG] Processing command: '{text}'")
        
        parsed = self.command_parser.parse(text)
        action = parsed['action']
        params = parsed['params']
        
        # DEBUG: Log parsed result
        logger.info(f"[DEBUG] Parsed action: '{action}', params: {params}")
        
        response = ""
        success = True
        
        try:
            if action == 'open_app':
                app = params[0] if params else ""
                app = app.lower().strip()
                logger.info(f"[DEBUG] Opening app: '{app}'")
                if self.system_control.open_application(app):
                    response = f"Done boss! Opening {app}."
                else:
                    response = f"Sorry boss, I couldn't open {app}. It may not be installed."
                    success = False
            
            elif action == 'smart_search':
                # Use Google Search API if available
                query = params[0] if params else text
                query = re.sub(r'^(search|google|look\s+up|find\s+info\s+(on|about))\s+(for\s+)?', '', query, flags=re.IGNORECASE).strip()
                logger.info(f"[DEBUG] Smart search for: '{query}'")
                
                if self.google_search.is_available():
                    results = self.google_search.search(query, num_results=3)
                    if results:
                        response = f"🔍 Found {len(results)} results for '{query}':\n\n"
                        for i, r in enumerate(results, 1):
                            response += f"{i}. {r['title']}\n   {r['snippet'][:100]}...\n"
                        response += "\nOpening top result in browser..."
                        webbrowser.open(results[0]['link'])
                    else:
                        response = f"No results found via API. Opening browser search for '{query}'..."
                        self.web_browser.open(query)
                else:
                    response = f"Opening browser search for '{query}'..."
                    self.web_browser.open(query)
            
            elif action == 'open_website':
                target = params[0] if params else text.replace('open', '').strip()
                logger.info(f"[DEBUG] Opening website: '{target}'")
                if self.web_browser.open(target):
                    response = f"Done boss! Opening {target}"
                else:
                    response = f"Sorry boss, could not open {target}"
                    success = False
            
            elif action == 'shutdown':
                response = "Shutting down in 5 seconds. Say 'cancel' to stop."
                self.system_control.shutdown(5)
            
            elif action == 'restart':
                response = "Restarting in 5 seconds. Say 'cancel' to stop."
                self.system_control.restart(5)
            
            elif action == 'lock':
                self.system_control.lock()
                response = "Done boss! Locking your screen."
            
            elif action == 'volume':
                if 'mute' in text.lower():
                    self.system_control.set_volume(action='mute')
                    response = "Done boss! Volume muted."
                elif 'up' in text.lower() or 'increase' in text.lower():
                    self.system_control.set_volume(action='up')
                    response = "Done boss! Volume increased."
                elif 'down' in text.lower() or 'decrease' in text.lower():
                    self.system_control.set_volume(action='down')
                    response = "Done boss! Volume decreased."
                else:
                    response = "Done boss! Volume adjusted."
            
            elif action == 'brightness':
                # Extract brightness level from command
                numbers = re.findall(r'\d+', text)
                if numbers:
                    level = min(100, max(0, int(numbers[0])))
                    self.system_control.set_brightness(level)
                    response = f"Done boss! Brightness set to {level}%."
                elif 'up' in text.lower() or 'increase' in text.lower():
                    self.system_control.set_brightness(80)
                    response = "Done boss! Brightness increased."
                elif 'down' in text.lower() or 'decrease' in text.lower():
                    self.system_control.set_brightness(30)
                    response = "Done boss! Brightness decreased."
                else:
                    response = "Please specify a brightness level, boss."
            
            elif action == 'weather':
                city = params[1] if params and params[1] else self.db.get_preference('default_city', 'New York')
                weather = self.weather_service.get_weather(city)
                if weather:
                    response = (f"Weather in {weather['city']}: {weather['temp']}°C, "
                               f"{weather['description']}. Humidity: {weather['humidity']}%.")
                else:
                    response = "Could not fetch weather data."
                    success = False
            
            elif action == 'stock':
                symbol = params[-1] if params else 'AAPL'
                symbol = symbol.upper().strip()
                data = self.market_data.get_stock(symbol)
                if data:
                    arrow = '📈' if data['change_percent'] > 0 else '📉'
                    response = (f"{arrow} {data['name']} ({data['symbol']}): "
                               f"${data['price']:.2f} ({data['change_percent']:+.2f}%)")
                    
                    # Get trend analysis
                    trend = self.market_data.analyze_trend(symbol)
                    if trend:
                        response += f"\n💡 {trend['suggestion']}"
                else:
                    response = f"Could not fetch data for {symbol}."
                    success = False
            
            elif action == 'crypto':
                data = self.market_data.get_crypto('BTC-USD')
                if data:
                    response = f"₿ Bitcoin: ${data['price']:,.2f} ({data['change_percent']:+.2f}%)"
                else:
                    response = "Could not fetch crypto data."
            
            elif action == 'time':
                current_time = datetime.now().strftime("%I:%M %p")
                response = f"The current time is {current_time}."
            
            elif action == 'date':
                current_date = datetime.now().strftime("%A, %B %d, %Y")
                response = f"Today is {current_date}."
            
            elif action == 'screenshot':
                path = self.screen_capture.take_screenshot()
                if path:
                    response = f"Done boss! Screenshot saved to {path}"
                else:
                    response = "Sorry boss, failed to take screenshot."
                    success = False
            
            elif action == 'organize_files':
                result = self.file_manager.organize_folder()
                total = sum(result.values())
                if total > 0:
                    details = ", ".join(f"{v} to {k}" for k, v in result.items() if v > 0)
                    response = f"Done boss! Moved {total} files: {details}"
                else:
                    response = "All done boss! No files needed organizing."
            
            elif action == 'clean_junk':
                deleted = self.file_manager.clean_junk()
                if deleted > 0:
                    response = f"Done boss! Cleaned up {deleted} junk files."
                else:
                    response = "All clean boss! No junk files found."
            
            elif action == 'delete_files':
                # Dangerous action - ask for confirmation
                response = "Sorry boss, I can't delete files directly for safety reasons. Please use File Explorer to delete files manually."
                success = False
            
            elif action == 'game':
                game = params[0] if params else text.replace('play', '').replace('game', '').strip()
                if self.gaming_launcher.launch(game):
                    response = f"Launching {game}..."
                else:
                    response = f"Could not find {game}. Add it in settings."
                    success = False
            
            elif action == 'summary':
                response = self.market_data.get_market_summary()
                
                # Add weather
                weather = self.weather_service.get_weather()
                if weather:
                    response += f"\n\n🌤️ Weather: {weather['temp']}°C, {weather['description']}"
            
            elif action == 'history':
                history = self.db.get_command_history(10)
                if history:
                    response = "Recent commands:\n" + "\n".join(
                        f"• {h['command']}" for h in history
                    )
                else:
                    response = "No command history yet."
            
            elif action == 'close_app':
                app = params[0] if params else ""
                if app:
                    self.system_control.close_application(app)
                    response = f"Closed {app}."
                else:
                    response = "Which application should I close?"
            
            elif action == 'help':
                response = ("I can help you with:\n"
                           "**🖥️ Apps & System**\n"
                           "• Open/close ANY app (say 'open chrome' or 'close notepad')\n"
                           "• System status (say 'system status' or 'cpu usage')\n"
                           "• Top processes (say 'what is using memory')\n"
                           "• Lock/shutdown/restart\n\n"
                           "**🧮 Smart Calculations**\n"
                           "• Math (say 'what is 5 + 3' or 'sqrt(144)')\n"
                           "• Conversions (say '100 kg to lbs' or '30°C to fahrenheit')\n\n"
                           "**🌐 Web & Info**\n"
                           "• Web search (say 'search python tutorials')\n"
                           "• Define words (say 'define algorithm')\n"
                           "• Weather - FREE! (say 'weather in NYC')\n"
                           "• Stock prices (say 'stock AAPL')\n\n"
                           "**📁 Files & Media**\n"
                           "• Organize files (say 'organize downloads')\n"
                           "• Screenshots (say 'screenshot')\n"
                           "• Volume/brightness control\n\n"
                           "**💬 AI Chat** (powered by Ollama - runs locally!)\n"
                           "• Ask me anything!")
            
            elif action == 'greeting':
                greetings = [
                    f"Hello {USER_NAME}! How can I help you today?",
                    f"Hi {USER_NAME}! What would you like me to do?",
                    f"Hey there {USER_NAME}! Ready to assist you.",
                ]
                response = random.choice(greetings)
            
            elif action == 'name':
                response = f"I'm April, your personal AI assistant! I'm here to help you, {USER_NAME}."
            
            elif action == 'thanks':
                response = f"You're welcome, {USER_NAME}! Let me know if you need anything else."
            
            elif action == 'feedback':
                self.feedback_system.request_feedback('general')
                response = "Thank you for your feedback!"
            
            else:
                # Unknown command - try to detect intent
                text_lower = text.lower()
                
                # Check if it looks like an app open request
                if any(word in text_lower for word in ['open', 'run', 'start', 'launch']):
                    # Extract the app name
                    for prefix in ['open', 'run', 'start', 'launch']:
                        if prefix in text_lower:
                            app_name = text_lower.split(prefix)[-1].strip()
                            if app_name:
                                if self.system_control.open_application(app_name):
                                    response = f"Done boss! Opening {app_name}."
                                else:
                                    response = f"Sorry boss, I couldn't find '{app_name}'. Try saying 'open chrome' or 'open notepad'."
                                    success = False
                                break
                    else:
                        response = "What would you like me to open?"
                        success = False
                else:
                    # Try built-in local intelligence first (math, knowledge, etc.)
                    local_response = self.local_intelligence.process(text)
                    if local_response:
                        response = local_response
                        success = True
                    # Then try Ollama/Gemini AI for conversation
                    elif self.gemini_ai.is_available():
                        ai_response = self.gemini_ai.chat_response(text)
                        if ai_response:
                            response = ai_response
                            success = True
                        else:
                            response = "I'm having trouble thinking right now. Try again?"
                            success = False
                    else:
                        # No AI available - give helpful response
                        response = (f"I didn't understand '{text}'. Try commands like:\n"
                                   "• 'open [any app]' or 'close [any app]'\n"
                                   "• 'weather' or 'screenshot'\n"
                                   "• 'volume up' or 'lock'\n"
                                   "• Math: 'what is 5 + 3' or '15 * 7'\n"
                                   "For AI chat: Install Ollama + run 'ollama pull gemma3:4b'")
                        success = False
        
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            response = f"Sorry, I encountered an error: {str(e)}"
            success = False
        
        # Log command
        self.db.log_command(text, response, success)
        
        # Display and speak response
        self._add_message("April", response)
        self.voice_engine.speak_async(response)
    
    def open_settings(self, *args):
        """Open settings panel."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("April Settings")
        settings_window.geometry("500x600")
        settings_window.configure(bg=self.colors['bg'])
        
        # Settings frame
        frame = ttk.Frame(settings_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="⚙️ Settings", font=('Segoe UI', 18, 'bold'),
                 foreground=self.colors['text']).pack(pady=(0, 20))
        
        # API Keys section
        ttk.Label(frame, text="API Keys", font=('Segoe UI', 12, 'bold')).pack(anchor=tk.W)
        
        # Alpha Vantage
        # Gemini API Key (most important - for AI chat)
        ttk.Label(frame, text="Gemini API Keys (for AI chat - get free at ai.google.dev):", 
                 foreground=self.colors['success']).pack(anchor=tk.W, pady=(10, 5))
        ttk.Label(frame, text="💡 Add multiple keys separated by commas for unlimited access!", 
                 foreground=self.colors['warning']).pack(anchor=tk.W)
        gemini_entry = tk.Entry(frame, width=70, bg=self.colors['secondary_bg'],
                               fg=self.colors['text_light'], show='*')
        gemini_entry.pack(anchor=tk.W)
        gemini_entry.insert(0, self.db.get_preference('gemini_api_key', ''))
        
        # Show current key status
        key_status = self.gemini_ai.get_key_status() if hasattr(self, 'gemini_ai') else "Not initialized"
        ttk.Label(frame, text=f"Status: {key_status}", 
                 foreground=self.colors['accent']).pack(anchor=tk.W, pady=(2, 0))
        
        # Ollama (Local AI) section
        ttk.Label(frame, text="", font=('Segoe UI', 6)).pack()  # Spacer
        ttk.Label(frame, text="🏠 Local AI (Ollama - Unlimited & Free)", 
                 font=('Segoe UI', 12, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        ollama_status = "✅ Installed & Running" if self.gemini_ai.ollama_available else "❌ Not detected"
        ollama_color = self.colors['success'] if self.gemini_ai.ollama_available else self.colors['error']
        ttk.Label(frame, text=f"Ollama Status: {ollama_status}", 
                 foreground=ollama_color).pack(anchor=tk.W)
        
        if self.gemini_ai.ollama_available:
            ttk.Label(frame, text=f"Model: {self.gemini_ai.ollama_model}", 
                     foreground=self.colors['accent']).pack(anchor=tk.W)
        
        # Use Ollama checkbox
        ollama_var = tk.BooleanVar(value=self.gemini_ai.use_ollama)
        ollama_check = ttk.Checkbutton(
            frame, 
            text="Use Ollama as primary AI (unlimited, runs locally)",
            variable=ollama_var
        )
        ollama_check.pack(anchor=tk.W, pady=(5, 0))
        
        if not self.gemini_ai.ollama_available:
            ttk.Label(frame, text="💡 To install: 1) Download from ollama.com  2) Run: ollama pull gemma4:e4b", 
                     foreground=self.colors['warning']).pack(anchor=tk.W)
        
        # Alpha Vantage
        ttk.Label(frame, text="Alpha Vantage API Key (optional):").pack(anchor=tk.W, pady=(10, 5))
        alpha_entry = tk.Entry(frame, width=50, bg=self.colors['secondary_bg'],
                               fg=self.colors['text_light'])
        alpha_entry.pack(anchor=tk.W)
        alpha_entry.insert(0, self.db.get_preference('alpha_vantage_key', ''))
        
        # OpenWeather
        ttk.Label(frame, text="OpenWeather API Key (optional):").pack(anchor=tk.W, pady=(10, 5))
        weather_entry = tk.Entry(frame, width=50, bg=self.colors['secondary_bg'],
                                 fg=self.colors['text_light'])
        weather_entry.pack(anchor=tk.W)
        weather_entry.insert(0, self.db.get_preference('openweather_key', ''))
        
        # Google API Key
        ttk.Label(frame, text="Google API Key (for enhanced search):").pack(anchor=tk.W, pady=(10, 5))
        google_entry = tk.Entry(frame, width=50, bg=self.colors['secondary_bg'],
                                fg=self.colors['text_light'])
        google_entry.pack(anchor=tk.W)
        google_entry.insert(0, self.db.get_preference('google_api_key', ''))
        
        # Default city
        ttk.Label(frame, text="Default City:").pack(anchor=tk.W, pady=(10, 5))
        city_entry = tk.Entry(frame, width=50, bg=self.colors['secondary_bg'],
                              fg=self.colors['text_light'])
        city_entry.pack(anchor=tk.W)
        city_entry.insert(0, self.db.get_preference('default_city', 'New York'))
        
        # Startup option
        startup_var = tk.BooleanVar(value=self.startup_manager.is_in_startup())
        startup_check = ttk.Checkbutton(frame, text="Start with Windows",
                                        variable=startup_var)
        startup_check.pack(anchor=tk.W, pady=(20, 5))
        
        # Wake word option
        wake_var = tk.BooleanVar(value=self.db.get_preference('wake_word_enabled', 'true') == 'true')
        wake_check = ttk.Checkbutton(frame, text="Enable wake word detection",
                                     variable=wake_var)
        wake_check.pack(anchor=tk.W, pady=5)
        
        # ═══════════════════════════════════════════════════════════════════════
        # Microphone Settings Section
        # ═══════════════════════════════════════════════════════════════════════
        ttk.Label(frame, text="🎤 Microphone Settings", font=('Segoe UI', 12, 'bold')).pack(anchor=tk.W, pady=(20, 10))
        
        mic_frame = ttk.Frame(frame)
        mic_frame.pack(fill=tk.X, pady=5)
        
        # Sensitivity dropdown
        ttk.Label(mic_frame, text="Sensitivity:").pack(side=tk.LEFT, padx=(0, 10))
        sensitivity_var = tk.StringVar(value=self.db.get_preference('mic_sensitivity', 'medium'))
        sensitivity_combo = ttk.Combobox(mic_frame, textvariable=sensitivity_var, 
                                         values=['low', 'medium', 'high', 'very_high'],
                                         state='readonly', width=15)
        sensitivity_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        def apply_sensitivity():
            level = sensitivity_var.get()
            result = self.voice_engine.set_sensitivity(level)
            if result['success']:
                self.db.save_preference('mic_sensitivity', level)
                messagebox.showinfo("Microphone", f"Sensitivity set to {level}")
            else:
                messagebox.showerror("Microphone", result['message'])
        
        tk.Button(mic_frame, text="Apply", command=apply_sensitivity,
                 bg=self.colors['accent'], fg=self.colors['text_light']).pack(side=tk.LEFT)
        
        # Calibrate button
        mic_frame2 = ttk.Frame(frame)
        mic_frame2.pack(fill=tk.X, pady=5)
        
        mic_status_label = ttk.Label(mic_frame2, text=f"Current threshold: {int(self.voice_engine.recognizer.energy_threshold)}")
        mic_status_label.pack(side=tk.LEFT, padx=(0, 10))
        
        def calibrate_mic():
            mic_status_label.config(text="Calibrating... stay quiet for 2 seconds")
            settings_window.update()
            result = self.voice_engine.recalibrate()
            if result['success']:
                mic_status_label.config(text=f"Calibrated! Threshold: {result['energy_threshold']}")
            else:
                mic_status_label.config(text=f"Failed: {result['message']}")
        
        tk.Button(mic_frame2, text="🔄 Calibrate Now", command=calibrate_mic,
                 bg=self.colors['success'], fg=self.colors['text_light']).pack(side=tk.LEFT)
        
        # Tips
        ttk.Label(frame, text="💡 Tips: If words are misheard, try 'high' sensitivity and calibrate.",
                 foreground=self.colors['warning']).pack(anchor=tk.W, pady=(5, 0))
        ttk.Label(frame, text="     Speak clearly and close to the microphone.",
                 foreground=self.colors['warning']).pack(anchor=tk.W)
        
        # Save button
        def save_settings():
            # Save Gemini key and reload AI
            new_gemini_key = gemini_entry.get()
            self.db.save_preference('gemini_api_key', new_gemini_key, encrypt=True)
            
            # Save Ollama preference
            self.db.save_preference('use_ollama', str(ollama_var.get()).lower())
            self.gemini_ai.use_ollama = ollama_var.get()
            
            self.gemini_ai.reload_api_key()  # Reinitialize with new key
            
            self.db.save_preference('alpha_vantage_key', alpha_entry.get(), encrypt=True)
            self.db.save_preference('openweather_key', weather_entry.get(), encrypt=True)
            self.db.save_preference('google_api_key', google_entry.get(), encrypt=True)
            self.google_search.reload_api_key()  # Reload Google Search API key
            self.db.save_preference('default_city', city_entry.get())
            self.db.save_preference('wake_word_enabled', str(wake_var.get()).lower())
            
            # Save and apply mic sensitivity
            self.db.save_preference('mic_sensitivity', sensitivity_var.get())
            self.voice_engine.set_sensitivity(sensitivity_var.get())
            
            if startup_var.get():
                self.startup_manager.add_to_startup()
            else:
                self.startup_manager.remove_from_startup()
            
            messagebox.showinfo("Settings", "Settings saved successfully!")
            settings_window.destroy()
        
        tk.Button(frame, text="Save Settings", command=save_settings,
                 bg=self.colors['text'], fg=self.colors['text_light'],
                 font=('Segoe UI', 12), padx=20, pady=10).pack(pady=20)
        
        # Voice profile section
        ttk.Label(frame, text="Voice Profile", font=('Segoe UI', 12, 'bold')).pack(anchor=tk.W, pady=(20, 10))
        
        profile_status = "✅ Voice profile exists" if self.voice_profile.profile_exists else "❌ No voice profile"
        ttk.Label(frame, text=profile_status).pack(anchor=tk.W)
        
        def create_voice_profile():
            messagebox.showinfo("Voice Profile", 
                              "Please say these phrases when prompted:\n1. Hello April\n2. What's the weather\n3. Open YouTube")
            samples = []
            for phrase in ["Hello April", "What's the weather", "Open YouTube"]:
                self.voice_engine.speak(f"Please say: {phrase}")
                sample = self.voice_engine.listen(timeout=5)
                if sample:
                    samples.append(sample)
            
            if len(samples) >= 2:
                self.voice_profile.create_profile(samples)
                messagebox.showinfo("Voice Profile", "Voice profile created successfully!")
            else:
                messagebox.showerror("Voice Profile", "Could not capture enough voice samples.")
        
        tk.Button(frame, text="Create Voice Profile", command=create_voice_profile,
                 bg=self.colors['accent'], fg=self.colors['text_light']).pack(anchor=tk.W, pady=10)
        
        # Microphone Test section
        ttk.Label(frame, text="Microphone Test", font=('Segoe UI', 12, 'bold')).pack(anchor=tk.W, pady=(20, 10))
        
        mic_status_label = ttk.Label(frame, text="Click 'Test Microphone' to check audio input")
        mic_status_label.pack(anchor=tk.W)
        
        def calibrate_mic():
            mic_status_label.config(text="Calibrating... stay quiet for 2 seconds")
            settings_window.update()
            result = self.voice_engine.calibrate_microphone()
            if result['success']:
                mic_status_label.config(text=f"Calibrated! Threshold: {result['threshold']}")
                messagebox.showinfo("Calibration", result['message'])
            else:
                mic_status_label.config(text=f"Calibration failed: {result['message']}")
        
        def test_mic():
            mic_status_label.config(text="Listening for 5 seconds... speak now!")
            settings_window.update()
            text = self.voice_engine.listen(timeout=10, phrase_limit=10)
            if text:
                mic_status_label.config(text=f"Heard: '{text}'")
                messagebox.showinfo("Test Result", f"Successfully recognized:\n\n'{text}'")
            else:
                mic_status_label.config(text="Could not recognize speech. Try calibrating first.")
                messagebox.showwarning("Test Result", "Could not recognize speech.\n\nTry:\n1. Click 'Calibrate Microphone' first\n2. Speak louder and clearer\n3. Reduce background noise")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(anchor=tk.W, pady=10)
        
        tk.Button(btn_frame, text="Calibrate Microphone", command=calibrate_mic,
                 bg=self.colors['warning'], fg=self.colors['bg']).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(btn_frame, text="Test Microphone", command=test_mic,
                 bg=self.colors['accent'], fg=self.colors['text_light']).pack(side=tk.LEFT)
    
    def show_window(self, *args):
        """Show the main window."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.is_minimized = False
    
    def minimize_to_tray(self):
        """Minimize to system tray."""
        self.root.withdraw()
        self.is_minimized = True
    
    def toggle_startup(self):
        """Toggle Windows startup."""
        if self.startup_manager.is_in_startup():
            self.startup_manager.remove_from_startup()
        else:
            self.startup_manager.add_to_startup()
    
    def quit_app(self):
        """Quit the application."""
        self.wake_word_detector.stop()
        self.task_scheduler.stop()
        self.whatsapp_handler.stop_monitoring()
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        self.db.close()
        self.root.quit()
        self.root.destroy()
        sys.exit(0)
    
    def run(self):
        """Run the application."""
        # Load saved microphone sensitivity
        saved_sensitivity = self.db.get_preference('mic_sensitivity', 'medium')
        self.voice_engine.set_sensitivity(saved_sensitivity)
        logger.info(f"Loaded mic sensitivity: {saved_sensitivity}")
        
        # Update status based on microphone availability
        if self.voice_engine.microphone:
            self.status_label.config(text="Ready - Voice enabled", foreground=self.colors['success'])
        else:
            self.status_label.config(text="Voice disabled - type commands", foreground=self.colors['warning'])
        
        # Start background services only if microphone available
        if self.voice_engine.microphone and self.db.get_preference('wake_word_enabled', 'true') == 'true':
            self.wake_word_detector.start()
        else:
            logger.info("Wake word detection disabled (no microphone)")
        
        self.task_scheduler.start()
        
        # Start tray icon in thread
        if self.tray_icon:
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()
        
        # Minimize if started with flag
        if self.start_minimized:
            self.minimize_to_tray()
        
        # Welcome message (only speak if microphone works, otherwise just log)
        if self.voice_engine.microphone:
            self.voice_engine.speak_async(f"Hello {USER_NAME}, April is ready to help you.")
        
        # Run main loop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit_app()

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point."""
    # Check if started with --minimized flag
    start_minimized = '--minimized' in sys.argv
    
    # Create and run the application
    app = AprilApp(start_minimized=start_minimized)
    app.run()

if __name__ == "__main__":
    main()
