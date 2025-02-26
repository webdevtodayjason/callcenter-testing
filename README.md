# Call Center Testing Tool

A Flask-based web application for testing call center systems using Twilio's voice API. This tool allows you to make test calls to phone numbers with customizable audio playback options.

## Features

- **Multiple Call Management**: Make calls to multiple phone numbers with configurable delay between calls
- **Customizable Audio Playback**:
  - Text-to-Speech Only: Use Twilio's TTS or Eleven Labs for voice synthesis
  - Text-to-Speech + MP3: Play a custom greeting followed by an MP3 file
  - MP3 Only: Play only an MP3 file during the call
- **MP3 File Management**:
  - Upload MP3 files through the web interface
  - Delete or rename existing MP3 files
  - Preview MP3 files before using them in calls
- **Text-to-Speech Options**:
  - Choose between Twilio Voice or Eleven Labs for TTS
  - Select from multiple Eleven Labs voices (when configured)
  - Option to save TTS output as MP3 files
- **Real-time Call Status Updates**: Monitor call progress with Socket.IO
- **Test Pages**: Dedicated pages for testing MP3 playback, static file serving, and Twilio integration

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/webdevtodayjason/callcenter-testing.git
   cd callcenter-testing
   ```

2. Create and activate a Conda environment:
   ```
   conda create -n callcenter python=3.11
   conda activate callcenter
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on the provided `.env.example`:
   ```
   cp .env.example .env
   ```

5. Edit the `.env` file with your Twilio credentials and other configuration options.

## Usage

1. Start the application:
   ```
   python app.py
   ```

2. Open your browser and navigate to `http://localhost:5000`

3. Configure your call settings:
   - Enter phone numbers (one per line) in E.164 format (e.g., +15551234567)
   - Set the delay between calls
   - Choose playback mode (Text-to-Speech Only, Text-to-Speech + MP3, or MP3 Only)
   - Select MP3 options (random or specific file)
   - Configure Text-to-Speech settings

4. Click "Start Calls" to initiate the calls

5. Monitor call status in real-time on the page

## MP3 Management

The application provides a dedicated page for managing MP3 files:

1. Navigate to the "Manage MP3 Files" page from the main interface
2. Upload new MP3 files (up to 16MB)
3. Preview existing MP3 files
4. Rename or delete MP3 files as needed

## Eleven Labs Integration (Optional)

To use Eleven Labs for enhanced Text-to-Speech:

1. Sign up for an Eleven Labs account at [https://elevenlabs.io](https://elevenlabs.io)
2. Get your API key from the Eleven Labs dashboard
3. Add your API key to the `.env` file
4. Configure your voice IDs in the `ELEVENLABS_VOICES` environment variable

## Development

### Local Testing with ngrok

For testing callbacks locally:

1. Install ngrok: [https://ngrok.com/download](https://ngrok.com/download)
2. Start ngrok on port 5000:
   ```
   ngrok http 5000
   ```
3. Update the `BASE_URL` in your `.env` file with the ngrok URL

### Test Pages

The application includes several test pages to verify functionality:

- `/test-mp3`: Test MP3 file playback
- `/test-static`: Test static file serving
- `/test-twilio`: Test Twilio account integration
- `/test-call`: Test TwiML response

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Jason Brashear

## Acknowledgments

- [Twilio](https://www.twilio.com/) for their excellent voice API
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Socket.IO](https://socket.io/) for real-time communication
- [Eleven Labs](https://elevenlabs.io/) for advanced text-to-speech capabilities 