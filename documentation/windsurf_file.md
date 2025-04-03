# .windsurfrules

## Project Overview

*   **Type:** IoT Voice Interaction System
*   **Description:** Develop a voice interaction system on a Raspberry Pi Zero 2 W that interfaces with a Sesame AI demo server via persistent WebSocket connection. Utilize a physical button for session control, capture audio from a microphone, and play audio responses through speakers.
*   **Primary Goal:** Enable seamless full-duplex audio streaming with sub-200 ms latency and robust session management using hardware controls and software debouncing.

## Project Structure

### Framework-Specific Routing

*   **Directory Rules:**

    *   Python 3.x: As a non-web framework project, enforce a modular, script-driven directory layout.
    *   Example 1: Main entry in the root folder (`main.py`) for initializing processes.
    *   Example 2: Use a dedicated `src/` folder for core modules (audio, websocket, GPIO) with clear separation of concerns.

### Core Directories

*   **Versioned Structure:**

    *   `src/`: Contains core modules implementing essential functionalities.
    *   Example 1: `src/audio_handler.py` → "Manages microphone input and speaker output using PyAudio, maintaining a 16 kHz sample rate and 16-bit depth."
    *   Example 2: `src/websocket_handler.py` → "Handles persistent WebSocket communication to wss://sesameai.app/agent-service-0/v1/connect, including reconnection with exponential backoff."
    *   Example 3: `src/gpio_handler.py` → "Manages physical button input with debouncing (50ms delay) and distinguishes between short press and 2-second hold for session control."

### Key Files

*   **Stack-Versioned Patterns:**

    *   `main.py`: Aggregates initialization routines and integrates audio, websocket, and GPIO modules for overall system flow.
    *   `src/config.py`: Maintains configuration parameters including WebSocket URL, audio processing settings, and GPIO pin assignments (default GPIO 17, Pin 11).

## Tech Stack Rules

*   **Version Enforcement:**

    *   `python@3.x`: Must leverage asynchronous programming (e.g., asyncio) for handling simultaneous full-duplex audio streaming and WebSocket communication, ensuring efficient resource management on the Raspberry Pi.

## PRD Compliance

*   **Non-Negotiable:**

    *   "Press-and-hold (2 seconds) to end session": This rule requires strict implementation of hardware button press detection with a 50ms software debouncing mechanism before terminating an ongoing session.

## App Flow Integration

*   **Stack-Aligned Flow:**

    *   The physical button press (handled in `src/gpio_handler.py`) triggers the start of an audio session.
    *   `main.py` coordinates the initiation of audio capture (`src/audio_handler.py`) and establishes a persistent WebSocket connection via `src/websocket_handler.py`.
    *   The system listens for server "ping" messages to maintain the connection and uses an event-driven approach (asyncio) to manage real-time interactions across subsystems.
