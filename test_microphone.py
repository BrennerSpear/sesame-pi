import pyaudio
import numpy as np
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler()  # Print to console
    ]
)

def test_microphone():
    """
    Simple script to test microphone functionality:
    1. List all available audio devices
    2. Capture audio from the default microphone
    3. Check if there's actual data (not just silence) being captured
    """
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    # List all available audio devices
    logging.info("=== Available Audio Devices ===")
    default_input_device_info = p.get_default_input_device_info()
    default_input_device_index = default_input_device_info['index']
    
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        is_input = device_info['maxInputChannels'] > 0
        is_default = " (DEFAULT)" if i == default_input_device_index and is_input else ""
        
        if is_input:
            logging.info(f"Input Device {i}: {device_info['name']}{is_default}")
            logging.info(f"  Sample Rate: {int(device_info['defaultSampleRate'])}")
            logging.info(f"  Channels: {device_info['maxInputChannels']}")
    
    logging.info(f"\nUsing default input device: {default_input_device_info['name']} (index {default_input_device_index})")
    
    # Audio stream parameters
    CHUNK = 4096  # Increased from 1024 to 4096 for longer chunks
    FORMAT = pyaudio.paFloat32
    CHANNELS = 1
    RATE = 24000  # Changed from 16000 to 24000 to match server's rate
    MAX_CHUNKS = 32  # Increased from 16 to 32 chunks for longer recording
    
    logging.info(f"\nStarting audio capture for {MAX_CHUNKS} chunks...")
    logging.info(f"Format: {FORMAT}, Channels: {CHANNELS}, Rate: {RATE}, Chunk size: {CHUNK}")
    
    # Store non-silent chunks for playback
    non_silent_chunks = []
    
    # Open input stream
    input_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    
    # Start recording
    try:
        for i in range(MAX_CHUNKS):
            # Read audio data
            data = input_stream.read(CHUNK, exception_on_overflow=False)
            
            # Convert to numpy array for analysis
            audio_data = np.frombuffer(data, dtype=np.float32)
            
            # Calculate audio metrics
            rms = np.sqrt(np.mean(np.square(audio_data)))
            peak = np.max(np.abs(audio_data))
            
            # Determine if there's actual sound (not just silence)
            is_silent = rms < 0.01  # Adjust this threshold as needed
            
            # Store non-silent chunks for playback
            if not is_silent:
                non_silent_chunks.append(data)
            
            # Log audio metrics
            logging.info(f"Chunk {i}: RMS={rms:.6f}, Peak={peak:.6f}, {'SILENT' if is_silent else 'SOUND DETECTED'}")
        
        # Playback non-silent chunks
        if non_silent_chunks:
            logging.info(f"\nPlaying back {len(non_silent_chunks)} non-silent chunks...")
            
            # Open output stream for playback
            output_stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                frames_per_buffer=CHUNK
            )
            
            # Play each non-silent chunk
            for chunk in non_silent_chunks:
                output_stream.write(chunk)
            
            # Add a delay to allow buffer to empty before closing the stream
            logging.info("Waiting for buffer to empty...")
            time.sleep(1.0)  # 1 second delay to ensure buffer is emptied
            
            # Close output stream
            output_stream.stop_stream()
            output_stream.close()
            logging.info("Playback complete")
        else:
            logging.info("\nNo non-silent chunks detected for playback")
    
    except KeyboardInterrupt:
        logging.info("Recording stopped by user")
    except Exception as e:
        logging.error(f"Error during recording: {e}")
    finally:
        # Stop and close the input stream
        input_stream.stop_stream()
        input_stream.close()
        
        # Terminate PyAudio
        p.terminate()
        logging.info("PyAudio terminated")

if __name__ == "__main__":
    test_microphone()
