flowchart TD
    A[Hardware Initialization: Setup Mic, Speakers, Button with Debounce, WebSocket Connection]
    B[Button Press Detected: Start Session]
    C[Retrieve JWT Token from Companion Website]
    D[Initiate Full-Duplex Audio Streaming]
    E[Capture Audio from Microphone]
    F[Transmit Audio to Server via WebSocket]
    G[Receive Audio from Server]
    H[Play Audio through Speakers]
    I[Button Press-and-Hold 2 seconds: Terminate Session]
    J[Stop Audio Streaming and Disconnect WebSocket]
    K[Log Session Events and Errors]
    L[Error Detected: Trigger Exponential Backoff Reconnection]

    A --> B
    B --> C
    C --> D
    D --> E
    D --> F
    F --> G
    G --> H
    D --> K
    I --> J
    J --> K
    L --> D
    B -- Long Press --> I