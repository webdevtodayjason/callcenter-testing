# Call Center Testing Script

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Twilio](https://img.shields.io/badge/Twilio-API-red.svg)](https://www.twilio.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![SocketIO](https://img.shields.io/badge/SocketIO-Enabled-brightgreen.svg)](https://socket.io/)

A Flask-based application for testing call center scripts and voice response systems. This tool allows you to initiate multiple test calls to a target number, play MP3 files, and monitor call status in real-time.

![Call Center Testing Script](https://via.placeholder.com/800x400?text=Call+Center+Testing+Script)

## Features

- **Multiple Call Testing**: Initiate multiple calls to a target phone number
- **Real-time Call Monitoring**: Track call status updates in real-time using WebSockets
- **Custom Greeting Text**: Option to use text-to-speech for custom greetings
- **MP3 Playback**: Play random MP3 files during calls
- **Diagnostic Tools**: Test pages for MP3 accessibility, static file serving, and Twilio account status
- **Responsive UI**: Clean, Bootstrap-based interface

## Table of Contents

- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setting Up Conda Environment](#setting-up-conda-environment)
  - [Installing Dependencies](#installing-dependencies)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Setting Up Ngrok](#setting-up-ngrok)
- [Usage](#usage)
  - [Starting the Application](#starting-the-application)
  - [Making Test Calls](#making-test-calls)
  - [Using Custom Greetings](#using-custom-greetings)
  - [Diagnostic Tools](#diagnostic-tools)
- [API Reference](#api-reference)
- [Credits](#credits)
- [License](#license)

## Installation

### Prerequisites

- Python 3.11 or higher
- Conda package manager
- Twilio account with API credentials
- Ngrok account (for exposing local server to the internet)
- MP3 files for playback testing

### Setting Up Conda Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/webdevtodayjason/callcenter-testing.git
   cd callcenter-testing
   ```

2. Create a new Conda environment:
   ```bash
   conda create -n callcenter-testing python=3.11
   ```

3. Activate the environment:
   ```bash
   conda activate callcenter-testing
   ```

### Installing Dependencies

Install the required packages:

```bash
pip install flask flask-socketio twilio python-dotenv
```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
BASE_URL=your_public_url_from_ngrok
```

### Setting Up Ngrok

1. **Install Ngrok**:
   - Download Ngrok from [https://ngrok.com/download](https://ngrok.com/download)
   - Extract the downloaded file
   - Move the ngrok executable to an accessible location

2. **Create an Ngrok Account**:
   - Sign up at [https://dashboard.ngrok.com/signup](https://dashboard.ngrok.com/signup)
   - Get your auth token from the dashboard

3. **Configure Ngrok**:
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

4. **Start Ngrok**:
   ```bash
   ngrok http 5005
   ```

5. **Update Your .env File**:
   - Copy the HTTPS URL provided by Ngrok (e.g., `https://a1b2c3d4.ngrok.io`)
   - Update the `BASE_URL` in your `.env` file with this URL

## Usage

### Starting the Application

1. Make sure your Conda environment is activated:
   ```bash
   conda activate callcenter-testing
   ```

2. Start the Flask application:
   ```bash
   python app.py
   ```

3. The application will run on `http://localhost:5005`

### Making Test Calls

1. Open your browser and navigate to the application URL
2. Enter the target phone number in the format `+1234567890`
3. Specify the number of calls to make (1-50)
4. Click "Initiate Calls"
5. Monitor call status in the "Call Activity" table

### Using Custom Greetings

1. Check the "Use Custom Intro Text-to-Speech" box
2. Enter your custom greeting text in the text area that appears
3. When calls are made, Twilio will speak this text before playing the MP3 file

### Diagnostic Tools

The application provides several diagnostic pages accessible from the main interface:

- **Test MP3 Files**: Check if MP3 files are accessible and playable
- **Test Static Files**: Verify that static files are being served correctly
- **Test Twilio Account**: Check your Twilio account status and make a test call

## API Reference

### Endpoints

- `GET /`: Main admin interface
- `POST /initiate_calls`: Initiate calls to a target number
- `POST/GET /twiml`: TwiML instructions for Twilio
- `POST /status`: Status callback for Twilio
- `GET /test-mp3`: Test MP3 accessibility
- `GET /test-static`: Test static file serving
- `GET /test-twilio`: Test Twilio account status
- `POST /test-call`: Make a test call
- `POST/GET /simple-twiml`: Simple TwiML response for testing

## Directory Structure

```
callcenter-testing/
├── app.py                 # Main application file
├── .env                   # Environment variables (create this)
├── README.md              # This file
├── static/                # Static files directory
│   └── mp3/               # MP3 files for playback
│       ├── file1.mp3
│       ├── file2.mp3
│       └── ...
└── requirements.txt       # Python dependencies
```

## Credits

This project uses the following open-source packages and APIs:

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/) - WebSocket support
- [Twilio](https://www.twilio.com/) - Telephony API
- [Bootstrap](https://getbootstrap.com/) - UI framework
- [jQuery](https://jquery.com/) - JavaScript library
- [Socket.IO](https://socket.io/) - Real-time communication
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Environment variable management

## Author

**Jason Brashear** - [WebDevTodayJason](https://github.com/webdevtodayjason/)

## License

This project is licensed under the MIT License - see below for details:

```
MIT License

Copyright (c) 2023 Jason Brashear

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