import asyncio
import json
import logging
import os
import sys
import platform
import base64
import secrets
import time
from datetime import datetime
from functools import partial
import pyaudio
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import threading

# Platform-specific imports
IS_MACOS = platform.system() == 'Darwin'
if IS_MACOS:
    from pynput import keyboard
else:
    from gpiozero import Button
    import select
    import termios
    import tty

# Custom logging formatter for Raspberry Pi that ensures proper line endings in raw terminal mode
class RaspberryPiFormatter(logging.Formatter):
    def format(self, record):
        # Format the message
        msg = super().format(record)
        # Ensure proper line ending that works in raw terminal mode
        return f'\r{msg}\n'

# Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
#     datefmt='%M:%S',
#     handlers=[
#         logging.FileHandler('session.log'),
#         logging.StreamHandler()  # This will print to console
#     ]
# )

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Create the basic formatter for macOS
basic_formatter = logging.Formatter(
    fmt='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
    datefmt='%M:%S'
)

# Create the Raspberry Pi formatter for raw terminal mode
pi_formatter = RaspberryPiFormatter(
    fmt='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
    datefmt='%M:%S'
)

# Use the appropriate formatter based on platform
formatter = pi_formatter if not IS_MACOS else basic_formatter

# Set up handlers with the platform-specific formatter
file_handler = logging.FileHandler('session.log')
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# Load configuration from environment variables
AUDIO_RATE = int(os.getenv('AUDIO_RATE', '16000'))
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1024'))
CLIENT_NAME = os.getenv('CLIENT_NAME', 'RP-Web')  # Changed from 'Sesame-Pi' to match working request
CLIENT_TIMEZONE = os.getenv('CLIENT_TIMEZONE', 'America/New_York')

# WebSocket configuration
WS_URI = 'wss://sesameai.app/agent-service-0/v1/connect'

class WebSocketMessage:
    def __init__(self, msg_type, session_id=None, call_id=None, request_id=None, content=None):
        self.type = msg_type
        self.session_id = session_id
        self.call_id = call_id
        self.request_id = request_id
        self.content = content

    def to_dict(self):
        msg = {
            'type': self.type,
            'session_id': self.session_id
        }
        if self.call_id is not None:
            msg['call_id'] = self.call_id
        if self.request_id is not None:
            msg['request_id'] = self.request_id
        if self.content is not None:
            msg['content'] = self.content
        return msg

    @classmethod
    def from_dict(cls, data):
        return cls(
            msg_type=data['type'],
            session_id=data.get('session_id'),
            call_id=data.get('call_id'),
            request_id=data.get('request_id'),
            content=data.get('content')
        )

class VoiceInteractionSession:
    def __init__(self, button_pin=17):
        # Audio setup
        self.audio = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
        self.audio_format = pyaudio.paFloat32
        self.channels = 1
        self.frames_per_buffer = 637  # DO NOT CHANGE Calculated to achieve ~1822 byte messages after JSON+base64 encoding
        # Session state
        self.session_id = None
        self.call_id = None
        self.sample_rate = None
        self.press_time = None
        self.loop = asyncio.get_event_loop()
        self.session_active = False  # Track if a session is currently active
        self.ping_received = False  # Track if we've received a ping response
        self.first_audio_sent = False  # Track if we've sent the first audio message
        # Shutdown coordination
        self.shutting_down = False  # Flag to indicate we're in shutdown mode
        self.disconnect_event = None  # Event to signal when disconnect response is received
        self.pending_disconnect_id = None  # Track the request_id of a pending disconnect
        
        # Initialize keyboard handler for macOS
        if IS_MACOS:
            self.keyboard_listener = keyboard.Listener(
                on_press=self._handle_key_press,
                on_release=self._handle_key_release
            )
            self.keyboard_listener.start()
            logging.info('Initialized keyboard handler for macOS (using spacebar, press Q to quit)')
            
        # Initialize GPIO button for Raspberry Pi
        if not IS_MACOS:
            try:
                self.button = Button(button_pin, bounce_time=0.05)
                self.button.when_pressed = self._handle_button_press
                self.button.when_released = self._handle_button_release
                logging.info(f'Initialized GPIO button on pin {button_pin}')
            except Exception as e:
                self.button = None
                logging.warning(f'Failed to initialize GPIO button: {e}. Continuing with keyboard input only.')
        
        # WebSocket and session state
        self.jwt_token = os.getenv('JWT_TOKEN')
        if not self.jwt_token:
            raise ValueError("JWT_TOKEN environment variable not set")
        self.websocket = None
        self.reconnect_delay = 1  # Initial reconnect delay in seconds
        
        # Thread control
        self.running = True  # Controls keyboard thread

    async def connect_websocket(self):
        """Establish WebSocket connection with exponential backoff"""
        import ssl
        import websockets
        import jwt
        from urllib.parse import urlencode
        
        # Log websockets version for debugging
        logging.info(f"Using websockets version: {websockets.__version__}")

        # Validate JWT token format and expiry
        try:
            # Just decode without verification to check format and expiry
            token_data = jwt.decode(self.jwt_token, options={"verify_signature": False})
            logging.info('JWT token format is valid')
            # Log expiry time
            if 'exp' in token_data:
                expiry = datetime.fromtimestamp(token_data['exp'])
                now = datetime.now()
                logging.info(f'Token expires at: {expiry} (in {expiry - now} seconds)')
                if expiry <= now:
                    logging.error('Token has expired!')
                    return
        except jwt.InvalidTokenError as e:
            logging.error(f'Invalid JWT token format: {e}')
            return

        # Temporarily disable SSL verification for testing
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        logging.info('SSL verification temporarily disabled for testing')

        # Prepare query parameters (including id_token)
        params = {
            'id_token': self.jwt_token,
            'client_name': CLIENT_NAME,
            'usercontext': json.dumps({'timezone': CLIENT_TIMEZONE}),
            'character': 'Miles'
        }
        ws_uri_with_params = f"{WS_URI}?{urlencode(params)}"

        while True:
            try:
                logging.info('Attempting WebSocket connection...')
                # Generate a random WebSocket key (16 random bytes, base64 encoded)
                websocket_key = base64.b64encode(secrets.token_bytes(16)).decode()
                
                async with websockets.connect(
                    ws_uri_with_params,
                    ssl=ssl_context,
                    additional_headers={
                        'Connection': 'Upgrade', 
                        'Upgrade': 'websocket',
                        'sec-websocket-key': websocket_key,
                        'sec-websocket-version': '13',
                        'sec-websocket-extensions': 'permessage-deflate; client_max_window_bits'
                    }
                ) as ws:
                    logging.info('WebSocket connection established successfully')
                    self.websocket = ws
                    await self.handle_messages()

            except websockets.exceptions.WebSocketException as e:
                if "401" in str(e) or "403" in str(e):
                    logging.error(f'Authentication failed: {e}')
                    logging.error('Full error details:')
                    for line in str(e).split('\n'):
                        logging.error(f'  {line}')
                    # Don't retry on auth failure
                    return
                else:
                    logging.error(f'WebSocket error: {e}')

            except ssl.SSLCertVerificationError as e:
                logging.error(f'SSL Certificate verification failed: {e}')
                logging.error('This might be due to an invalid or self-signed certificate.')
                logging.error('If you trust this server, you can try to obtain its certificate or temporarily disable verification.')

            except OSError as e:
                if e.errno == 49:  # Can't assign requested address
                    logging.error(f"Connection address binding error: {e}")
                    # Try a different approach - this often happens when network interface changes
                    import socket
                    # Log network interfaces for debugging
                    try:
                        hostname = socket.gethostname()
                        local_ip = socket.gethostbyname(hostname)
                        logging.info(f"Local hostname: {hostname}, IP: {local_ip}")
                    except Exception as net_err:
                        logging.error(f"Failed to get network info: {net_err}")
                    
                    # Wait a bit longer before retry when hitting address errors
                    await asyncio.sleep(5)
                else:
                    logging.error(f'OSError: {e}')
            except Exception as e:
                logging.error(f'Unexpected error: {type(e).__name__}: {e}')

            if not self.running:
                break

            logging.info(f'Reconnecting in {self.reconnect_delay} seconds...')
            await asyncio.sleep(self.reconnect_delay)
            self.reconnect_delay = min(self.reconnect_delay * 2, 60)  # Max delay of 60 seconds

    async def send_message(self, message):
        """Send a WebSocket message"""
        try:
            msg_dict = message.to_dict()
            msg_json = json.dumps(msg_dict)
            msg_length = len(msg_json)
            logging.info(f'Sending message type: {message.type}, length: {msg_length} bytes')
            await self.websocket.send(msg_json)
        except Exception as e:
            logging.error(f'Error sending message: {e}')

    async def handle_initialize(self, message):
        """Handle initialization message"""
        self.session_id = message.content['session_id']
        logging.info(f'Session initialized with ID: {self.session_id}')

        # Send client location state
        location_msg = WebSocketMessage(
            'client_location_state',
            session_id=self.session_id,
            content={
                'latitude': 0,
                'longitude': 0,
                'address': '',
                'timezone': CLIENT_TIMEZONE
            }
        )
        await self.send_message(location_msg)

        # Send call connect
        import uuid
        call_msg = WebSocketMessage(
            'call_connect',
            session_id=self.session_id,
            request_id=str(uuid.uuid4()),
            content={
                'sample_rate': 24000,  # Match server's expected rate
                'audio_codec': 'none',
                'reconnect': False,
                'is_private': False,
                'settings': {
                    'preset': 'Miles'
                },
                'client_name': CLIENT_NAME,
                'client_metadata': {}
            }
        )
        await self.send_message(call_msg)

    async def handle_call_connect_response(self, message):
        """Handle call connect response"""
        self.call_id = message.call_id
        self.sample_rate = message.content['sample_rate']
        logging.info(f'Call connected with ID: {self.call_id}, sample rate: {self.sample_rate}')
        # Send initial ping
        await self.send_ping()

    async def handle_ping_response(self, message):
        """Handle ping response message"""
        self.ping_received = True
        logging.info('Received ping response - now accepting audio input')
        
    async def handle_chat(self, message):
        """Handle chat message"""
        # logging.info(f'Chat message received')

    async def send_ping(self):
        """Send ping message"""
        import uuid
        ping_msg = WebSocketMessage(
            'ping',
            session_id=self.session_id,
            call_id=self.call_id,
            request_id=str(uuid.uuid4()),
            content='ping'
        )
        logging.info('Sending ping message')
        await self.send_message(ping_msg)

    async def handle_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            while self.running:
                try:
                    message = await self.websocket.recv()
                    msg_length = len(message)
                    
                    try:
                        data = json.loads(message)
                        
                        # Check for disconnect response during shutdown
                        if self.shutting_down and self.pending_disconnect_id and \
                           data.get('type') == 'call_disconnect_response' and \
                           data.get('request_id') == self.pending_disconnect_id:
                            logging.info('Received call_disconnect_response during shutdown')
                            if self.disconnect_event:
                                self.disconnect_event.set()
                            continue
                        
                        if not self.shutting_down:
                            msg = WebSocketMessage.from_dict(data)
                            msg_type = msg.type
                            
                            # Log all message types and lengths, including audio
                            logging.info(f'Received message type: {msg_type}, length: {msg_length} bytes')
                            if not self.shutting_down and msg_type != 'audio':
                                logging.debug(f'Raw message: {message[:200]}...' if len(message) > 200 else f'Raw message: {message}')

                            if msg_type == 'initialize':
                                await self.handle_initialize(msg)
                            elif msg_type == 'call_connect_response':
                                await self.handle_call_connect_response(msg)
                            elif msg_type == 'ping_response':
                                await self.handle_ping_response(msg)
                            elif msg_type == 'audio':
                                # Process audio without excessive logging
                                await self._handle_audio_message(msg)
                            elif msg_type == 'chat':
                                await self.handle_chat(msg)
                            else:
                                logging.info(f'Unknown message type: {msg_type}')
                                # Log the full message for unknown types
                                logging.info(f'Full message: {json.dumps(data, indent=2)}')

                    except json.JSONDecodeError:
                        if not self.shutting_down:
                            logging.warning(f'Received invalid JSON message: {message[:200]}...' if len(message) > 200 else f'Received invalid JSON message: {message}')
                    except Exception as e:
                        if not self.shutting_down:
                            logging.error(f'Error processing message: {e}')
                            logging.error(f'Message content: {message[:200]}...' if len(message) > 200 else f'Message content: {message}')
                
                except websockets.exceptions.ConnectionClosedOK:
                    # Normal closure during shutdown
                    if self.shutting_down:
                        logging.info('WebSocket closed normally during shutdown')
                        break
                    else:
                        raise  # Re-raise if not shutting down
                
                except Exception as e:
                    if not self.shutting_down:
                        raise  # Re-raise if not shutting down
                    else:
                        # During shutdown, just log and break
                        logging.info(f'WebSocket error during shutdown: {e}')
                        break

        except Exception as e:
            if not self.shutting_down:
                logging.error(f'Error in message handling loop: {e}')
                if self.running:
                    # Attempt to reconnect if this wasn't a clean shutdown
                    self.websocket = None
                    await self.connect_websocket()

    async def authenticate(self):
        """Send JWT authentication message"""
        auth_message = json.dumps({'token': self.jwt_token})
        await self.websocket.send(auth_message)

    # This is a duplicate method, removing it as it conflicts with the first handle_messages method

    # This method is already defined properly above as handle_ping_response(self, message)

    def _setup_audio_streams(self):
        """Initialize audio input and output streams"""
        if self.input_stream or self.output_stream:
            self._cleanup_audio_streams()

        # Use server's sample rate (24000) for both input and output
        input_rate = 24000  # Hardcoded to match server's expected rate
        output_rate = self.sample_rate if self.sample_rate else input_rate
        
        # Log available audio devices for debugging
        logging.info("=== Available Audio Devices ===")
        default_input_device_info = self.audio.get_default_input_device_info()
        default_input_device_index = default_input_device_info['index']
        
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            is_input = device_info['maxInputChannels'] > 0
            is_default = " (DEFAULT)" if i == default_input_device_index and is_input else ""
            
            if is_input:
                logging.info(f"Input Device {i}: {device_info['name']}{is_default}")
                logging.info(f"  Sample Rate: {int(device_info['defaultSampleRate'])}")
                logging.info(f"  Channels: {device_info['maxInputChannels']}")
        
        logging.info(f"\nUsing default input device: {default_input_device_info['name']} (index {default_input_device_index})")

        # Input stream for microphone
        self.input_stream = self.audio.open(
            rate=input_rate,
            channels=self.channels,
            format=self.audio_format,
            input=True,
            frames_per_buffer=self.frames_per_buffer,
            stream_callback=self._audio_input_callback
        )

        # Output stream for speakers
        self.output_stream = self.audio.open(
            rate=output_rate,
            channels=self.channels,
            format=self.audio_format,
            output=True,
            frames_per_buffer=self.frames_per_buffer
        )

        logging.info(f'Audio streams initialized (input rate: {input_rate}, output rate: {output_rate})')

    def _cleanup_audio_streams(self):
        """Clean up audio streams"""
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
            self.input_stream = None

        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
            self.output_stream = None

    def _audio_input_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio input stream"""
        if not self.running:
            logging.debug('Audio callback called but self.running is False')
            return (in_data, pyaudio.paContinue)
            
        if not self.websocket:
            logging.debug('Audio callback called but websocket is not connected')
            return (in_data, pyaudio.paContinue)
            
        if not self.ping_received:
            logging.debug('Audio callback called but ping response not yet received')
            return (in_data, pyaudio.paContinue)

        # Convert audio data to base64
        try:
            # Convert bytes to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            
            # Calculate audio metrics for debugging
            rms = np.sqrt(np.mean(np.square(audio_data)))
            peak = np.max(np.abs(audio_data))
            is_silent = rms < 0.01  # Adjust this threshold as needed
            
            # Only log non-silent audio to reduce log volume
            if not is_silent:
                logging.info(f'Input audio metrics - RMS: {rms:.6f}, Peak: {peak:.6f}, SOUND DETECTED')
            
            # Convert to int16 format (required by the server)
            audio_data = (audio_data * 32767).astype(np.int16)
            # Convert to base64
            audio_base64 = base64.b64encode(audio_data.tobytes()).decode('utf-8')

            # Create audio message
            audio_msg = WebSocketMessage(
                'audio',
                session_id=self.session_id,
                call_id=self.call_id,
                content={
                    'audio_data': audio_base64
                }
            )

            # Log the first audio message's complete contents
            # if not self.first_audio_sent:
            #     msg_dict = audio_msg.to_dict()
            #     logging.info(f'First audio message complete contents: {json.dumps(msg_dict, indent=2)}')
            #     self.first_audio_sent = True

            # Send audio data asynchronously using the event loop in a thread-safe way
            self.loop.call_soon_threadsafe(
                lambda msg=audio_msg: self.loop.create_task(self.send_message(msg))
            )

        except Exception as e:
            logging.error(f'Error processing input audio: {e}')
            import traceback
            logging.error(f'Traceback: {traceback.format_exc()}')

        return (in_data, pyaudio.paContinue)

    async def _handle_audio_message(self, message):
        """Handle incoming audio message"""
        try:
            if not self.output_stream:
                logging.error('Output stream is not initialized')
                return
                
            # Log receipt of audio message with timestamp
            current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            logging.info(f'(incoming) Processing audio message at {current_time}')
                
            # Decode base64 audio data
            audio_data = base64.b64decode(message.content['audio_data'])
            logging.info(f'(incoming) Decoded audio data length: {len(audio_data)} bytes')
            
            # Convert to int16 numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Calculate audio metrics for debugging
            rms = np.sqrt(np.mean(np.square(audio_array.astype(np.float32) / 32767)))
            peak = np.max(np.abs(audio_array.astype(np.float32) / 32767))
            is_silent = rms < 0.01
            
            # Log audio metrics for all audio messages
            if is_silent:
                logging.info(f'(incoming) Output audio metrics - RMS: {rms:.6f}, Peak: {peak:.6f}, SILENT')
            else:
                logging.info(f'(incoming) Output audio metrics - RMS: {rms:.6f}, Peak: {peak:.6f}, SOUND DETECTED')
            
            # Convert to float32 for PyAudio
            audio_float = (audio_array / 32767).astype(np.float32)
            
            # Play audio
            bytes_data = audio_float.tobytes()
            logging.info(f'(incoming) Writing {len(bytes_data)} bytes to audio output stream')
            self.output_stream.write(bytes_data)
            
            # Removed the 0.1s delay that was causing pauses between audio chunks
            
            logging.info('(incoming) Audio message processing completed')
            
        except Exception as e:
            logging.error(f'Error processing output audio: {e}')
            import traceback
            logging.error(f'Traceback: {traceback.format_exc()}')

    async def start_session(self):
        """Start a new voice interaction session"""
        self.running = True
        self.session_active = True  # Set session as active
        self.ping_received = False  # Reset ping status for new session
        self.first_audio_sent = False  # Reset first audio message flag
        logging.info('Session Started')
        self._setup_audio_streams()
        
        # Ensure proper network initialization before connecting
        # Use asyncio.sleep instead of time.sleep to avoid blocking the event loop
        await asyncio.sleep(1)  # Brief pause to ensure system network is ready
        
        # Attempt to connect to websocket
        await self.connect_websocket()

    async def disconnect_call(self):
        """Send a call_disconnect message and wait for the response"""
        if not self.session_id or not self.call_id or not self.websocket:
            logging.info('No active call to disconnect')
            return
            
        import uuid
        request_id = str(uuid.uuid4())
        self.pending_disconnect_id = request_id
        
        # Create an event to wait for the disconnect response
        self.disconnect_event = asyncio.Event()
        
        # Send call_disconnect message
        disconnect_msg = WebSocketMessage(
            'call_disconnect',
            session_id=self.session_id,
            call_id=self.call_id,
            request_id=request_id,
            content={
                'reason': 'user_request'
            }
        )
        
        logging.info('Sending call_disconnect message')
        try:
            await self.send_message(disconnect_msg)
            
            # Wait for disconnect response with timeout
            try:
                await asyncio.wait_for(self.disconnect_event.wait(), timeout=3.0)
                logging.info('Disconnect complete')
            except asyncio.TimeoutError:
                logging.warning('Timed out waiting for call_disconnect_response')
        except Exception as e:
            if not self.shutting_down:
                logging.error(f'Error in disconnect process: {e}')
        finally:
            # Clean up
            self.disconnect_event = None
            self.pending_disconnect_id = None

    async def stop_session(self):
        """Stop the current voice interaction session"""
        self.running = False
        self.session_active = False  # Set session as inactive
        self.shutting_down = True  # Set shutdown flag
        
        # First disconnect the call if active and wait for it to complete
        if self.session_id and self.call_id and self.websocket:
            try:
                await self.disconnect_call()
                # Add a small delay to ensure any pending messages are processed
                await asyncio.sleep(0.2)
            except Exception as e:
                logging.info(f'Non-critical error during call disconnect: {e}')
        
        # Then close the websocket
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logging.info(f'Non-critical error closing websocket: {e}')
            
        # Clean up audio resources
        self._cleanup_audio_streams()
        logging.info('Session Terminated')

    def _handle_input_press(self):
        """Handle input press event (button or keyboard)"""
        self.press_time = datetime.now()
        logging.info('Input pressed')

    def _handle_input_release(self):
        """Handle input release event and determine if it was a short or long press"""
        if not self.press_time:
            return

        release_time = datetime.now()
        press_duration = (release_time - self.press_time).total_seconds()
        self.press_time = None

        if press_duration >= 2.0:
            # Long press (>= 2 seconds) - stop session
            if self.session_active:
                logging.info('Long press detected - stopping session')
                self.loop.call_soon_threadsafe(lambda: self.loop.create_task(self.stop_session()))
        else:
            # Short press - start session only if not already active
            if not self.session_active:
                logging.info('Short press detected - starting session')
                self.loop.call_soon_threadsafe(lambda: self.loop.create_task(self.start_session()))
            else:
                logging.info('Session already active, ignoring short press')

    def _handle_button_press(self):
        """Handle Raspberry Pi GPIO button press"""
        self._handle_input_press()

    def _handle_button_release(self):
        """Handle Raspberry Pi GPIO button release"""
        self._handle_input_release()

    def _handle_key_press(self, key):
        """Handle macOS keyboard press"""
        if key == keyboard.Key.space:
            self._handle_input_press()
        elif hasattr(key, 'char') and key.char == 'q':
            logging.info('Q key pressed - terminating application')
            
            # Prevent multiple shutdown attempts
            if self.shutting_down:
                return
                
            # Create a graceful shutdown sequence
            async def shutdown_sequence():
                try:
                    # Stop the session (which will disconnect the call)
                    await self.stop_session()
                    
                    # Add a small delay to ensure session is fully stopped
                    await asyncio.sleep(0.5)
                    
                    # Cancel all other tasks
                    for task in asyncio.all_tasks(self.loop):
                        if task is not asyncio.current_task():
                            task.cancel()
                    
                    # Allow a moment for tasks to clean up
                    await asyncio.sleep(0.5)
                    
                    # Stop the loop
                    self.loop.stop()
                except Exception as e:
                    logging.info(f'Non-critical error in shutdown sequence: {e}')
                    # Ensure the loop stops even if there's an error
                    self.loop.stop()
            
            # Schedule the shutdown sequence
            self.loop.call_soon_threadsafe(
                lambda: self.loop.create_task(shutdown_sequence())
            )

    def _handle_key_release(self, key):
        """Handle macOS keyboard release"""
        if key == keyboard.Key.space:
            self._handle_input_release()

    def _stdin_keyboard_thread(self):
        """Background thread for keyboard input on Raspberry Pi"""
        try:
            logging.info('Keyboard thread started')
            while self.running:
                if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                    char = sys.stdin.read(1)
                    if char == ' ':
                        logging.info('Spacebar pressed')
                        self._handle_input_press()
                        self._handle_input_release()
                    elif char.lower() == 'q':
                        logging.info('Q pressed - stopping...')
                        self.running = False
                        break
        except Exception as e:
            logging.error(f'Error in keyboard thread: {e}')
        finally:
            logging.info('Keyboard thread stopping - restoring terminal settings')
            if hasattr(self, 'old_terminal_settings'):
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_terminal_settings)

    async def _handle_space_press(self):
        """Handle spacebar press in the main event loop"""
        self._handle_input_press()
        await asyncio.sleep(0.1)  # Small delay to prevent double-triggers
        self._handle_input_release()

    async def _handle_q_press(self):
        """Handle Q press in the main event loop"""
        await self.stop_session()
        self.running = False
        self.loop.stop()

async def main():
    """Main entry point for the voice interaction application"""
    try:
        global session
        session = VoiceInteractionSession(button_pin=17)
        
        # Initialize keyboard input for Raspberry Pi after event loop is running
        if not IS_MACOS:
            session.old_terminal_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
            session.keyboard_thread = threading.Thread(target=session._stdin_keyboard_thread)
            session.keyboard_thread.daemon = True
            session.keyboard_thread.start()
            logging.info('Initialized keyboard handler for Raspberry Pi (using spacebar, press Q to quit)')
        
        input_type = 'spacebar (press Q to quit)' + (' or GPIO button' if not IS_MACOS else '')
        logging.info(f'Voice Interaction Service started. Waiting for {input_type} press...')
        
        # Keep the application running until interrupted
        try:
            # Both macOS and Raspberry Pi use background threads now
            await asyncio.get_event_loop().create_future()
        except asyncio.CancelledError:
            logging.info('Main task cancelled')
            
    except Exception as e:
        logging.error(f'Fatal error: {e}')
        raise

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Application terminated by user')
    except Exception as e:
        # Filter out expected shutdown-related errors
        expected_errors = [
            "Event loop stopped before Future completed",
            "Task was destroyed but it is pending",
            "asyncio.run() cannot be called from a running event loop"
        ]
        
        if not any(expected_error in str(e) for expected_error in expected_errors):
            logging.error(f'Application error: {e}')
    finally:
        # Clean up PyAudio
        try:
            session = VoiceInteractionSession()
            session.audio.terminate()
        except Exception:
            pass
