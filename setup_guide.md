# 📖 Setup Guide

Complete setup instructions for your Personal AI Assistant.

## 🎯 Quick Overview

This guide takes you through:
1. Installing prerequisites (Python, Ollama)
2. Downloading the AI model (~2GB)
3. Installing Python dependencies
4. Running your assistant

**Total time: ~15 minutes**

## 📋 System Requirements

### Minimum
- **OS**: Windows 10+, macOS 10.14+, or Linux
- **RAM**: 4GB available (8GB total recommended)
- **Storage**: 5GB free space
- **Internet**: Required for setup only

### Recommended
- **RAM**: 8GB+ available
- **CPU**: Quad-core processor
- **Storage**: SSD with 10GB+ free space

## 🛠️ Step-by-Step Setup

### Step 1: Install Python

**Windows:**
1. Go to [python.org/downloads](https://python.org/downloads)
2. Download Python 3.8+
3. ⚠️ **Important**: Check "Add Python to PATH" during installation
4. Test: Open cmd and run `python --version`

**macOS:**
```bash
# Using Homebrew (recommended)
brew install python

# Or download from python.org
```

**Linux:**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

### Step 2: Install Ollama

**Windows:**
1. Go to [ollama.com](https://ollama.com)
2. Click "Download for Windows"
3. Run installer
4. Ollama starts automatically

**macOS:**
```bash
brew install ollama
# Or download from ollama.com
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Verify installation:**
```bash
ollama --version
```

### Step 3: Download AI Model

This downloads the AI "brain" (~2GB download):

```bash
ollama pull phi3.5:3.8b
```

⏳ **Wait for completion** (5-15 minutes depending on internet speed)

**Verify model:**
```bash
ollama list
```
You should see `phi3.5:3.8b` in the list.

### Step 4: Get the Code

**Option A: Download ZIP**
1. Go to this repository on GitHub
2. Click green "Code" button
3. Click "Download ZIP"
4. Extract to a folder

**Option B: Clone with Git**
```bash
git clone https://github.com/Adhawaide/personal-ai-assistant.git
cd personal-ai-assistant
```

### Step 5: Install Python Dependencies

Navigate to your project folder:

```bash
cd personal-ai-assistant
pip install -r requirements.txt
```

**If you get errors:**
```bash
# Try user installation
pip install --user -r requirements.txt

# On Windows, if PyAudio fails:
pip install pipwin
pipwin install pyaudio
```

### Step 6: Run Your Assistant

**Start Ollama (if not running):**
```bash
ollama serve
```

**Launch the assistant:**
```bash
streamlit run fast_assistant.py
```

**Open browser to:**
```
http://localhost:8501
```

## 🎉 First Test

1. Type "Hello, how are you?" and press Enter
2. First response takes 20-30 seconds (model loading)
3. Subsequent responses: 10-20 seconds
4. Try voice features if you have microphone

## 📱 Mobile Access

**Access from phone/tablet on same WiFi:**

```bash
# Run with network access
streamlit run fast_assistant.py --server.address 0.0.0.0

# Find your computer's IP:
# Windows: ipconfig
# Mac/Linux: ifconfig

# Access from mobile: http://[your-ip]:8501
```

## 🔧 Troubleshooting

### Slow Responses (>60 seconds)
```bash
# Check system performance
python check_performance.py

# Close other applications to free RAM
# Need 3GB+ available for best performance
```

### Connection Issues
```bash
# Check if Ollama is running
ollama serve

# Test connection
curl http://localhost:11434/api/tags
```

### Voice Not Working
```bash
# Test voice system
python voice_debug_test.py

# Try alternative version
streamlit run voice_fixed_assistant.py
```

### Module Not Found
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

## ⚡ Performance Tips

- Keep 3GB+ RAM available
- Close unnecessary browser tabs
- Use SSD storage if available
- Check performance: `python check_performance.py`

## 🆘 Getting Help

- **Check error messages** in the terminal where you ran streamlit
- **Run diagnostics**: `python check_performance.py`
- **Report issues**: Create issue on GitHub repository
- **Include**: Your OS, error messages, system specs

## 🎯 What's Next?

Once running:
1. Explore different conversation topics
2. Try voice features (if available)
3. Test mobile access
4. Customize settings in the interface

Your personal AI assistant is ready! 🤖✨
