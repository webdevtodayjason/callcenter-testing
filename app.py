from flask import Flask, request, Response, render_template_string, jsonify, redirect, url_for
from flask_socketio import SocketIO
from twilio.rest import Client
import os
import random
import logging
from threading import Thread
from dotenv import load_dotenv
import urllib.parse
import json
import re
from werkzeug.utils import secure_filename
import time
from twilio.twiml.voice_response import VoiceResponse
import requests
import tempfile
import uuid
from urllib.parse import quote

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app and SocketIO
app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['UPLOAD_FOLDER'] = 'static/mp3'
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key')
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'mp3', 'wav'}

# Function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to get all MP3 files in the static/mp3 directory
def get_mp3_files():
    mp3_dir = os.path.join(app.root_path, 'static', 'mp3')
    if not os.path.exists(mp3_dir):
        os.makedirs(mp3_dir)
    
    files = [f for f in os.listdir(mp3_dir) if os.path.isfile(os.path.join(mp3_dir, f)) and allowed_file(f)]
    return sorted(files)

# Update the mp3_files list
mp3_files = get_mp3_files()

# Twilio configuration
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_number = os.environ['TWILIO_PHONE_NUMBER']
base_url = os.environ['BASE_URL']

# ElevenLabs configuration (optional)
elevenlabs_api_key = os.environ.get('ELEVENLABS_API_KEY', '')
elevenlabs_voices = json.loads(os.environ.get('ELEVENLABS_VOICES', '{}'))

client = Client(account_sid, auth_token)

# In-memory storage for call statuses
calls = {}

# Define a function to handle the actual HTML generation
def generate_admin_html():
    """Generate the admin HTML with embedded JavaScript and no template errors."""
    mp3_files = get_mp3_files()
    
    # Create the MP3 options HTML
    mp3_options = ""
    if mp3_files:
        for file in mp3_files:
            mp3_options += f'<option value="{file}">{file}</option>\n'
    else:
        mp3_options = '<option value="">No MP3 files available</option>'
    
    # Create the Eleven Labs voices options HTML
    voice_options = ""
    if elevenlabs_voices:
        for name, id in elevenlabs_voices.items():
            voice_options += f'<option value="{name}">{name}</option>\n'
    else:
        voice_options = '<option value="">No voices available</option>'
    
    # Build the full HTML - escape all CSS curly braces with double braces
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Call Center Testing</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <style>
        body {{ padding: 20px; }}
        #status {{ margin-top: 20px; }}
        .call-status {{ margin-bottom: 10px; padding: 10px; border-radius: 5px; }}
        .pending {{ background-color: #f8f9fa; }}
        .in-progress {{ background-color: #fff3cd; }}
        .completed {{ background-color: #d4edda; }}
        .failed {{ background-color: #f8d7da; }}
        footer {{ margin-top: 50px; padding: 20px 0; border-top: 1px solid #dee2e6; text-align: center; }}
        footer a {{ color: #007bff; }}
        footer a:hover {{ color: #0056b3; text-decoration: none; }}
        .test-links {{ margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }}
        .test-links a {{ margin-right: 15px; }}
        #specific_mp3_container, #eleven_labs_voices_container, #custom_greeting_container {{ display: block; }}
        .visible {{ display: block !important; }}
        .card {{ margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">Call Center Testing</h1>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">Call Settings</div>
                    <div class="card-body">
                        <form id="callForm">
                            <div class="form-group">
                                <label for="phone_numbers">Phone Numbers (one per line)</label>
                                <textarea class="form-control" id="phone_numbers" rows="5" required></textarea>
                                <small class="form-text text-muted">Enter one phone number per line in E.164 format (e.g., +15551234567)</small>
                            </div>
                            
                            <div class="form-group">
                                <label for="delay">Delay Between Calls (seconds)</label>
                                <input type="number" class="form-control" id="delay" value="5" min="1" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="simultaneous_calls">Simultaneous Calls (1-50, single number only)</label>
                                <input type="number" class="form-control" id="simultaneous_calls" value="1" min="1" max="50">
                                <small class="form-text text-muted">Only works when calling a single phone number. For multiple numbers, set to 1.</small>
                            </div>
                            
                            <div class="form-check mb-3">
                                <input type="checkbox" class="form-check-input" id="use_custom_greeting">
                                <label class="form-check-label" for="use_custom_greeting">Custom Intro Text-to-Speech</label>
                            </div>
                            
                            <div id="custom_greeting_container" class="form-group">
                                <label for="custom_greeting">Custom Greeting Text</label>
                                <textarea class="form-control" id="custom_greeting" rows="3" placeholder="Enter your custom greeting text here..."></textarea>
                            </div>
                            
                            <button type="submit" class="btn btn-primary" id="startButton">Start Calls</button>
                            <button type="button" class="btn btn-danger" id="stopButton" disabled>Stop Calls</button>
                        </form>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">Audio Settings</div>
                    <div class="card-body">
                        <div class="form-group">
                            <label id="playback_mode_label" for="tts_only">Playback Mode</label>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="playback_mode" id="tts_only" value="tts_only" checked>
                                <label class="form-check-label" for="tts_only">
                                    Text-to-Speech Only
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="playback_mode" id="tts_mp3" value="tts_mp3">
                                <label class="form-check-label" for="tts_mp3">
                                    Text-to-Speech + MP3
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="playback_mode" id="mp3_only" value="mp3_only">
                                <label class="form-check-label" for="mp3_only">
                                    MP3 Only
                                </label>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label id="mp3_selection_label" for="random_mp3">MP3 Selection</label>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="mp3_selection" id="random_mp3" value="random" checked>
                                <label class="form-check-label" for="random_mp3">
                                    Random MP3
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="mp3_selection" id="specific_mp3" value="specific">
                                <label class="form-check-label" for="specific_mp3">
                                    Specific MP3
                                </label>
                            </div>
                            
                            <div id="specific_mp3_container" class="form-group mt-2">
                                <label for="mp3_file">Select MP3 File</label>
                                <select class="form-control" id="mp3_file">
                                    {mp3_options}
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label id="tts_provider_label" for="twilio_voice">Text-to-Speech Provider</label>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="tts_provider" id="twilio_voice" value="twilio" checked>
                                <label class="form-check-label" for="twilio_voice">
                                    Twilio Voice
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="tts_provider" id="eleven_labs" value="elevenlabs">
                                <label class="form-check-label" for="eleven_labs">
                                    Eleven Labs
                                </label>
                            </div>
                            
                            <div id="eleven_labs_voices_container" class="form-group mt-2">
                                <label for="eleven_labs_voice">Select Voice</label>
                                <select class="form-control" id="eleven_labs_voice">
                                    {voice_options}
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-check mb-3">
                            <input type="checkbox" class="form-check-input" id="save_tts">
                            <label class="form-check-label" for="save_tts">Save Text-to-Speech as MP3</label>
                        </div>
                        
                        <a href="/manage-mp3" class="btn btn-info" target="_blank">
                            <i class="fas fa-music"></i> Manage MP3 Files
                        </a>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="status" class="mt-4">
            <h3>Call Status</h3>
            <div id="callStatus"></div>
        </div>
        
        <div class="test-links">
            <h4>Test Pages</h4>
            <a href="/test-mp3" target="_blank">Test MP3 Playback</a>
            <a href="/test-static" target="_blank">Test Static Files</a>
            <a href="/test-twilio" target="_blank">Test Twilio Integration</a>
        </div>
        
        <footer>
            <p>
                <a href="https://github.com/webdevtodayjason/callcenter-testing" target="_blank">
                    <i class="fab fa-github fa-2x"></i>
                    <span class="ml-2">View on GitHub</span>
                </a>
            </p>
            <p class="text-muted">© 2023 Jason Brashear</p>
        </footer>
    </div>

    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/js/bootstrap.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        $(document).ready(function() {{
            console.log("Document ready");

            // Check if the elements exist in the DOM
            console.log("Checking if elements exist:");
            console.log("- mp3_file exists:", $('#mp3_file').length > 0);
            console.log("- eleven_labs_voice exists:", $('#eleven_labs_voice').length > 0);
            
            // Manually check initial states - no need to show/hide anymore
            console.log("Initial states:");
            console.log("- Custom greeting:", $('#use_custom_greeting').is(':checked'));
            console.log("- Specific MP3:", $('#specific_mp3').is(':checked'));
            console.log("- Eleven Labs:", $('#eleven_labs').is(':checked'));
            
            // Trigger change events to ensure proper initial state
            $('#use_custom_greeting').trigger('change');
            $('input[name="mp3_selection"]:checked').trigger('change');
            $('input[name="tts_provider"]:checked').trigger('change');
            
            // Connect to Socket.IO
            const socket = io();
            
            // Add debugging for Socket.IO connection events
            socket.on('connect', function() {{
                console.log('Socket.IO connected successfully with ID:', socket.id);
            }});
            
            socket.on('connect_error', function(error) {{
                console.error('Socket.IO connection error:', error);
            }});
            
            socket.on('connect_timeout', function() {{
                console.error('Socket.IO connection timeout');
            }});
            
            socket.on('error', function(error) {{
                console.error('Socket.IO error:', error);
            }});
            
            socket.on('disconnect', function(reason) {{
                console.log('Socket.IO disconnected, reason:', reason);
            }});
            
            // Handle form submission
            $('#callForm').submit(function(e) {{
                e.preventDefault();
                console.log('Call form submitted');
                
                const phoneNumbers = $('#phone_numbers').val().split('\\n').filter(n => n.trim() !== '');
                console.log('Phone numbers:', phoneNumbers);
                
                if (phoneNumbers.length === 0) {{
                    alert('Please enter at least one phone number.');
                    return;
                }}
                
                // Get form values
                const delay = $('#delay').val();
                const simultaneous_calls = $('#simultaneous_calls').val();
                
                // Validate simultaneous calls
                if (phoneNumbers.length > 1 && parseInt(simultaneous_calls) > 1) {{
                    alert('Simultaneous calls (>1) can only be used with a single phone number.');
                    return;
                }}
                
                // Cap simultaneous calls at 50
                const finalSimultaneousCalls = Math.min(parseInt(simultaneous_calls), 50);
                
                const useCustomGreeting = $('#use_custom_greeting').is(':checked');
                const customGreeting = $('#custom_greeting').val();
                const playbackMode = $('input[name="playback_mode"]:checked').val();
                const mp3Selection = $('input[name="mp3_selection"]:checked').val();
                const mp3File = $('#mp3_file').val();
                const ttsProvider = $('input[name="tts_provider"]:checked').val();
                console.log("Selected TTS provider:", ttsProvider);
                const elevenLabsVoice = $('#eleven_labs_voice').val();
                const saveTts = $('#save_tts').is(':checked');
                
                // Disable start button, enable stop button
                $('#startButton').prop('disabled', true);
                $('#stopButton').prop('disabled', false);
                
                // Clear previous call status
                $('#callStatus').empty();
                
                // Send data to server
                console.log("Emitting start_calls event to server with TTS provider:", ttsProvider);
                socket.emit('start_calls', {{
                    phone_numbers: phoneNumbers,
                    delay: delay,
                    simultaneous_calls: finalSimultaneousCalls,
                    use_custom_greeting: useCustomGreeting,
                    custom_greeting: customGreeting,
                    playback_mode: playbackMode,
                    mp3_selection: mp3Selection,
                    mp3_file: mp3File,
                    tts_provider: ttsProvider,
                    eleven_labs_voice: elevenLabsVoice,
                    save_tts: saveTts
                }});
            }});
            
            // Handle stop button click
            $('#stopButton').click(function() {{
                socket.emit('stop_calls');
                $('#startButton').prop('disabled', false);
                $('#stopButton').prop('disabled', true);
            }});
            
            // Handle call status updates
            socket.on('call_status', function(data) {{
                const statusClass = data.status === 'pending' ? 'pending' :
                                   data.status === 'in-progress' ? 'in-progress' :
                                   data.status === 'completed' ? 'completed' : 'failed';
                
                // Check if the call status already exists
                const callStatusElement = $('#call-' + data.call_id);
                if (callStatusElement.length) {{
                    // Update existing call status
                    callStatusElement.removeClass('pending in-progress completed failed').addClass(statusClass);
                    callStatusElement.html('<strong>' + data.phone_number + '</strong>: ' + data.status + (data.message ? ' - ' + data.message : ''));
                }} else {{
                    // Add new call status
                    $('#callStatus').append(
                        '<div id="call-' + data.call_id + '" class="call-status ' + statusClass + '">' +
                            '<strong>' + data.phone_number + '</strong>: ' + data.status + (data.message ? ' - ' + data.message : '') +
                        '</div>'
                    );
                }}
            }});
            
            // Handle all calls completed
            socket.on('all_calls_completed', function() {{
                $('#startButton').prop('disabled', false);
                $('#stopButton').prop('disabled', true);
            }});
            
            // MP3 files and Eleven Labs voices are pre-populated by Python
            console.log("MP3 files and Eleven Labs voices pre-populated");
            
            // Toggle custom greeting textarea - keep tracking state but don't hide/show
            $('#use_custom_greeting').change(function() {{
                console.log("Custom greeting checkbox changed:", $(this).is(':checked'));
                // We're not hiding/showing anymore, just tracking state
            }});
            
            // Toggle MP3 selection dropdown - keep tracking state but don't hide/show
            $('input[name="mp3_selection"]').change(function() {{
                console.log("MP3 selection changed:", $('#specific_mp3').is(':checked'));
                // We're not hiding/showing anymore, just tracking state
            }});
            
            // Toggle Eleven Labs voices dropdown - keep tracking state but don't hide/show
            $('input[name="tts_provider"]').change(function() {{
                console.log("TTS provider changed:", $('#eleven_labs').is(':checked'));
                // We're not hiding/showing anymore, just tracking state
            }});
            
            // Validate simultaneous calls - only allow >1 for single phone number
            $('#phone_numbers, #simultaneous_calls').on('input change', function() {{
                const phoneNumbers = $('#phone_numbers').val().split('\\n').filter(n => n.trim() !== '');
                const simultaneousCalls = parseInt($('#simultaneous_calls').val(), 10);
                
                if (phoneNumbers.length > 1 && simultaneousCalls > 1) {{
                    alert('Simultaneous calls (>1) can only be used with a single phone number. Please either enter just one phone number or set simultaneous calls to 1.');
                    $('#simultaneous_calls').val(1);
                }}
            }});
        }});
    </script>
</body>
</html>
"""
    
    # Format the HTML with the options
    return html.format(mp3_options=mp3_options, voice_options=voice_options)

@app.route('/')
def index():
    """Main page."""
    return generate_admin_html()

@app.route('/initiate_calls', methods=['POST'])
def initiate_calls():
    """Legacy endpoint for initiating calls. Now redirects to the main page."""
    logger.info("Legacy initiate_calls endpoint accessed, redirecting to main page")
    return redirect(url_for('index'))

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('start_calls')
def handle_start_calls(data):
    """Handle start calls request from client."""
    logger.info(f"Received start_calls request: {data}")
    logger.info(f"Client SID: {request.sid}")
    
    try:
        # Extract data
        phone_numbers = data.get('phone_numbers', [])
        logger.info(f"Phone numbers to call: {phone_numbers}")
        
        delay = int(data.get('delay', 5))
        simultaneous_calls = int(data.get('simultaneous_calls', 1))
        
        # Server-side validation for simultaneous calls
        if len(phone_numbers) > 1 and simultaneous_calls > 1:
            logger.warning("Attempted to use simultaneous calls with multiple phone numbers")
            simultaneous_calls = 1  # Force to 1 for multiple numbers
        
        # Cap simultaneous calls at 50
        simultaneous_calls = min(simultaneous_calls, 50)
        
        use_custom_greeting = data.get('use_custom_greeting', False)
        custom_greeting = data.get('custom_greeting', '')
        logger.info(f"Custom greeting: {'Yes - ' + custom_greeting if use_custom_greeting else 'No'}")
        
        playback_mode = data.get('playback_mode', 'mp3_only')
        mp3_selection = data.get('mp3_selection', 'random')
        mp3_file = data.get('mp3_file', '')
        tts_provider = data.get('tts_provider', 'twilio')
        eleven_labs_voice = data.get('eleven_labs_voice', '')
        save_tts = data.get('save_tts', False)
        
        logger.info(f"Starting call thread with: mode={playback_mode}, provider={tts_provider}, simultaneous={simultaneous_calls}")
        
        # Start a thread to make calls
        thread = Thread(target=make_calls, args=(
            phone_numbers, 
            delay, 
            simultaneous_calls,
            use_custom_greeting,
            custom_greeting,
            playback_mode,
            mp3_selection,
            mp3_file,
            tts_provider,
            eleven_labs_voice,
            save_tts,
            request.sid
        ))
        thread.daemon = True
        thread.start()
        logger.info(f"Call thread started successfully")
        
        return {'status': 'success', 'message': 'Calls initiated'}
    except Exception as e:
        logger.error(f"Error in handle_start_calls: {str(e)}", exc_info=True)
        return {'status': 'error', 'message': f'Error initiating calls: {str(e)}'}

@socketio.on('stop_calls')
def handle_stop_calls():
    """Handle stop calls request from client."""
    logger.info("Received stop_calls request")
    # Set a flag to stop making calls
    global stop_calls_flag
    stop_calls_flag = True
    return {'status': 'success', 'message': 'Calls stopped'}

# Flag to control call flow
stop_calls_flag = False

def make_calls(phone_numbers, delay, simultaneous_calls, use_custom_greeting, custom_greeting, 
               playback_mode, mp3_selection, mp3_file, tts_provider, 
               eleven_labs_voice, save_tts, client_sid):
    """Make calls to the specified phone numbers with the specified settings."""
    global stop_calls_flag
    stop_calls_flag = False
    
    # Check if we're doing simultaneous calls to a single number
    if len(phone_numbers) == 1 and simultaneous_calls > 1:
        phone_number = phone_numbers[0].strip()
        if not phone_number:
            return
            
        logger.info(f"Making {simultaneous_calls} simultaneous calls to {phone_number}")
        
        # Emit pending status for all simultaneous calls
        for i in range(simultaneous_calls):
            call_id = f"call_{i}_{int(time.time())}"
            socketio.emit('call_status', {
                'call_id': call_id,
                'phone_number': f"{phone_number} (Call {i+1}/{simultaneous_calls})",
                'status': 'pending',
                'message': 'Preparing to call'
            }, room=client_sid)
        
        # Create threads for simultaneous calls
        threads = []
        for i in range(simultaneous_calls):
            if stop_calls_flag:
                logger.info("Stopping calls as requested")
                break
                
            call_id = f"call_{i}_{int(time.time())}"
            
            # Create thread for this call
            thread = Thread(target=make_single_call, args=(
                phone_number,
                call_id,
                f"{phone_number} (Call {i+1}/{simultaneous_calls})",
                use_custom_greeting,
                custom_greeting,
                playback_mode,
                mp3_selection,
                mp3_file,
                tts_provider,
                eleven_labs_voice,
                save_tts,
                client_sid
            ))
            thread.daemon = True
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
            time.sleep(0.2)  # Small delay to prevent rate limiting
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
            
        # All calls completed
        if not stop_calls_flag:
            socketio.emit('all_calls_completed', room=client_sid)
    else:
        # Original behavior for multiple different numbers or just one call
        for i, phone_number in enumerate(phone_numbers):
            if stop_calls_flag:
                logger.info("Stopping calls as requested")
                break
            
            # Clean the phone number
            phone_number = phone_number.strip()
            if not phone_number:
                continue
            
            # Generate a unique call ID
            call_id = f"call_{i}_{int(time.time())}"
            
            # Emit pending status
            socketio.emit('call_status', {
                'call_id': call_id,
                'phone_number': phone_number,
                'status': 'pending',
                'message': 'Preparing to call'
            }, room=client_sid)
            
            # Make the single call
            make_single_call(
                phone_number,
                call_id,
                phone_number,
                use_custom_greeting,
                custom_greeting,
                playback_mode,
                mp3_selection,
                mp3_file,
                tts_provider,
                eleven_labs_voice,
                save_tts,
                client_sid
            )
            
            # Wait for the specified delay before making the next call
            if i < len(phone_numbers) - 1 and not stop_calls_flag:
                time.sleep(delay)
        
        # All calls completed
        if not stop_calls_flag:
            socketio.emit('all_calls_completed', room=client_sid)

def make_single_call(phone_number, call_id, display_number, use_custom_greeting, custom_greeting,
                    playback_mode, mp3_selection, mp3_file, tts_provider, 
                    eleven_labs_voice, save_tts, client_sid):
    """Make a single call with the specified settings."""
    try:
        logger.info(f"Making call to {phone_number} (ID: {call_id})")
        
        # Prepare TwiML URL parameters
        url_params = {
            'use_custom_greeting': 'true' if use_custom_greeting else 'false',
            'playback_mode': playback_mode,
            'tts_provider': tts_provider,
            'call_id': call_id
        }
        
        if use_custom_greeting and custom_greeting:
            url_params['greeting'] = custom_greeting
            logger.info(f"Using custom greeting: {custom_greeting}")
        
        if playback_mode in ['tts_mp3', 'mp3_only']:
            if mp3_selection == 'random':
                if mp3_files:
                    url_params['mp3_file'] = random.choice(mp3_files)
                    logger.info(f"Selected random MP3: {url_params['mp3_file']}")
                else:
                    logger.warning("No MP3 files available for random selection")
            else:
                url_params['mp3_file'] = mp3_file
                logger.info(f"Using specific MP3: {mp3_file}")
        
        if tts_provider == 'elevenlabs' and eleven_labs_voice:
            url_params['voice'] = eleven_labs_voice
            logger.info(f"Using Eleven Labs voice: {eleven_labs_voice}")
        
        if save_tts:
            url_params['save_tts'] = 'true'
        
        # Construct the TwiML URL
        twiml_url = f"{base_url}/twiml?{urllib.parse.urlencode(url_params)}"
        logger.info(f"TwiML URL: {twiml_url}")
        
        # Log Twilio credentials (partial for security)
        logger.info(f"Using Twilio account: {account_sid[:4]}...{account_sid[-4:]}")
        logger.info(f"Using Twilio phone number: {twilio_number}")
        
        # Emit in-progress status
        try:
            socketio.emit('call_status', {
                'call_id': call_id,
                'phone_number': display_number,
                'status': 'in-progress',
                'message': 'Initiating call'
            }, room=client_sid)
            logger.info(f"Emitted in-progress status for {call_id}")
        except Exception as e:
            logger.error(f"Failed to emit call status: {str(e)}")
        
        # Make the call
        logger.info(f"Calling Twilio API for {phone_number}")
        try:
            call = client.calls.create(
                to=phone_number,
                from_=twilio_number,
                url=twiml_url,
                status_callback=f"{base_url}/call-status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                status_callback_method='POST'
            )
            logger.info(f"Twilio API call succeeded, SID: {call.sid}")
        except Exception as e:
            logger.error(f"Twilio API call failed: {str(e)}", exc_info=True)
            raise
        
        # Store call information
        calls[call.sid] = {
            'call_id': call_id,
            'phone_number': display_number,
            'status': 'initiated',
            'client_sid': client_sid
        }
        
        logger.info(f"Call initiated to {phone_number}, SID: {call.sid}")
        
        # Emit status update
        socketio.emit('call_status', {
            'call_id': call_id,
            'phone_number': display_number,
            'status': 'in-progress',
            'message': f'Call initiated (SID: {call.sid})'
        }, room=client_sid)
        logger.info(f"Emitted call initiated status for {call_id}")
            
    except Exception as e:
        logger.error(f"Error making call to {phone_number}: {str(e)}", exc_info=True)
        
        # Emit error status
        try:
            socketio.emit('call_status', {
                'call_id': call_id,
                'phone_number': display_number,
                'status': 'failed',
                'message': f'Error: {str(e)}'
            }, room=client_sid)
            logger.info(f"Emitted error status for {call_id}")
        except Exception as emit_error:
            logger.error(f"Failed to emit error status: {str(emit_error)}")

@app.route('/call-status', methods=['POST'])
def call_status():
    """Handle call status callbacks from Twilio."""
    call_sid = request.form.get('CallSid')
    call_status = request.form.get('CallStatus')
    
    logger.info(f"Call status update - SID: {call_sid}, Status: {call_status}")
    
    if call_sid in calls:
        call_info = calls[call_sid]
        call_info['status'] = call_status
        
        # Emit status update to the client
        socketio.emit('call_status', {
            'call_id': call_info['call_id'],
            'phone_number': call_info['phone_number'],
            'status': 'completed' if call_status in ['completed', 'busy', 'no-answer', 'failed'] else 'in-progress',
            'message': f'Call {call_status}'
        }, room=call_info['client_sid'])
    
    return '', 204

def generate_elevenlabs_speech(text, voice_name, save_path=None):
    """Generate speech using the Eleven Labs API and return a URL to the audio file."""
    logger.info(f"Generating Eleven Labs speech with voice: {voice_name}")
    
    if not elevenlabs_api_key:
        logger.error("Eleven Labs API key is not set")
        return None
    
    # Get the voice ID from the voice name
    voice_id = elevenlabs_voices.get(voice_name)
    if not voice_id:
        logger.error(f"Voice {voice_name} not found in configured voices")
        return None
    
    # Prepare API request
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": elevenlabs_api_key
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    try:
        # Make the API request
        logger.info(f"Making Eleven Labs API request for voice {voice_name} (ID: {voice_id})")
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            # If we need to save the file
            if save_path:
                # This is a custom path
                file_path = save_path
            else:
                # Generate a temporary file
                file_name = f"elevenlabs_{uuid.uuid4()}.mp3"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
            
            # Save the audio file
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Return the URL to the audio file
            audio_url = f"{base_url}/static/mp3/{os.path.basename(file_path)}"
            logger.info(f"Eleven Labs audio saved to {file_path}, URL: {audio_url}")
            return audio_url
        else:
            logger.error(f"Eleven Labs API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception during Eleven Labs API call: {str(e)}", exc_info=True)
        return None

@app.route('/twiml', methods=['GET', 'POST'])
def twiml():
    """Generate TwiML for the call."""
    # Get parameters
    use_custom_greeting = request.args.get('use_custom_greeting') == 'true'
    custom_greeting = request.args.get('greeting', '')
    playback_mode = request.args.get('playback_mode', 'mp3_only')
    mp3_file = request.args.get('mp3_file', '')
    tts_provider = request.args.get('tts_provider', 'twilio')
    voice = request.args.get('voice', '')
    save_tts = request.args.get('save_tts') == 'true'
    call_id = request.args.get('call_id', '')
    
    logger.info(f"TwiML request - Playback Mode: {playback_mode}, MP3 File: {mp3_file}, TTS Provider: {tts_provider}, Voice: {voice}")
    
    # Create TwiML response
    response = VoiceResponse()
    
    # Add a pause to ensure audio starts playing correctly
    response.pause(length=1)
    
    # Handle different playback modes
    if playback_mode == 'tts_only':
        # Text-to-Speech Only
        if use_custom_greeting and custom_greeting:
            if tts_provider == 'elevenlabs' and elevenlabs_api_key:
                # Generate Eleven Labs speech
                audio_url = generate_elevenlabs_speech(
                    custom_greeting, 
                    voice if voice else next(iter(elevenlabs_voices.keys()), None),
                    save_path=os.path.join(app.config['UPLOAD_FOLDER'], f"tts_{call_id}.mp3") if save_tts else None
                )
                
                if audio_url:
                    # Play the generated audio
                    response.play(audio_url)
                else:
                    # Fallback to Twilio TTS
                    logger.warning("Falling back to Twilio TTS due to Eleven Labs error")
                    response.say(custom_greeting)
            else:
                response.say(custom_greeting)
        else:
            response.say("This is a test call from the Call Center Testing application.")
    
    elif playback_mode == 'tts_mp3':
        # Text-to-Speech + MP3
        if use_custom_greeting and custom_greeting:
            if tts_provider == 'elevenlabs' and elevenlabs_api_key:
                # Generate Eleven Labs speech
                audio_url = generate_elevenlabs_speech(
                    custom_greeting, 
                    voice if voice else next(iter(elevenlabs_voices.keys()), None),
                    save_path=os.path.join(app.config['UPLOAD_FOLDER'], f"tts_{call_id}.mp3") if save_tts else None
                )
                
                if audio_url:
                    # Play the generated audio
                    response.play(audio_url)
                else:
                    # Fallback to Twilio TTS
                    logger.warning("Falling back to Twilio TTS due to Eleven Labs error")
                    response.say(custom_greeting)
            else:
                response.say(custom_greeting)
        else:
            response.say("This is a test call from the Call Center Testing application.")
        
        # Then play MP3
        if mp3_file and mp3_file in mp3_files:
            mp3_url = f"{base_url}/static/mp3/{mp3_file}"
            response.play(mp3_url)
        else:
            response.say("No MP3 file was selected or the file is not available.")
    
    elif playback_mode == 'mp3_only':
        # MP3 Only
        if mp3_file and mp3_file in mp3_files:
            mp3_url = f"{base_url}/static/mp3/{mp3_file}"
            response.play(mp3_url)
        else:
            response.say("No MP3 file was selected or the file is not available.")
    
    # Log the TwiML for debugging
    logger.info(f"Generated TwiML: {response}")
    
    return Response(str(response), mimetype='text/xml')

@app.route('/test-mp3')
def test_mp3():
    """Test route to check MP3 accessibility."""
    mp3_list = []
    for mp3 in mp3_files:
        mp3_url = f"{base_url}/static/mp3/{mp3}"
        mp3_list.append({
            'file': mp3,
            'url': mp3_url
        })
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MP3 Test</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
        <style>
            footer {{ margin-top: 50px; padding: 20px 0; border-top: 1px solid #dee2e6; text-align: center; }}
            footer a {{ color: #007bff; }}
            footer a:hover {{ color: #0056b3; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container mt-5">
            <h1>MP3 Test Page</h1>
            <p>Base URL: {base_url}</p>
            <h2>MP3 Files</h2>
            <ul class="list-group">
                {''.join([f'<li class="list-group-item"><a href="{mp3["url"]}" target="_blank">{mp3["file"]}</a> - <audio controls src="{mp3["url"]}"></audio></li>' for mp3 in mp3_list])}
            </ul>
            
            <div class="mt-4">
                <a href="/" class="btn btn-primary">Back to Main Page</a>
            </div>
            
            <footer>
                <p>
                    <a href="https://github.com/webdevtodayjason/callcenter-testing" target="_blank">
                        <i class="fab fa-github fa-2x"></i>
                        <span class="ml-2">View on GitHub</span>
                    </a>
                </p>
                <p class="text-muted">© 2023 Jason Brashear</p>
            </footer>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/test-static')
def test_static():
    """Test if static files are being served correctly."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Static File Test</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
        <style>
            footer {{ margin-top: 50px; padding: 20px 0; border-top: 1px solid #dee2e6; text-align: center; }}
            footer a {{ color: #007bff; }}
            footer a:hover {{ color: #0056b3; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container mt-5">
            <h1>Static File Test</h1>
            <p>This page tests if static files are being served correctly.</p>
            <div class="alert alert-info">
                If you see this page, the Flask server is running correctly.
            </div>
            <p>Try accessing a static file directly:</p>
            <a href="/static/mp3/file1.mp3" class="btn btn-primary">Test MP3 File</a>
            
            <div class="mt-4">
                <a href="/" class="btn btn-primary">Back to Main Page</a>
            </div>
            
            <footer>
                <p>
                    <a href="https://github.com/webdevtodayjason/callcenter-testing" target="_blank">
                        <i class="fab fa-github fa-2x"></i>
                        <span class="ml-2">View on GitHub</span>
                    </a>
                </p>
                <p class="text-muted">© 2023 Jason Brashear</p>
            </footer>
        </div>
    </body>
    </html>
    """

@app.route('/test-twilio')
def test_twilio():
    """Test Twilio account status."""
    try:
        # Get account information
        account = client.api.accounts(account_sid).fetch()
        
        # Get available phone numbers
        phone_numbers = client.incoming_phone_numbers.list(limit=10)
        
        # Format phone numbers for display
        formatted_numbers = []
        for number in phone_numbers:
            formatted_numbers.append({
                'sid': number.sid,
                'phone_number': number.phone_number,
                'friendly_name': number.friendly_name
            })
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Twilio Account Test</title>
            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
            <style>
                footer {{ margin-top: 50px; padding: 20px 0; border-top: 1px solid #dee2e6; text-align: center; }}
                footer a {{ color: #007bff; }}
                footer a:hover {{ color: #0056b3; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container mt-5">
                <h1>Twilio Account Status</h1>
                <div class="card mb-4">
                    <div class="card-header">Account Information</div>
                    <div class="card-body">
                        <p><strong>Account SID:</strong> {account.sid}</p>
                        <p><strong>Account Status:</strong> {account.status}</p>
                        <p><strong>Account Type:</strong> {account.type}</p>
                    </div>
                </div>
                
                <h2>Phone Numbers</h2>
                <div class="card">
                    <div class="card-header">Available Phone Numbers</div>
                    <div class="card-body">
                        <p><strong>Configured Twilio Number:</strong> {twilio_number}</p>
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>SID</th>
                                    <th>Phone Number</th>
                                    <th>Friendly Name</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join([f'<tr><td>{num["sid"]}</td><td>{num["phone_number"]}</td><td>{num["friendly_name"]}</td></tr>' for num in formatted_numbers])}
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <h2>Test Call</h2>
                <div class="card mt-4">
                    <div class="card-header">Make a Test Call</div>
                    <div class="card-body">
                        <form action="/test-call" method="post">
                            <div class="form-group">
                                <label for="test_number">Phone Number to Call</label>
                                <input type="text" class="form-control" id="test_number" name="test_number" placeholder="+1234567890" required>
                            </div>
                            <button type="submit" class="btn btn-primary">Make Test Call</button>
                        </form>
                    </div>
                </div>
                
                <div class="mt-4">
                    <a href="/" class="btn btn-primary">Back to Main Page</a>
                </div>
                
                <footer>
                    <p>
                        <a href="https://github.com/webdevtodayjason/callcenter-testing" target="_blank">
                            <i class="fab fa-github fa-2x"></i>
                            <span class="ml-2">View on GitHub</span>
                        </a>
                    </p>
                    <p class="text-muted">© 2023 Jason Brashear</p>
                </footer>
            </div>
        </body>
        </html>
        """
        return html
    except Exception as e:
        return f"""
        <html>
        <head>
            <title>Error checking Twilio account</title>
            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
            <style>
                footer {{ margin-top: 50px; padding: 20px 0; border-top: 1px solid #dee2e6; text-align: center; }}
                footer a {{ color: #007bff; }}
                footer a:hover {{ color: #0056b3; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container mt-5">
                <div class="alert alert-danger">
                    <h1>Error checking Twilio account</h1>
                    <p>{str(e)}</p>
                </div>
                <a href="/" class="btn btn-primary">Back to Main Page</a>
                
                <footer>
                    <p>
                        <a href="https://github.com/webdevtodayjason/callcenter-testing" target="_blank">
                            <i class="fab fa-github fa-2x"></i>
                            <span class="ml-2">View on GitHub</span>
                        </a>
                    </p>
                    <p class="text-muted">© 2023 Jason Brashear</p>
                </footer>
            </div>
        </body>
        </html>
        """

@app.route('/test-call', methods=['POST'])
def test_call():
    """Make a test call with simple TwiML."""
    try:
        test_number = request.form['test_number']
        
        call = client.calls.create(
            to=test_number,
            from_=twilio_number,
            url=f"{base_url}/simple-twiml",
            status_callback=f"{base_url}/status",
            status_callback_method='POST'
        )
        
        return f"""
        <html>
        <head>
            <title>Test Call Initiated</title>
            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
            <meta http-equiv="refresh" content="5;url=/" />
            <style>
                footer {{ margin-top: 50px; padding: 20px 0; border-top: 1px solid #dee2e6; text-align: center; }}
                footer a {{ color: #007bff; }}
                footer a:hover {{ color: #0056b3; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container mt-5">
                <div class="alert alert-success">
                    <h4>Test Call Initiated</h4>
                    <p>Call SID: {call.sid}</p>
                    <p>Status: {call.status}</p>
                </div>
                <p>Redirecting to main page in 5 seconds...</p>
                
                <div class="mt-4">
                    <a href="/" class="btn btn-primary">Back to Main Page</a>
                </div>
                
                <footer>
                    <p>
                        <a href="https://github.com/webdevtodayjason/callcenter-testing" target="_blank">
                            <i class="fab fa-github fa-2x"></i>
                            <span class="ml-2">View on GitHub</span>
                        </a>
                    </p>
                    <p class="text-muted">© 2023 Jason Brashear</p>
                </footer>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        return f"""
        <html>
        <head>
            <title>Test Call Failed</title>
            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
            <style>
                footer {{ margin-top: 50px; padding: 20px 0; border-top: 1px solid #dee2e6; text-align: center; }}
                footer a {{ color: #007bff; }}
                footer a:hover {{ color: #0056b3; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container mt-5">
                <div class="alert alert-danger">
                    <h4>Test Call Failed</h4>
                    <p>Error: {str(e)}</p>
                </div>
                <a href="/" class="btn btn-primary">Back to Main Page</a>
                
                <footer>
                    <p>
                        <a href="https://github.com/webdevtodayjason/callcenter-testing" target="_blank">
                            <i class="fab fa-github fa-2x"></i>
                            <span class="ml-2">View on GitHub</span>
                        </a>
                    </p>
                    <p class="text-muted">© 2023 Jason Brashear</p>
                </footer>
            </div>
        </body>
        </html>
        """

@app.route('/simple-twiml', methods=['POST', 'GET'])
def simple_twiml():
    """Provide a very simple TwiML response for testing."""
    logger.info(f"Simple TwiML request received with values: {request.values}")
    
    twiml = """
    <Response>
        <Say>This is a simple test call without MP3 files.</Say>
        <Pause length="1"/>
        <Say>If you hear this message, basic Twilio functionality is working correctly.</Say>
    </Response>
    """
    
    return Response(twiml, mimetype='text/xml')

@app.route('/api/mp3-files', methods=['GET'])
def api_mp3_files():
    """API endpoint to get all MP3 files."""
    global mp3_files
    mp3_files = get_mp3_files()
    return jsonify({"files": mp3_files})

@app.route('/api/eleven-labs-voices', methods=['GET'])
def api_eleven_labs_voices():
    """API endpoint to get all ElevenLabs voices."""
    return jsonify({"voices": elevenlabs_voices})

@app.route('/manage-mp3')
def manage_mp3():
    """Page to manage MP3 files."""
    global mp3_files
    mp3_files = get_mp3_files()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manage MP3 Files</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
        <style>
            footer {{ margin-top: 50px; padding: 20px 0; border-top: 1px solid #dee2e6; text-align: center; }}
            footer a {{ color: #007bff; }}
            footer a:hover {{ color: #0056b3; text-decoration: none; }}
            .file-actions {{ white-space: nowrap; }}
        </style>
    </head>
    <body>
        <div class="container mt-5">
            <h1>Manage MP3 Files</h1>
            
            <div class="card mb-4">
                <div class="card-header">Upload New MP3 File</div>
                <div class="card-body">
                    <form action="/upload-mp3" method="post" enctype="multipart/form-data">
                        <div class="form-group">
                            <label for="mp3_file">Select MP3 File</label>
                            <input type="file" class="form-control-file" id="mp3_file" name="mp3_file" accept=".mp3,.wav" required>
                            <small class="form-text text-muted">Max file size: 16MB. Allowed formats: MP3, WAV</small>
                        </div>
                        <button type="submit" class="btn btn-primary">Upload</button>
                    </form>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">MP3 Files</div>
                <div class="card-body">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Filename</th>
                                <th>Preview</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f'''
                            <tr>
                                <td>{file}</td>
                                <td><audio controls src="{base_url}/static/mp3/{file}" style="max-width: 300px;"></audio></td>
                                <td class="file-actions">
                                    <button type="button" class="btn btn-sm btn-info rename-btn" data-filename="{file}">
                                        <i class="fas fa-edit"></i> Rename
                                    </button>
                                    <a href="/delete-mp3/{file}" class="btn btn-sm btn-danger" onclick="return confirm('Are you sure you want to delete this file?')">
                                        <i class="fas fa-trash"></i> Delete
                                    </a>
                                </td>
                            </tr>
                            ''' for file in mp3_files])}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="mt-4">
                <a href="/" class="btn btn-primary">Back to Main Page</a>
            </div>
            
            <!-- Rename Modal -->
            <div class="modal fade" id="renameModal" tabindex="-1" role="dialog" aria-labelledby="renameModalLabel" aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="renameModalLabel">Rename File</h5>
                            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                        <form action="/rename-mp3" method="post">
                            <div class="modal-body">
                                <input type="hidden" id="original_filename" name="original_filename">
                                <div class="form-group">
                                    <label for="new_filename">New Filename</label>
                                    <input type="text" class="form-control" id="new_filename" name="new_filename" required>
                                    <small class="form-text text-muted">Include file extension (.mp3 or .wav)</small>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                                <button type="submit" class="btn btn-primary">Rename</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
            
            <footer>
                <p>
                    <a href="https://github.com/webdevtodayjason/callcenter-testing" target="_blank">
                        <i class="fab fa-github fa-2x"></i>
                        <span class="ml-2">View on GitHub</span>
                    </a>
                </p>
                <p class="text-muted">© 2023 Jason Brashear</p>
            </footer>
        </div>
        
        <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/js/bootstrap.min.js"></script>
        <script>
            $(document).ready(function() {{
                /* Handle rename button click */
                $('.rename-btn').click(function() {{
                    var filename = $(this).data('filename');
                    $('#original_filename').val(filename);
                    $('#new_filename').val(filename);
                    $('#renameModal').modal('show');
                }});
            }});
        </script>
    </body>
    </html>
    """
    return html

@app.route('/upload-mp3', methods=['POST'])
def upload_mp3():
    """Handle MP3 file upload."""
    if 'mp3_file' not in request.files:
        return redirect(url_for('manage_mp3'))
    
    file = request.files['mp3_file']
    
    if file.filename == '':
        return redirect(url_for('manage_mp3'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file
        file.save(file_path)
        
        # Update the mp3_files list
        global mp3_files
        mp3_files = get_mp3_files()
        
        logger.info(f"Uploaded new MP3 file: {filename}")
        
        return redirect(url_for('manage_mp3'))
    
    return redirect(url_for('manage_mp3'))

@app.route('/delete-mp3/<filename>')
def delete_mp3(filename):
    """Delete an MP3 file."""
    if not filename or '..' in filename:  # Basic security check
        return redirect(url_for('manage_mp3'))
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"Deleted MP3 file: {filename}")
        
        # Update the mp3_files list
        global mp3_files
        mp3_files = get_mp3_files()
    
    return redirect(url_for('manage_mp3'))

@app.route('/rename-mp3', methods=['POST'])
def rename_mp3():
    """Rename an MP3 file."""
    original_filename = request.form.get('original_filename')
    new_filename = request.form.get('new_filename')
    
    if not original_filename or not new_filename or '..' in original_filename or '..' in new_filename:
        return redirect(url_for('manage_mp3'))
    
    # Ensure new filename has a valid extension
    if not allowed_file(new_filename):
        return redirect(url_for('manage_mp3'))
    
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
    new_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(new_filename))
    
    if os.path.exists(original_path):
        os.rename(original_path, new_path)
        logger.info(f"Renamed MP3 file: {original_filename} to {new_filename}")
        
        # Update the mp3_files list
        global mp3_files
        mp3_files = get_mp3_files()
    
    return redirect(url_for('manage_mp3'))

if __name__ == '__main__':
    # Print configuration for debugging
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Twilio Number: {twilio_number}")
    logger.info(f"MP3 Files: {mp3_files}")
    logger.info("Starting Flask application on port 5005")
    socketio.run(app, host='0.0.0.0', port=5005, debug=True)