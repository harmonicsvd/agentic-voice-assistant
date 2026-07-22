import asyncio
import websockets
import json
from pathlib import Path

async def test_audio_client():
    """Send audio file to Pipecat WebSocket endpoint."""
    uri = 'ws://localhost:8000/ws/pipecat'
    
    try:
        # Get the correct path to the audio file
        script_dir = Path(__file__).parent
        audio_file = script_dir.parent / 'test_audio.wav'
        
        print(f'Audio file path: {audio_file}')
        
        # Read the audio file
        with open(audio_file, 'rb') as f:
            audio_data = f.read()
        
        print(f'Audio file size: {len(audio_data)} bytes')
        print('Connecting to WebSocket...')
        
        async with websockets.connect(uri) as websocket:
            print('WebSocket connected successfully!')
            
            # Send audio data
            print('Sending audio data...')
            await websocket.send(audio_data)
            print('Audio data sent')
            
            # Receive audio frames continuously
            print('Waiting for audio response...')
            try:
                while True:
                    response = await websocket.recv()
                    print(f'Received {len(response)} bytes of audio data')
            except websockets.exceptions.ConnectionClosed:
                print('Connection closed')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    asyncio.run(test_audio_client())