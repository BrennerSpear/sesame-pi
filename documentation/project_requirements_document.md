# Project Requirements Document (PRD)

## 1. Project Overview

This project is about building a Python script that runs on a Raspberry Pi and acts as an interface between a physical hardware setup (a button, microphone, and speakers) and a third-party voice interaction server via WebSockets. The script will replicate and integrate with the Sesame AI web service demo so that whenever a user presses a physical button, a voice session starts, capturing the user's audio and transmitting it to the remote server while any audio reply is played back through the speakers. The core problem addressed is combining hardware inputs with real-time, full-duplex audio streaming over a secure, persistent connection.

The project is being built to enable natural voice interactions on a compact hardware platform (Raspberry Pi Zero 2 W), with the intention of testing and refining the voice interaction system cost-effectively. Key success criteria include having a reliable and low latency (under 200 ms) full-duplex audio connection, robust error handling with automatic reconnection, and a clear session control mechanism using a physical button (including safeguards to avoid accidental session termination). The initiative is exploratory and may later evolve to use a more powerful Raspberry Pi model if performance limitations emerge.

## 2. In-Scope vs. Out-of-Scope

### In-Scope

*   Establishing a persistent WebSocket connection to the server at "wss://sesameai.app/agent-service-0/v1/connect".
*   Capturing audio from a connected microphone with optimized settings (sample rate of 16 kHz and 16-bit depth).
*   Playing incoming audio responses from the server through connected speakers.
*   Implementing a session control mechanism triggered by a physical button press (using GPIO 17 or an equivalent pin) with proper debouncing and a press-and-hold safeguard for session termination.
*   Incorporating basic JWT token retrieval and handling (via a companion website or pre-fed token) to manage authentication with the server.
*   Implementing full-duplex audio streaming to enable simultaneous audio input and output.
*   Handling errors, including network interruptions, with automatic reconnection attempts (using exponential backoff) and local logging of session events and errors.

### Out-of-Scope

*   Advanced audio processing features such as noise suppression or voice activity detection (feature to be considered in V2).
*   Integration with external monitoring or analytics services for logging (local logging will be implemented initially).
*   Hardware upgrades beyond using the Raspberry Pi Zero 2 W, unless testing shows that a more powerful model is needed.
*   Complex security or encryption measures for the audio data beyond JWT token management.
*   Extensive user interface features other than simple audio/physical button interactions (e.g., no graphical interface on the Raspberry Pi).

## 3. User Flow

When the Raspberry Pi boots up, it initializes all hardware components including the microphone for audio capture, speakers for output, and the physical button via a designated GPIO pin (e.g., GPIO 17). During initialization, a WebSocket connection is established with the Sesame service. Once these components are ready, the system waits for the user to trigger a session with a button press.

On a button press, the system enters a voice session mode. It reads a pre-fed JWT token (from a companion website if available) to authenticate with the server, starts streaming the microphone audio data over the WebSocket in real time, and simultaneously plays any responding audio received from the server. A safeguard requiring a press-and-hold (approximately 2 seconds) is implemented to end the session, preventing accidental session termination. Once the button is held for the required duration, the session gracefully terminates by stopping the audio stream, disconnecting from the server, and logging the event locally.

## 4. Core Features (Bullet Points)

*   **WebSocket Connection**:

    *   Establish a persistent connection to "wss://sesameai.app/agent-service-0/v1/connect".
    *   Handle periodic pings from the server and maintain a live session through error handling and reconnection attempts (exponential backoff).

*   **Audio Input/Output**:

    *   Use Python libraries (pyaudio) to capture user audio from the microphone (16 kHz, 16-bit) and transmit it in real time over the WebSocket.
    *   Play audio responses from the server through the connected speakers while maintaining low latency (<200 ms).

*   **Session Control via Physical Button**:

    *   Monitor a designated GPIO pin (e.g., GPIO 17) for button presses using libraries such as RPi.GPIO or gpiozero with built-in debouncing logic.
    *   Trigger session start on a short button press and session termination after a press-and-hold (around 2 seconds) to avoid accidental disruptions.

*   **JWT Token Authentication**:

    *   Integrate a process for receiving a JWT token via a companion service or input mechanism.
    *   Securely pass that token when initiating sessions with the Sesame server.

*   **Error Handling & Logging**:

    *   Implement robust error handling for network interruptions and hardware disconnections.
    *   Log session events, including timestamps, button actions, connection statuses, and errors to a local log file for troubleshooting.

## 5. Tech Stack & Tools

*   **Programming Language**: Python

*   **Libraries**:

    *   websockets (for handling the WebSocket connection)
    *   pyaudio (for audio capture and playback)
    *   RPi.GPIO or gpiozero (for handling GPIO interactions with debouncing)

*   **Hardware**: Raspberry Pi Zero 2 W (with a connected microphone and speakers; consider a more powerful model if performance becomes an issue)

*   **AI Models/Services**:

    *   While full AI integration is not handled locally, the solution relies on remote AI processing via the Sesame service.

*   **Development Tools**:

    *   Windsurf (Modern IDE with integrated AI coding capabilities)
    *   Claude 3.7 Sonnet (For reasoning and intelligent assistance in the coding process)

## 6. Non-Functional Requirements

*   **Performance**:

    *   Maintain audio latency below 200 ms for a natural voice interaction experience.
    *   Ensure real-time full-duplex audio processing without noticeable lag.

*   **Security**:

    *   Handle JWT tokens securely for session authentication.
    *   While extensive encryption for audio data is not required, ensure secure transmission over the WebSocket using the provided URL.

*   **Reliability**:

    *   Integrate robust error handling and automatic reconnection strategies (exponential backoff) for WebSocket connection drops.
    *   Implement hardware debouncing to avoid false button triggers and ensure consistent session control.

*   **Usability**:

    *   Use simple, clear physical interactions (button press and press-and-hold) to start and stop sessions, delivering clear audio/visual feedback during operations.
    *   Ensure that the system logs relevant events for debugging without requiring constant manual monitoring.

## 7. Constraints & Assumptions

*   **Hardware Constraints**:

    *   The initial deployment will use a Raspberry Pi Zero 2 W, though a more powerful model might be considered if the processing needs for real-time full-duplex audio exceed its capabilities.
    *   The physical button is assumed to use GPIO 17 (or another available pin), and a pull-down resistor will be used (either physically or via internal GPIO settings).

*   **Audio Specifications**:

    *   The microphone and speakers must support a sample rate of 16 kHz and a bit depth of 16 bits.
    *   Buffer sizes must be optimized within the pyaudio configurations to balance between performance (low latency) and audio quality.

*   **Connectivity Assumptions**:

    *   A stable internet connection is assumed for maintaining a persistent WebSocket connection to the remote service.
    *   JWT tokens are assumed to be retrieved easily via a companion website, and security beyond this authentication is not a major concern in the current scope.

*   **Software Dependencies**:

    *   The project assumes availability and compatibility of the necessary Python libraries (websockets, pyaudio, RPi.GPIO/gpiozero) on the target Raspberry Pi environment.
    *   Full-duplex streaming is assumed to be supported by the chosen hardware and libraries under optimal conditions.

## 8. Known Issues & Potential Pitfalls

*   **Hardware Limitations**:

    *   The Raspberry Pi Zero 2 W might face performance issues if processing power or memory is insufficient for real-time full-duplex audio. Monitor CPU usage and consider upgrading to a more powerful model if necessary.

*   **Network Interruptions**:

    *   The WebSocket connection may experience disconnections or network latency, so a robust error handling mechanism with exponential backoff is critical. Ensure that reconnection logic does not create memory leaks or excessive logging.

*   **Debouncing and Button Reliability**:

    *   Mechanical button bouncing is always a risk. While software debouncing (using a 50 ms delay) is planned, ensure that the code is tested under various conditions to handle spurious triggers reliably.

*   **Audio Buffering/Latency Issues**:

    *   Tuning the pyaudio buffer sizes is essential. Too small buffer sizes may lead to dropped audio frames, while too large buffers could introduce latency. Experiment with different settings to find the optimal configuration.

*   **JWT Token Management**:

    *   The reliance on a separate companion website for token retrieval might complicate the initial setup. Ensure that token management and passing to the WebSocket connection are robustly handled.

*   **Server-Side "ping" Messages**:

    *   The Sesame server sometimes sends a 'type: ping' message. The client code must be able to identify and handle these messages correctly to maintain the connection without misinterpreting them as session events.

This comprehensive PRD should serve as the main reference for the development of the Raspberry Pi voice-interaction script, enabling subsequent technical documents to be generated with no ambiguity about the project’s goals, requirements, or constraints.
