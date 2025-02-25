from flask import Flask, request, Response, render_template_string, jsonify
from flask_socketio import SocketIO
from twilio.rest import Client
import os
import random
import logging
from threading import Thread
from dotenv import load_dotenv
import urllib.parse

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
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Twilio configuration
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_number = os.environ['TWILIO_PHONE_NUMBER']
base_url = os.environ['BASE_URL']

client = Client(account_sid, auth_token)

# In-memory storage for call statuses
calls = {}

# List of MP3 files (stored in static/mp3/)
mp3_files = ['file1.mp3', 'file2.mp3', 'file3.mp3', 'file4.mp3', 'file5.mp3', 
             'file6.mp3', 'file7.mp3', 'file8.mp3', 'file9.mp3', 'file10.mp3']

# Admin page HTML with Bootstrap and SocketIO
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Call Center Test Script</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <style>
        body { background-color: #343a40; color: #f8f9fa; }
        .container { max-width: 800px; margin-top: 50px; }
        .alert { display: none; margin-top: 20px; }
        .test-links { margin-top: 30px; }
        .test-links a { margin-right: 10px; color: #17a2b8; }
        #custom_greeting_text { display: none; }
        footer { margin-top: 50px; padding: 20px 0; border-top: 1px solid #495057; text-align: center; }
        footer a { color: #17a2b8; }
        footer a:hover { color: #138496; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Call Center Test Script</h1>
        <div id="alert" class="alert alert-success" role="alert">
            Calls initiated successfully!
        </div>
        <form id="callForm">
            <div class="form-group">
                <label for="target_number">Target Number</label>
                <input type="text" class="form-control" id="target_number" name="target_number" placeholder="+1234567890" required>
            </div>
            <div class="form-group">
                <label for="call_count">Call Count</label>
                <input type="number" class="form-control" id="call_count" name="call_count" min="1" max="50" value="1">
            </div>
            <div class="form-group form-check">
                <input type="checkbox" class="form-check-input" id="use_custom_greeting" name="use_custom_greeting">
                <label class="form-check-label" for="use_custom_greeting">Use Custom Intro Text-to-Speech</label>
            </div>
            <div class="form-group" id="custom_greeting_text">
                <label for="greeting_text">Custom Greeting Text</label>
                <textarea class="form-control" id="greeting_text" name="greeting_text" rows="3" placeholder="Enter your custom greeting text here..."></textarea>
            </div>
            <button type="submit" class="btn btn-primary">Initiate Calls</button>
        </form>
        <h2 class="mt-4">Call Activity</h2>
        <table class="table table-dark">
            <thead>
                <tr>
                    <th>Call SID</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody id="call_table_body"></tbody>
        </table>
        
        <div class="test-links">
            <h3>Test Pages</h3>
            <a href="/test-mp3" target="_blank">Test MP3 Files</a> | 
            <a href="/test-static" target="_blank">Test Static Files</a> | 
            <a href="/test-twilio" target="_blank">Test Twilio Account</a>
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
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script>
        $(document).ready(function() {
            var socket = io();
            
            // Toggle custom greeting text area based on checkbox
            $('#use_custom_greeting').change(function() {
                if($(this).is(':checked')) {
                    $('#custom_greeting_text').show();
                } else {
                    $('#custom_greeting_text').hide();
                }
            });
            
            // Handle form submission with AJAX
            $('#callForm').on('submit', function(e) {
                e.preventDefault();
                
                var formData = {
                    target_number: $('#target_number').val(),
                    call_count: $('#call_count').val(),
                    use_custom_greeting: $('#use_custom_greeting').is(':checked'),
                    greeting_text: $('#greeting_text').val()
                };
                
                $.ajax({
                    type: 'POST',
                    url: '/initiate_calls',
                    data: formData,
                    success: function(response) {
                        $('#alert').text(response.message).fadeIn().delay(3000).fadeOut();
                    },
                    error: function(error) {
                        $('#alert').removeClass('alert-success').addClass('alert-danger')
                            .text('Error: ' + error.responseText).fadeIn();
                    }
                });
            });
            
            // Socket.io event handlers
            socket.on('new_call', function(data) {
                var row = `<tr id="${data.call_sid}"><td>${data.call_sid}</td><td>${data.status}</td></tr>`;
                $('#call_table_body').append(row);
            });
            
            socket.on('call_update', function(data) {
                $(`#${data.call_sid} td:last`).text(data.status);
            });
        });
    </script>
</body>
</html>
"""

@app.route('/')
def admin_page():
    """Serve the admin page."""
    logger.info("Admin page accessed")
    return render_template_string(ADMIN_HTML)

@app.route('/initiate_calls', methods=['POST'])
def initiate_calls():
    """Handle form submission to initiate calls."""
    target_number = request.form['target_number']
    call_count = int(request.form['call_count'])
    use_custom_greeting = request.form.get('use_custom_greeting') == 'true'
    
    # Log the raw form data for debugging
    logger.info(f"Form data received: {request.form}")
    
    # Check if the checkbox is checked (value could be 'on', 'true', or simply present)
    use_custom_greeting = 'use_custom_greeting' in request.form
    greeting_text = request.form.get('greeting_text', '')
    
    logger.info(f"Initiating {call_count} calls to {target_number}")
    logger.info(f"Custom greeting enabled: {use_custom_greeting}, Text: {greeting_text}")
    
    # Start call initiation in a background thread
    thread = Thread(target=make_calls, args=(target_number, call_count, use_custom_greeting, greeting_text))
    thread.start()
    return jsonify({"message": f"Initiated {call_count} calls to {target_number}"}), 200

def make_calls(target_number, call_count, use_custom_greeting, greeting_text):
    """Initiate the specified number of calls to the target number."""
    for i in range(min(call_count, 50)):  # Cap at 50 calls
        try:
            logger.info(f"Making call {i+1} to {target_number}")
            logger.info(f"Custom greeting: {use_custom_greeting}, Text: {greeting_text}")
            
            # Create the TwiML URL with greeting parameters
            twiml_url = f"{base_url}/twiml"
            if use_custom_greeting and greeting_text:
                # URL encode the greeting text
                encoded_greeting = urllib.parse.quote(greeting_text)
                twiml_url = f"{twiml_url}?use_custom_greeting=true&greeting_text={encoded_greeting}"
                logger.info(f"Using custom greeting with text: {greeting_text}")
            else:
                twiml_url = f"{twiml_url}?use_custom_greeting=false"
                logger.info("No custom greeting will be used")
                
            logger.info(f"Using TwiML URL: {twiml_url}")
            
            call = client.calls.create(
                to=target_number,
                from_=twilio_number,
                url=twiml_url,
                status_callback=f"{base_url}/status",
                status_callback_method='POST'
            )
            calls[call.sid] = 'queued'
            logger.info(f"Call queued with SID: {call.sid}")
            socketio.emit('new_call', {'call_sid': call.sid, 'status': 'queued'})
        except Exception as e:
            logger.error(f"Error initiating call: {e}")

@app.route('/twiml', methods=['POST', 'GET'])
def twiml():
    """Provide TwiML instructions to Twilio to play a random MP3."""
    # Log all request values for debugging
    logger.info(f"TwiML request received with values: {request.values}")
    logger.info(f"TwiML request received from: {request.values.get('From', 'unknown')}")
    logger.info(f"TwiML request to: {request.values.get('To', 'unknown')}")
    
    # Get greeting preferences from request parameters
    use_custom_greeting = request.args.get('use_custom_greeting') == 'true'
    greeting_text = request.args.get('greeting_text', '')
    
    logger.info(f"Custom greeting enabled: {use_custom_greeting}, Text: {greeting_text}")
    
    # Select a random MP3 file
    mp3_file = random.choice(mp3_files)
    mp3_url = f"{base_url}/static/mp3/{mp3_file}"
    logger.info(f"Playing MP3: {mp3_url}")
    
    # Create a TwiML response with optional greeting and MP3 playback
    response = ['<Response>']
    
    # Add custom greeting if enabled
    if use_custom_greeting and greeting_text:
        logger.info(f"Adding custom greeting to TwiML: {greeting_text}")
        response.append(f'<Say>{greeting_text}</Say>')
    else:
        logger.info("No custom greeting added to TwiML")
    
    # Add MP3 playback
    response.append(f'<Play>{mp3_url}</Play>')
    response.append('<Pause length="1"/>')
    response.append('<Say>MP3 playback complete. Thank you for testing.</Say>')
    response.append('</Response>')
    
    twiml = '\n'.join(response)
    
    logger.info(f"Sending TwiML response: {twiml}")
    return Response(twiml, mimetype='text/xml')

@app.route('/status', methods=['POST'])
def status_callback():
    """Handle status updates from Twilio and broadcast them."""
    call_sid = request.values['CallSid']
    call_status = request.values['CallStatus']
    
    # Log all request values for debugging
    logger.info(f"Status callback received with values: {request.values}")
    logger.info(f"Status update for call {call_sid}: {call_status}")
    
    if call_sid in calls:
        calls[call_sid] = call_status
        socketio.emit('call_update', {'call_sid': call_sid, 'status': call_status})
    return '', 200

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
            footer { margin-top: 50px; padding: 20px 0; border-top: 1px solid #dee2e6; text-align: center; }
            footer a { color: #007bff; }
            footer a:hover { color: #0056b3; text-decoration: none; }
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
                footer { margin-top: 50px; padding: 20px 0; border-top: 1px solid #dee2e6; text-align: center; }
                footer a { color: #007bff; }
                footer a:hover { color: #0056b3; text-decoration: none; }
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

if __name__ == '__main__':
    # Print configuration for debugging
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Twilio Number: {twilio_number}")
    logger.info(f"MP3 Files: {mp3_files}")
    logger.info("Starting Flask application on port 5005")
    socketio.run(app, host='0.0.0.0', port=5005, debug=True)