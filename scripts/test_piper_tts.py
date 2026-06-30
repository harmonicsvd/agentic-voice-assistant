"""
Test script for Piper TTS.
"""

import time
from piper import PiperVoice

def test_basic_tts():
    """Test basic text-to-speech."""
    print("=" * 60)
    print("Step 1: Testing Basic TTS")
    print("=" * 60)
    
    # Load the voice model
    model_path = "voice_models/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
    config_path = "voice_models/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
    
    print(f"Loading model from {model_path}...")
    voice = PiperVoice.load(model_path, config_path)
    
    # Synthesize speech
    text = "Hello, this is a test of the Piper text-to-speech engine."
    print(f"Synthesizing: {text}")
    
    start = time.time()
    audio_generator = voice.synthesize(text)
    
    # Combine all chunks using audio_int16_bytes
    audio_bytes = b''.join(chunk.audio_int16_bytes for chunk in audio_generator)
    elapsed = time.time() - start
    
    print(f"✓ Synthesis completed in {elapsed:.2f}s")
    print(f"  Audio length: {len(audio_bytes)} bytes")
    
    # Save to file
    output_path = "test_output.wav"
    with open(output_path, 'wb') as f:
        f.write(audio_bytes)
    print(f"✓ Saved to {output_path}")
    
    return elapsed

def main():
    """Run all tests."""
    print("Piper TTS Test Suite")
    print("=" * 60)
    
    test_basic_tts()
    
    print("\n" + "=" * 60)
    print("Tests Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()