# First-Time Setup Instructions

Follow these steps to set up the repository for the first time:

## 1. Verify the Repository

Visit https://github.com/webdevtodayjason/callcenter-testing to verify that your code has been pushed successfully.

## 2. Set Up Environment

1. Create a `.env` file based on the `.env.example` template:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your actual Twilio credentials and other configuration:
   - `TWILIO_ACCOUNT_SID`: Your Twilio account SID
   - `TWILIO_AUTH_TOKEN`: Your Twilio auth token
   - `TWILIO_PHONE_NUMBER`: Your Twilio phone number in E.164 format
   - `BASE_URL`: Your ngrok URL (for local development) or production URL
   - `ELEVENLABS_API_KEY`: Your Eleven Labs API key (for enhanced TTS)
   - `ELEVENLABS_VOICES`: JSON object mapping voice names to Eleven Labs voice IDs

## 3. Create Conda Environment

```bash
conda create -n callcenter python=3.11
conda activate callcenter
pip install -r requirements.txt
```

## 4. Set Up ngrok for Local Development

If you're developing locally and need to receive Twilio callbacks:

1. Download and install ngrok from https://ngrok.com/download
2. Run ngrok to create a tunnel to port 5005:
   ```bash
   ngrok http 5005
   ```
3. Copy the HTTPS URL provided by ngrok (e.g., https://a1b2c3d4.ngrok.io)
4. Update the `BASE_URL` in your `.env` file with this URL

## 5. Run the Application

```bash
python app.py
```

The application will be available at http://localhost:5005. 

## 6. Testing the Application

1. Open your browser and navigate to http://localhost:5005
2. Enter at least one phone number in E.164 format (e.g., +12345678900)
3. Configure your call settings
4. Click "Start Calls" to initiate test calls

## 7. Troubleshooting

If you encounter issues:

- Check the console logs for error messages
- Verify your Twilio credentials are correct
- Ensure ngrok is running if testing locally
- Confirm your Eleven Labs API key is valid (if using Eleven Labs TTS) 