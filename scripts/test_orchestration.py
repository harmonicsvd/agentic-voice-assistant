"""
Test script for the VoiceOrchestrator.
Tests the full pipeline: STT → LLM → Tools → TTS
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.orchestration import VoiceOrchestrator

def test_individual_components():
    """Test each component individually."""
    print("=" * 60)
    print("Testing Individual Components")
    print("=" * 60)
    
    orchestrator = VoiceOrchestrator()
    
    # Test 1: TTS (no audio needed)
    print("\nStep 1: Testing TTS")
    print("-" * 60)
    test_text = "Hello, this is a test of the voice orchestration system."
    audio = orchestrator.synthesize_speech(test_text)
    print(f"✓ TTS works: {len(audio)} bytes generated")
    
    # Test 2: LLM (no audio needed)
    print("\nStep 2: Testing LLM")
    print("-" * 60)
    llm_response = orchestrator.process_with_llm("What is 2 + 2?")
    print(f"✓ LLM works: {llm_response}")
    
    print("\n" + "=" * 60)
    print("Individual Component Tests Complete!")
    print("=" * 60)

def test_full_pipeline_with_audio():
    """Test the full pipeline with audio (if available)."""
    print("\n" + "=" * 60)
    print("Testing Full Pipeline with Audio")
    print("=" * 60)
    
    # Check if we have a test audio file
    test_audio_path = Path("test_audio.wav")
    if not test_audio_path.exists():
        test_audio_path = Path("test_audio.webm")
    
    if not test_audio_path.exists():
        print("⚠ No test audio file found. Skipping full pipeline test.")
        print("  To test full pipeline, place a .wav or .webm audio file as 'test_audio.wav' or 'test_audio.webm'")
        return
    
    orchestrator = VoiceOrchestrator()
    
    # Read audio
    with open(test_audio_path, 'rb') as f:
        audio_bytes = f.read()
    
    print(f"Loaded audio: {len(audio_bytes)} bytes")
    
    # Run full pipeline
    print("\nRunning full pipeline...")
    output_audio = orchestrator.run_pipeline(audio_bytes)
    
    print(f"✓ Full pipeline works: {len(output_audio)} bytes output")
    
    # Save output
    output_path = "pipeline_output.wav"
    with open(output_path, 'wb') as f:
        f.write(output_audio)
    print(f"✓ Saved output to {output_path}")

def main():
    """Run all tests."""
    print("VoiceOrchestrator Test Suite")
    print("=" * 60)
    
    test_individual_components()
    test_full_pipeline_with_audio()
    
    print("\n" + "=" * 60)
    print("All Tests Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()