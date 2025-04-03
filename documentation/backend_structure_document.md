# Backend Structure Document

This document outlines the backend setup for our Python-based voice interaction project running on a Raspberry Pi. It provides a clear understanding of how the backend system is structured, the components involved, and the strategies used to ensure reliability and performance.

## 1. Backend Architecture

The backend is designed around a lightweight, event-driven, asynchronous Python script running on a Raspberry Pi. The key points of this architecture include:

*   **Event-Driven & Asynchronous:**

    *   Uses Python’s asynchronous capabilities (with libraries such as asyncio) to handle real-time audio streaming and WebSocket communication efficiently.
    *   Implements event-driven patterns to detect button presses, manage audio streams, and handle server responses.

*   **Modular Design:**

    *   Separates concerns into modules (audio capture, transmission, session control, error handling, and logging), enhancing maintainability and ease of updates.
    *   Easy replacement or upgrade of components (e.g., moving to a Raspberry Pi 3/4 if needed) without reworking the entire system.

*   **Scalability & Performance:**

    *   Designed for a single device scenario but structured in a way that could be extended to multi-device setups or integrated with additional services if necessary.
    *   Prioritizes low latency (< 200ms) in audio streaming and uses techniques such as exponential backoff for reconnection to maintain a smooth user experience.

*   **Tech Stack Components (Bullet Points):**

    *   Programming Language: Python

    *   Libraries:

        *   websockets (for real-time WebSocket communication)
        *   pyaudio (for capturing and playing audio)
        *   RPi.GPIO or gpiozero (for handling the physical button and GPIO interactions)

## 2. Database Management

Although this is not a traditional web application with extensive data storage needs, the project incorporates a lightweight logging mechanism to maintain session details and error logs.

*   **Local Logging:**

    *   Logs are stored locally on the Raspberry Pi to assist with debugging and tracking session activities.

*   **Database Consideration:**

    *   A local SQLite database can be utilized to store session logs systematically rather than flat files. This makes search and retrieval simpler if more in-depth analysis is needed later.

## 3. Database Schema

For local logging, the use of an SQL-based local database (SQLite) is recommended. A human-readable version of the schema is as follows:

*   **Sessions Table:** Tracks each voice interaction session.

    *   Columns:

        *   Session ID (Primary Key, auto-increment integer)
        *   Start Time (Timestamp when session begins)
        *   End Time (Timestamp when session ends)
        *   Status (e.g., 'active', 'completed', 'error')
        *   Notes (Text field for additional info or error messages)

*   **Logs Table:** Stores log messages and error information.

    *   Columns:

        *   Log ID (Primary Key, auto-increment integer)
        *   Timestamp (Date and time of the log entry)
        *   Session ID (Foreign Key linking to Sessions table)
        *   Log Level (e.g., INFO, WARNING, ERROR)
        *   Message (Detail of the log/error)

*For a simple SQLite implementation, the following SQL statements illustrate the schema setup:*

-- Sessions Table CREATE TABLE Sessions ( SessionID INTEGER PRIMARY KEY AUTOINCREMENT, StartTime TIMESTAMP NOT NULL, EndTime TIMESTAMP, Status TEXT NOT NULL, Notes TEXT );

-- Logs Table CREATE TABLE Logs ( LogID INTEGER PRIMARY KEY AUTOINCREMENT, Timestamp TIMESTAMP NOT NULL, SessionID INTEGER, LogLevel TEXT NOT NULL, Message TEXT, FOREIGN KEY(SessionID) REFERENCES Sessions(SessionID) );

## 4. API Design and Endpoints

While the Raspberry Pi acts primarily as a client connecting to an external WebSocket API, it also uses in-project API-like interactions for session management and logging.

*   **WebSocket API Integration:**

    *   The main API endpoint is the Sesame AI demo server at:

        *   wss://sesameai.app/agent-service-0/v1/connect

    *   Responsibilities of the endpoint include handling a full-duplex audio stream and processing control messages (such as ping messages).

*   **Internal API Endpoints (Conceptual):**

    *   Although not exposed to external users, the system internally defines methods to:

        *   Start a session when a button press is detected.
        *   Stream captured audio to the server.
        *   Receive and play audio responses in real-time.
        *   Handle session termination on a press-and-hold of the button.

## 5. Hosting Solutions

The hosting environment for the project is tailored for the specialized hardware and real-time nature of the application.

*   **Local Hosting on Raspberry Pi:**

    *   The Python script runs directly on the Raspberry Pi Zero 2 W (or Pi 3/4 if upgraded). This ensures minimal delay between sensor input (button press) and response.

*   **Benefits of the Chosen Setup:**

    *   **Reliability:** The device operates independently without reliance on external cloud hosting, reducing points of failure.
    *   **Scalability:** Though designed for a single device, the architecture allows for future expansion where multiple devices interact with a centralized logging service or dashboard.
    *   **Cost-Effectiveness:** Utilizing existing hardware eliminates recurring cloud hosting expenses for a lightweight solution.

## 6. Infrastructure Components

Various components within the infrastructure ensure smooth operations and improved performance:

*   **Physical Device:**

    *   Raspberry Pi running the main Python script.

*   **Networking Components:**

    *   WiFi or Ethernet connectivity to reliably maintain a connection with the Sesame AI server.

*   **Audio Components:**

    *   Microphone and speakers integrated with pyaudio for full-duplex audio processing.

*   **Load Balancing & Caching (Conceptual):**

    *   While not necessary for a single device, the design could incorporate a load balancer if extended to multiple devices in the future.
    *   OS-level buffering and caching mechanisms are utilized to ensure uninterrupted streaming and low latency.

## 7. Security Measures

Security is addressed to protect the system and its interactions, even if the scope is limited for the initial implementation:

*   **JWT Token Handling:**

    *   Securely processes a pre-fed JWT token to authenticate the WebSocket connection with the Sesame AI server.
    *   The token is stored and handled carefully within the local environment to prevent exposure.

*   **Communication Security:**

    *   Uses WebSocket protocol over TLS (wss) which encrypts data between the Raspberry Pi and the remote server.

*   **Local Security Measures:**

    *   Minimal user data is stored; however, local logs and session details are maintained with adequate caution against unauthorized access.

## 8. Monitoring and Maintenance

Monitoring and maintenance strategies ensure the longevity and stability of the backend system:

*   **Local Logging and Alerting:**

    *   The system logs key events, errors, and session information, all of which can be reviewed for troubleshooting.
    *   In cases of errors or reconnection attempts due to network issues, the script logs details to help diagnose problems.

*   **Automatic Reconnection:**

    *   Implements an exponential backoff strategy to attempt reconnections automatically in the event of a lost connection, thereby enhancing reliability.

*   **Performance Monitoring:**

    *   Regular checks on audio latency and system performance help maintain the target of < 200ms delay.
    *   Maintenance scripts (or system-level cron jobs) may be set up to review logs and system health periodically.

## 9. Conclusion and Overall Backend Summary

This backend structure brings together a lightweight, event-driven system optimized for real-time voice interaction on a Raspberry Pi. Key points include:

*   A modular and asynchronous Python backend that ensures low latency and reliable session management.
*   Local logging with a potential SQLite database for session and error details, supporting a straightforward operational overview.
*   Direct integration with a third-party WebSocket API (wss://sesameai.app/agent-service-0/v1/connect) for full-duplex audio processing.
*   A self-contained hosting environment on the Raspberry Pi that minimizes external dependencies, while still putting in place clear security and maintenance protocols.

This setup aligns with the project’s goals of providing responsive, real-time voice interactions while maintaining ease of maintenance and the possibility for future scalability or feature expansion.

Unique aspects of this backend include its fusion of real-time audio streaming with local, hardware-based event handling, ensuring that the system is both responsive and robust even under challenging real-world operating conditions.
