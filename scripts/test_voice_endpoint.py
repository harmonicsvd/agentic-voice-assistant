"""
Test script for the /voice/process endpoint.
Tests the integrated voice pipeline via HTTP.
"""

import httpx
from pathlib import Path

def test_voice_endpoint():
    """Test the /voice/process endpoint with audio file."""
    print("=" * 60)
    print("Testing /voice/process Endpoint")
    print("=" * 60)
    
    # Check for test audio file
    test_audio_path = Path("test_audio.wav")
    if not test_audio_path.exists():
        test_audio_path = Path("test_audio.webm")
    
    if not test_audio_path.exists():
        print("⚠ No test audio file found.")
        print("  Place a .wav or .webm file as 'test_audio.wav' or 'test_audio.webm'")
        return
    
    print(f"Using audio file: {test_audio_path}")
    print(f"File size: {test_audio_path.stat().st_size} bytes")
    
    # Read audio file
    with open(test_audio_path, 'rb') as f:
        audio_bytes = f.read()
    
    print("\nSending request to http://localhost:8000/voice/process")
    
    try:
        # Send request to endpoint
        with httpx.Client(timeout=120) as client:
            files = {'audio': (test_audio_path.name, audio_bytes, 'audio/wav')}
            response = client.post(
                "http://localhost:8000/voice/process",
                files=files
            )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            output_size = len(response.content)
            print(f"✓ Success! Received {output_size} bytes of audio")
            
            # Save output
            output_path = "endpoint_output.wav"
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"✓ Saved output to {output_path}")
        else:
            print(f"✗ Error: {response.text}")
            
    except httpx.ConnectError:
        print("✗ Connection error: Is the server running at http://localhost:8000?")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_voice_endpoint()
