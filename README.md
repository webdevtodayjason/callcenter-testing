# Call Center Testing Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-red.svg)](https://flask.palletsprojects.com/)
[![Twilio](https://img.shields.io/badge/Twilio-8.5.0-blueviolet.svg)](https://www.twilio.com/)
[![ElevenLabs](https://img.shields.io/badge/ElevenLabs-API-orange.svg)](https://elevenlabs.io/)
[![Maintained by Jason Brashear](https://img.shields.io/badge/Maintained%20by-Jason%20Brashear-brightgreen.svg)](https://github.com/webdevtodayjason)

<div align="center">
  <img src="https://raw.githubusercontent.com/webdevtodayjason/callcenter-testing/main/static/phone.png" alt="Call Center Testing Tool Logo" width="200"/>
  <p><i>A powerful tool for testing call center systems with realistic voice simulations</i></p>
</div>

A Flask-based web application for testing call center systems using Twilio's voice API. This tool allows you to make test calls to phone numbers with customizable audio playback options.

## ✨ Features

### 📞 Multiple Call Management
- **Simultaneous Calls**: Make calls to multiple phone numbers with configurable delay between calls
- **Load Control**: Set the maximum number of simultaneous calls to control system load
- **Real-time Tracking**: Monitor each call's status in real-time

### 🔊 Customizable Audio Playback
- **Text-to-Speech Only**: Use Twilio's TTS or Eleven Labs for voice synthesis
- **Text-to-Speech + MP3**: Play a custom greeting followed by an MP3 file
- **MP3 Only**: Play only an MP3 file during the call

### 🗣️ Enhanced Text-to-Speech with Eleven Labs
- **Natural-Sounding Voices**: High-quality, realistic voice synthesis
- **Multiple Voice Options**: Choose from various voice profiles with adjustable settings
- **Direct API Integration**: Seamless integration with Eleven Labs API
- **Performance Optimization**: Audio caching to improve responsiveness

### 📂 MP3 File Management
- **Easy Upload**: Upload MP3 files through the intuitive web interface
- **File Operations**: Delete or rename existing MP3 files
- **Preview Capability**: Listen to MP3 files before using them in calls

### 📊 Real-time Call Status Updates
- **Live Monitoring**: Track call progress with Socket.IO
- **Detailed Logging**: View comprehensive logs for troubleshooting
- **Call Control**: Abort ongoing calls when needed

### 🧪 Test Pages
- Dedicated pages for testing MP3 playback, static file serving, and Twilio integration

## 🚀 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/webdevtodayjason/callcenter-testing.git
   cd callcenter-testing
   ```

2. Create and activate a Conda environment:
   ```bash
   conda create -n callcenter python=3.11
   conda activate callcenter
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on the provided `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Edit the `.env` file with your Twilio credentials and other configuration options.

## 📋 Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to `http://localhost:5005`

3. Configure your call settings:
   - Enter phone numbers (one per line) in E.164 format (e.g., +15551234567)
   - Set the delay between calls (minimum 1 second)
   - Set the maximum number of simultaneous calls (1-50)
   - Choose playback mode (Text-to-Speech Only, Text-to-Speech + MP3, or MP3 Only)
   - Select MP3 options (random or specific file)
   - Configure Text-to-Speech settings

4. Click "Start Calls" to initiate the calls

5. Monitor call status in real-time on the page

## 🎵 MP3 Management

The application provides a dedicated page for managing MP3 files:

1. Navigate to the "Manage MP3 Files" page from the main interface
2. Upload new MP3 files (up to 16MB)
3. Preview existing MP3 files
4. Rename or delete MP3 files as needed

## 🔊 Eleven Labs Integration

The application features full integration with Eleven Labs for enhanced text-to-speech:

1. Sign up for an Eleven Labs account at [https://elevenlabs.io](https://elevenlabs.io)
2. Get your API key from the Eleven Labs dashboard
3. Add your API key to the `.env` file
4. Configure your voice IDs in the `ELEVENLABS_VOICES` environment variable
5. Select "Eleven Labs" as your TTS provider in the web interface
6. Choose from available voices and customize settings as needed

**Benefits of using Eleven Labs:**
- Higher quality, more natural-sounding voices compared to Twilio's built-in TTS
- Multiple voice options to choose from
- Ability to save generated audio for reuse

## 💻 Development

### Local Testing with ngrok

For testing callbacks locally:

1. Install ngrok: [https://ngrok.com/download](https://ngrok.com/download)
2. Start ngrok on port 5005:
   ```bash
   ngrok http 5005
   ```
3. Update the `BASE_URL` in your `.env` file with the ngrok URL

### Test Pages

The application includes several test pages to verify functionality:

- `/test-mp3`: Test MP3 file playback
- `/test-static`: Test static file serving
- `/test-twilio`: Test Twilio account integration
- `/test-call`: Test TwiML response

## 📝 License

This project is licensed under the MIT License.

```
MIT License

Copyright (c) 2025 Jason Brashear

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 👨‍💻 Author

**Jason Brashear**

[![GitHub](https://img.shields.io/badge/GitHub-webdevtodayjason-181717?style=for-the-badge&logo=github)](https://github.com/webdevtodayjason)

## 🙏 Acknowledgments

- [Twilio](https://www.twilio.com/) for their excellent voice API
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Socket.IO](https://socket.io/) for real-time communication
- [Eleven Labs](https://elevenlabs.io/) for advanced text-to-speech capabilities 