# Implementation plan

## Phase 1: Environment Setup

1.  **Prevalidation**: Check if the current directory is already a Python project by verifying the presence of files like `requirements.txt` or a virtual environment folder. (Project Requirements)

2.  **Initialize Project Directory**: If not already a project, create a new directory structure for the project. (Project Requirements)

3.  **Create Virtual Environment**: In the project root, run `python3 -m venv venv` to initialize a virtual environment. (Tech Stack: Python)

4.  **Activate Virtual Environment**:

    *   On Linux/macOS: run `source venv/bin/activate`
    *   On Windows: run `venv\Scripts\activate` (Tech Stack: Python)

5.  **Install Required Libraries**: Install the necessary libraries using pip:

`pip install websockets pyaudio gpiozero `(Tech Stack: Libraries: websockets, pyaudio, gpiozero)

1.  **Create requirements.txt**: Freeze the installed libraries into a `requirements.txt` file by running `pip freeze > requirements.txt`. (Tech Stack: Python)
2.  **Validation**: Run `pip freeze` and verify that `websockets`, `pyaudio`, and `gpiozero` libraries are listed.

## Phase 2: Core Application Development

1.  **Create Main Application File**: Create a file named `voice_interaction.py` in the project root. (Project Requirements)
2.  **Import Modules**: In `voice_interaction.py`, import the required modules: `asyncio`, `websockets`, `pyaudio`, `gpiozero`, `json`, `time`, and `logging`. (Project Requirements)
3.  **Setup Logging**: Initialize logging to log session details and errors locally. Write logs to a file (e.g., `session.log`). (Project Requirements: Logging) Example code snippet:

`import logging logging.basicConfig(filename='session.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')`

1.  **Configure Audio Parameters**: Define constants for audio configuration. Set sample rate to 16000 Hz, sample format to 16-bit, and choose an appropriate buffer size for low latency (<200ms). (Project Requirements: Audio Quality) Example code snippet:

`AUDIO_RATE = 16000 AUDIO_FORMAT = pyaudio.paInt16 CHUNK_SIZE = 1024 # Adjust as needed to keep latency low`

1.  **Initialize PyAudio Instances**: Create separate PyAudio stream instances for input (microphone capture) and output (speaker playback). (Project Requirements: Audio Processing)
2.  **Setup GPIO for Button Input**: Use the gpiozero library to configure a physical button on GPIO pin 17 with a debouncing delay of 50ms. Example code snippet:

`from gpiozero import Button button = Button(17, bounce_time=0.05)`

(Project Requirements: Session Control, Button Debouncing)

1.  **Define JWT Token Retrieval**: Implement a method to retrieve the JWT token. For simplicity, assume the token is provided as an environment variable (`JWT_TOKEN`) or prompt the user to input it. (Project Requirements: JWT Token Authentication) Example code snippet:

`import os JWT_TOKEN = os.getenv('JWT_TOKEN') or input('Enter JWT Token: ')`

1.  **Implement WebSocket Connection Function**: Write an asynchronous function to establish and maintain a persistent WebSocket connection to `wss://sesameai.app/agent-service-0/v1/connect`. (Project Requirements: WebSocket Connection) Example code snippet:

`async def connect_websocket(): uri = 'wss://sesameai.app/agent-service-0/v1/connect' async with websockets.connect(uri) as ws: # Send JWT token for authentication await ws.send(json.dumps({'token': JWT_TOKEN})) logging.info('WebSocket connected and JWT sent') return ws`

1.  **Handle 'ping' Messages**: Within the WebSocket listener, parse incoming messages. If a message with `"type": "ping"` is received, optionally send a response if required by the protocol. (Project Requirements: 'ping' Messages)

2.  **Implement Exponential Backoff**: In the event that the WebSocket connection drops, implement reconnection logic using exponential backoff (e.g., delays of 1s, 2s, 4s, etc.). (Project Requirements: Error Handling)

3.  **Define Audio Capture Routine**: Create an asynchronous function that reads audio chunks from the microphone stream and sends them to the WebSocket server. (Project Requirements: Audio Processing, Full-Duplex Audio)

4.  **Define Audio Playback Routine**: Create an asynchronous function that listens for audio data from the WebSocket server and plays it through the speaker stream. (Project Requirements: Audio Processing, Full-Duplex Audio)

5.  **Implement Session Control Logic**:

    *   Monitor the physical button using gpiozero.
    *   On a short press, trigger the start of the voice session.
    *   On a press-and-hold (>=2 seconds), trigger session termination.

6.  (Project Requirements: Session Control, Safeguards)

7.  **Combine Audio Streaming Tasks**: In the main asynchronous function, use `asyncio.create_task` to run the audio capture and audio playback routines concurrently while managing the WebSocket connection. (Project Requirements: Full-Duplex Audio)

8.  **Validation**: Add log statements to confirm that pressing the button logs 'Session Started' and that a press-and-hold (>2 seconds) logs 'Session Terminated'.

## Phase 3: Integration

1.  **Integrate Components**: Combine the functions for WebSocket connection, audio capture, playback, and button monitoring into a single application flow within `voice_interaction.py`. (Project Requirements: App Structure/Flow)
2.  **Define Main Entry Point**: Use the `if __name__ == '__main__':` block to start the asyncio event loop and initiate the voice session control logic. (Project Requirements: Initialization) Example code snippet:

`if __name__ == '__main__': try: asyncio.run(main()) except Exception as e: logging.error(f'Fatal error: {e}')`

1.  **Validation**: Manually review the integration by simulating button presses to ensure that audio streaming starts and stops as expected.

## Phase 4: Testing & Debugging

1.  **Local Testing**: Run the application on a development machine (if possible) with simulated audio in/out to confirm basic functionality. (Project Requirements)
2.  **Hardware Validation**: Test the PyAudio input/output separately on the Raspberry Pi with simple scripts to validate microphone and speaker performance. (Project Requirements: Hardware Testing)
3.  **Simulate Button presses**: Write a temporary test routine if needed to simulate button press events and verify session control logic. (Project Requirements: Session Control)
4.  **Test WebSocket Connection**: Verify that the application successfully connects to `wss://sesameai.app/agent-service-0/v1/connect` and handles messages (including 'ping'). (Project Requirements: WebSocket Connection)
5.  **Logging Verification**: Check the log file `session.log` to confirm that session events and errors are being recorded correctly. (Project Requirements: Logging)

## Phase 5: Deployment

1.  **Transfer Code to Raspberry Pi**: Copy the complete project (including `voice_interaction.py`, `requirements.txt`, and any other necessary files) to the Raspberry Pi Zero 2 W. (Project Requirements: Deployment)
2.  **Hardware Setup Verification**: Ensure the Raspberry Pi is connected to the microphone, speakers, and physical button wired to GPIO pin 17. (Project Requirements: Hardware)
3.  **Install Dependencies on Raspberry Pi**: On the Raspberry Pi, create a virtual environment, activate it, and install dependencies from `requirements.txt`.
4.  **Run the Application**: Execute `python voice_interaction.py` on the Raspberry Pi and monitor the console and `session.log` for issues. (Project Requirements)
5.  **Validation**: Confirm that a short button press successfully starts the WebSocket connection and audio streaming and that a press-and-hold (>=2 seconds) terminates the session.

## Phase 6: Production Readiness

1.  **Setup Auto-Start with systemd**: Create a systemd service file to run the application on boot. (Deployment)
2.  **Create systemd Service File**: Create a file at `/etc/systemd/system/voice_interaction.service` with the following content:

`[Unit] Description=Voice Interaction Service After=network.target [Service] ExecStart=/path/to/venv/bin/python /path/to/voice_interaction.py WorkingDirectory=/path/to/project StandardOutput=inherit StandardError=inherit Restart=always [Install] WantedBy=multi-user.target`

1.  **Enable and Start Service**: Run `sudo systemctl enable voice_interaction` and `sudo systemctl start voice_interaction`. (Deployment)
2.  **Validation**: Verify that the service is running using `sudo systemctl status voice_interaction` and check the logs for any startup issues.

## Phase 7: Documentation and Final Validation

1.  **Create README.md**: Write a README document explaining the project setup, hardware wiring instructions (including physical button on GPIO 17), dependency installation, and how to run and test the application. (Documentation)
2.  **Code Review and Commit**: Review all code and commit the changes to version control, ensuring that proper documentation exists. (Best Practices)
3.  **Final System Check**: Perform an end-to-end test on the Raspberry Pi to simulate a full voice session including JWT token authentication, audio capture/playback, WebSocket communication, and proper session termination. (Project Requirements)

This implementation plan outlines a clear, step-by-step process for developing the voice interaction system on the Raspberry Pi as per the provided project requirements and tech stack.
