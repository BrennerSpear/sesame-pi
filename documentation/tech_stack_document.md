# Tech Stack Document

This document explains the technology choices for our voice interaction system running on a Raspberry Pi. It is designed to provide clear and non-technical insight into the components we use and why they were chosen.

## Frontend Technologies

While this project is primarily a hardware-driven Python script, there is a small user-facing component in the form of the companion website that helps manage authentication (JWT tokens) and potentially provides visual status indicators. In summary:

*   **Companion Website** (optional): Serves as a portal where users can log in and retrieve a JWT token. This simple interface is built with modern web standards to ensure it is user-friendly and accessible.
*   **Physical Interface**: The Raspberry Pi itself acts as a minimal frontend. It uses a physical button for session control and integrates audio input and output for interaction. This hands-on interface eliminates the need for a traditional screen-based UI while still providing an effective way for users to interact with the system.

## Backend Technologies

The core of our application is implemented on the Raspberry Pi with Python handling the backend processes. These are the main components and libraries involved:

*   **Programming Language: Python**

    *   Provides a simple yet powerful language with a large variety of libraries supporting hardware integration.

*   **WebSockets Library (**`websockets`**)**

    *   Manages the persistent WebSocket connection to the third-party server at `wss://sesameai.app/agent-service-0/v1/connect`, ensuring real-time bi-directional communication.

*   **Audio Processing with **`pyaudio`

    *   Handles capturing audio from the microphone and playing audio through the speakers with parameters optimized for speech (16 kHz sample rate, 16-bit depth).

*   **GPIO Handling (**`rpi_gpio`** or similar, such as RPi.GPIO or gpiozero)**

    *   Interfaces with the physical button connected to the Raspberry Pi (using, for example, GPIO 17), including debouncing logic to filter out noise due to mechanical bounce.

## Infrastructure and Deployment

The infrastructure choices are designed to keep the system lean, reliable, and easy to update or troubleshoot:

*   **Hardware: Raspberry Pi Zero 2 W**

    *   A compact, low-power device that performs the required tasks. It is paired with an external microphone and speakers to handle audio input and output. Should performance require an upgrade, newer models like the Raspberry Pi 3 or 4 may be considered in the future.

*   **Development Environment & IDE: Windsurf**

    *   Provides a modern integrated development environment with AI coding assistance, simplifying coding, testing, and debugging.

*   **Version Control: Git**

    *   Keeps track of changes to the codebase, making collaboration and future updates straightforward.

*   **Local Logging**

    *   Logs session details, button events, WebSocket connection status, and errors locally on the Raspberry Pi for quick troubleshooting and maintenance.

## Third-Party Integrations

The application integrates with several external services and libraries to extend its functionality:

*   **Sesame AI Remote Service**

    *   The system connects to a third-party WebSocket service, which processes voice interactions using AI. The remote service handles the heavy lifting of processing and responding to user audio input.

*   **JWT Token Retrieval via a Companion Portal**

    *   A secondary service to authenticate with the Sesame AI service. This system is designed to securely retrieve and manage JWT tokens to establish an authorized session.

## Security and Performance Considerations

Even though the project is focused on local operation, the following measures ensure the system remains secure and responsive:

*   **Authentication and Token Handling (JWT)**

    *   Integrates with a companion system to securely retrieve and manage JWT tokens. The Raspberry Pi sends these tokens when initiating WebSocket connections.

*   **Hardware Debouncing & Safeguards**

    *   Uses software debouncing on the physical button (typically using a short 50 ms delay) to avoid misreads from mechanical bounce. A long press (around 2 seconds) is required to terminate a session, protecting against accidental interruptions.

*   **Robust Error Handling**

    *   Implements automatic reconnection strategies for the WebSocket connection using an exponential backoff approach. This ensures the system can recover gracefully from network disruptions by resetting the microphone, speakers, and connection as needed.

*   **Performance Optimizations**

    *   Uses audio settings (16 kHz sample rate and 16-bit depth) that strike the right balance between quality and resource usage. Buffer sizes are adjusted within the audio library to maintain low latency (under 200 ms) for a natural interaction flow.

## Conclusion and Overall Tech Stack Summary

This project leverages a combination of hardware and well-established software libraries to create a reliable and responsive voice interaction system. Key points include:

*   A straightforward physical interface using a Raspberry Pi Zero 2 W with a button, microphone, and speakers.
*   Python-based backend integration with powerful libraries such as `websockets` for real-time communication and `pyaudio` for managing audio streams.
*   A secure, albeit simple, method for handling JWT tokens via a companion website.
*   Careful attention to error handling, with features like automatic reconnections and local logging to simplify maintenance and troubleshooting.

These choices align with the project’s goals by keeping the system simple, efficient, and highly responsive, while ensuring user interactions are smooth and intuitive. The combination of these technologies sets our project apart by blending robust audio processing with real-time communication, all within a compact and user-friendly interactive system.
