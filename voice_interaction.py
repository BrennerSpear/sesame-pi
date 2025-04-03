import asyncio
import json
import logging
import os
import sys
import platform
import base64
from datetime import datetime
from functools import partial
import pyaudio
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Platform-specific imports
IS_MACOS = platform.system() == 'Darwin'
if IS_MACOS:
    from pynput import keyboard
else:
    from gpiozero import Button

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('session.log'),
        logging.StreamHandler()  # This will print to console
    ]
)

# Load configuration from environment variables
AUDIO_RATE = int(os.getenv('AUDIO_RATE', '16000'))
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1024'))
CLIENT_NAME = os.getenv('CLIENT_NAME', 'Sesame-Pi')
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
        self.frames_per_buffer = 1024
        # Session state
        self.session_id = None
        self.call_id = None
        self.sample_rate = None
        self.press_time = None
        self.loop = asyncio.get_event_loop()
        
        if IS_MACOS:
            # Setup keyboard handler for macOS
            self.keyboard_listener = keyboard.Listener(
                on_press=lambda key: self._handle_keyboard_press(None) if key == keyboard.Key.space else None,
                on_release=lambda key: self._handle_keyboard_release(None) if key == keyboard.Key.space else None
            )
            self.keyboard_listener.start()
            logging.info('Initialized keyboard handler for macOS (using spacebar)')
        else:
            # Initialize GPIO button for Raspberry Pi
            self.button = Button(button_pin, bounce_time=0.05)
            self.button.when_pressed = self._handle_button_press
            self.button.when_released = self._handle_button_release
            logging.info(f'Initialized GPIO button on pin {button_pin}')
        self.jwt_token = os.getenv('JWT_TOKEN')
        if not self.jwt_token:
            raise ValueError("JWT_TOKEN environment variable not set")
        
        self.running = False
        self.websocket = None
        self.reconnect_delay = 1  # Initial reconnect delay in seconds

    async def connect_websocket(self):
        """Establish WebSocket connection with exponential backoff"""
        import ssl
        import websockets
        import jwt
        from urllib.parse import urlencode

        # Validate JWT token format first
        try:
            # Just decode without verification to check format
            jwt.decode(self.jwt_token, options={"verify_signature": False})
            logging.info('JWT token format is valid')
        except jwt.InvalidTokenError as e:
            logging.error(f'Invalid JWT token format: {e}')
            return

        # Setup SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Prepare query parameters
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
                async with websockets.connect(
                    ws_uri_with_params,
                    ssl=ssl_context
                ) as ws:
                    logging.info('WebSocket connection established successfully')
                    self.websocket = ws
                    await self.handle_messages()

            except websockets.exceptions.WebSocketException as e:
                if "401" in str(e) or "403" in str(e):
                    logging.error('Authentication failed: Invalid or expired JWT token')
                    # Don't retry on auth failure
                    return
                else:
                    logging.error(f'WebSocket error: {e}')

            except ssl.SSLCertVerificationError as e:
                logging.error(f'SSL Certificate verification failed: {e}')

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
            await self.websocket.send(json.dumps(message.to_dict()))
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
                'sample_rate': AUDIO_RATE,
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

    async def handle_ping(self, message):
        """Handle ping message"""
        response = WebSocketMessage(
            'ping_response',
            session_id=self.session_id,
            request_id=message.request_id,
            content='ping'
        )
        await self.send_message(response)

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
        await self.send_message(ping_msg)

    async def handle_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            while self.running:
                message = await self.websocket.recv()
                try:
                    data = json.loads(message)
                    msg = WebSocketMessage.from_dict(data)

                    if msg.type == 'initialize':
                        await self.handle_initialize(msg)
                    elif msg.type == 'call_connect_response':
                        await self.handle_call_connect_response(msg)
                    elif msg.type == 'ping':
                        await self.handle_ping(msg)
                    elif msg.type == 'audio':
                        await self._handle_audio_message(msg)
                    else:
                        logging.debug(f'Received message of type: {msg.type}')

                except json.JSONDecodeError:
                    logging.warning('Received invalid JSON message')
                except Exception as e:
                    logging.error(f'Error processing message: {e}')

        except Exception as e:
            logging.error(f'Error in message handling loop: {e}')
            if self.running:
                # Attempt to reconnect if this wasn't a clean shutdown
                self.websocket = None
                await self.connect_websocket()

    async def authenticate(self):
        """Send JWT authentication message"""
        auth_message = json.dumps({'token': self.jwt_token})
        await self.websocket.send(auth_message)

    async def handle_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            while self.running:
                message = await self.websocket.recv()
                try:
                    data = json.loads(message)
                    if data.get('type') == 'ping':
                        await self.handle_ping()
                except json.JSONDecodeError:
                    logging.warning('Received invalid JSON message')
        except Exception as e:
            logging.error(f'Error handling messages: {e}')

    async def handle_ping(self):
        """Handle ping messages from the server"""
        try:
            await self.websocket.send(json.dumps({'type': 'pong'}))
        except Exception as e:
            logging.error(f'Error sending pong: {e}')

    def _setup_audio_streams(self):
        """Initialize audio input and output streams"""
        if self.input_stream or self.output_stream:
            self._cleanup_audio_streams()

        # Input stream for microphone
        self.input_stream = self.audio.open(
            rate=AUDIO_RATE,
            channels=self.channels,
            format=self.audio_format,
            input=True,
            frames_per_buffer=self.frames_per_buffer,
            stream_callback=self._audio_input_callback
        )

        # Output stream for speakers
        self.output_stream = self.audio.open(
            rate=AUDIO_RATE,
            channels=self.channels,
            format=self.audio_format,
            output=True,
            frames_per_buffer=self.frames_per_buffer
        )

        logging.info('Audio streams initialized')

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
        if self.running and self.websocket:
            # Convert audio data to base64
            try:
                # Convert bytes to numpy array
                audio_data = np.frombuffer(in_data, dtype=np.float32)
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
                        'audio_data': audio_base64,
                        'timestamp_epoch_ms': int(datetime.now().timestamp() * 1000)
                    }
                )

                # Send audio data asynchronously
                asyncio.create_task(self.send_message(audio_msg))

            except Exception as e:
                logging.error(f'Error processing input audio: {e}')

        return (in_data, pyaudio.paContinue)

    async def _handle_audio_message(self, message):
        """Handle incoming audio message"""
        try:
            # Decode base64 audio data
            audio_data = base64.b64decode(message.content['audio_data'])
            # Convert to int16 numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            # Convert to float32 for PyAudio
            audio_float = (audio_array / 32767).astype(np.float32)
            # Play audio
            self.output_stream.write(audio_float.tobytes())
        except Exception as e:
            logging.error(f'Error processing output audio: {e}')

    async def start_session(self):
        """Start a new voice interaction session"""
        self.running = True
        logging.info('Session Started')
        self._setup_audio_streams()
        await self.connect_websocket()

    async def stop_session(self):
        """Stop the current voice interaction session"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
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
            logging.info('Long press detected - stopping session')
            self.loop.call_soon_threadsafe(lambda: self.loop.create_task(self.stop_session()))
        else:
            # Short press - start session
            logging.info('Short press detected - starting session')
            self.loop.call_soon_threadsafe(lambda: self.loop.create_task(self.start_session()))

    def _handle_button_press(self):
        """Handle Raspberry Pi GPIO button press"""
        self._handle_input_press()

    def _handle_button_release(self):
        """Handle Raspberry Pi GPIO button release"""
        self._handle_input_release()

    def _handle_keyboard_press(self, event):
        """Handle macOS keyboard press"""
        self._handle_input_press()

    def _handle_keyboard_release(self, event):
        """Handle macOS keyboard release"""
        self._handle_input_release()

async def main():
    """Main entry point for the voice interaction application"""
    try:
        session = VoiceInteractionSession(button_pin=17)
        input_type = 'spacebar' if IS_MACOS else 'GPIO button'
        logging.info(f'Voice Interaction Service started. Waiting for {input_type} press...')
        
        # Keep the application running until interrupted
        await asyncio.Future()  # Run forever until interrupted
            
    except Exception as e:
        logging.error(f'Fatal error: {e}')
        raise

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Application terminated by user')
    except Exception as e:
        logging.error(f'Application error: {e}')
    finally:
        # Clean up PyAudio
        try:
            session = VoiceInteractionSession()
            session.audio.terminate()
        except Exception:
            pass
