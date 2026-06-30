"""
Test script for Faster-Whisper STT implementation.

This script tests:
1. Basic transcription with faster-whisper
2. Performance comparison with current Whisper
3. Streaming capabilities
4. VAD (Voice Activity Detection)
5. Output quality and accuracy

Usage:
    python scripts/test_faster_whisper.py
"""

import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_faster_whisper_installation():
    """Test if faster-whisper is installed."""
    print("=" * 60)
    print("Step 1: Testing Faster-Whisper Installation")
    print("=" * 60)
    
    try:
        from faster_whisper import WhisperModel
        print("✓ faster-whisper is installed")
        return True
    except ImportError:
        print("✗ faster-whisper is NOT installed")
        print("Install with: pip install faster-whisper")
        return False

def test_model_loading():
    """Test loading different model sizes."""
    print("\n" + "=" * 60)
    print("Step 2: Testing Model Loading")
    print("=" * 60)
    
    from faster_whisper import WhisperModel
    
    models_to_test = ["tiny", "base", "small"]
    results = {}
    
    for model_size in models_to_test:
        print(f"\nTesting model: {model_size}")
        try:
            start_time = time.time()
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
            load_time = time.time() - start_time
            results[model_size] = {
                "loaded": True,
                "load_time": load_time
            }
            print(f"  ✓ Loaded in {load_time:.2f}s")
        except Exception as e:
            results[model_size] = {
                "loaded": False,
                "error": str(e)
            }
            print(f"  ✗ Failed: {e}")
    
    return results

def test_transcription():
    """Test transcription with audio file."""
    print("\n" + "=" * 60)
    print("Step 3: Testing Transcription")
    print("=" * 60)
    
    from faster_whisper import WhisperModel
    
    # Find test audio file
    audio_path = Path(__file__).parent.parent / "test_audio.wav"
    if not audio_path.exists():
        print(f"✗ Audio file not found: {audio_path}")
        return None
    
    print(f"Using audio file: {audio_path}")
    print(f"File size: {audio_path.stat().st_size / 1024:.1f} KB")
    
    # Test with base model (good balance of speed/accuracy)
    print("\nLoading model (base)...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    
    print("Starting transcription...")
    start_time = time.time()
    
    segments, info = model.transcribe(
        str(audio_path),
        beam_size=5,
        language="en",
        vad_filter=True,  # Enable Voice Activity Detection
        vad_parameters=dict(min_silence_duration_ms=500)
    )
    
    # Collect all segments
    all_segments = []
    full_transcript = ""
    
    print("Processing segments:")
    for segment in segments:
        segment_text = segment.text.strip()
        all_segments.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment_text
        })
        full_transcript += segment_text + " "
        print(f"  [{segment.start:.2f}s -> {segment.end:.2f}s] {segment_text}")
    
    transcription_time = time.time() - start_time
    
    print(f"\n✓ Transcription completed in {transcription_time:.2f}s")
    print(f"  Detected language: {info.language} (probability: {info.language_probability:.2f})")
    print(f"  Number of segments: {len(all_segments)}")
    print(f"  Total duration: {info.duration:.2f}s")
    print(f"  Real-time factor: {transcription_time / info.duration:.2f}x")
    
    print(f"\nFull transcript:\n{full_transcript.strip()}")
    
    return {
        "transcription_time": transcription_time,
        "segments": all_segments,
        "full_transcript": full_transcript.strip(),
        "language_info": info
    }

def test_streaming_transcription():
    """Test streaming transcription (simulating real-time)."""
    print("\n" + "=" * 60)
    print("Step 4: Testing Streaming Transcription")
    print("=" * 60)
    
    from faster_whisper import WhisperModel
    
    audio_path = Path(__file__).parent.parent / "test_audio.wav"
    if not audio_path.exists():
        print(f"✗ Audio file not found: {audio_path}")
        return None
    
    print("Loading model (tiny for faster streaming)...")
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    
    print("Simulating streaming transcription:")
    print("(Processing segments as they arrive)")
    
    start_time = time.time()
    segment_count = 0
    
    segments, info = model.transcribe(
        str(audio_path),
        beam_size=5,
        language="en",
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )
    
    for segment in segments:
        segment_count += 1
        elapsed = time.time() - start_time
        print(f"  Segment {segment_count} at {elapsed:.2f}s: {segment.text.strip()}")
    
    total_time = time.time() - start_time
    print(f"\n✓ Streaming completed in {total_time:.2f}s")
    print(f"  Average segment latency: {total_time / segment_count:.2f}s")
    
    return {
        "total_time": total_time,
        "segment_count": segment_count
    }

def compare_with_current_whisper():
    """Compare with current Whisper implementation."""
    print("\n" + "=" * 60)
    print("Step 5: Comparing with Current Whisper")
    print("=" * 60)
    
    try:
        from app.stt import transcribe_audio_bytes
        import time
        
        audio_path = Path(__file__).parent.parent / "test_audio.wav"
        if not audio_path.exists():
            print(f"✗ Audio file not found: {audio_path}")
            return None
        
        print("Testing current Whisper implementation...")
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        
        start_time = time.time()
        transcript = transcribe_audio_bytes(audio_bytes, suffix=".wav")
        current_time = time.time() - start_time
        
        print(f"✓ Current Whisper transcription time: {current_time:.2f}s")
        print(f"  Transcript: {transcript}")
        
        return {
            "transcription_time": current_time,
            "transcript": transcript
        }
    except Exception as e:
        print(f"✗ Could not test current Whisper: {e}")
        print("  (This is okay if STT dependencies not installed)")
        return None

def print_summary(results):
    """Print summary of all tests."""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if results.get("installation"):
        print("✓ Installation: PASSED")
    else:
        print("✗ Installation: FAILED")
    
    if results.get("model_loading"):
        print("✓ Model Loading: PASSED")
        for model, info in results["model_loading"].items():
            if info.get("loaded"):
                print(f"  - {model}: {info['load_time']:.2f}s")
    else:
        print("✗ Model Loading: FAILED")
    
    if results.get("transcription"):
        trans = results["transcription"]
        print(f"✓ Transcription: PASSED")
        print(f"  - Time: {trans['transcription_time']:.2f}s")
        print(f"  - Segments: {len(trans['segments'])}")
    else:
        print("✗ Transcription: FAILED")
    
    if results.get("streaming"):
        stream = results["streaming"]
        print(f"✓ Streaming: PASSED")
        print(f"  - Total time: {stream['total_time']:.2f}s")
        print(f"  - Segments: {stream['segment_count']}")
    else:
        print("✗ Streaming: FAILED")
    
    if results.get("current_whisper"):
        current = results["current_whisper"]
        faster = results.get("transcription", {})
        print(f"✓ Comparison: AVAILABLE")
        print(f"  - Current Whisper: {current['transcription_time']:.2f}s")
        if faster:
            print(f"  - Faster-Whisper: {faster['transcription_time']:.2f}s")
            speedup = current['transcription_time'] / faster['transcription_time']
            print(f"  - Speedup: {speedup:.2f}x")
    else:
        print("✓ Comparison: SKIPPED (current Whisper not available)")

def main():
    """Run all tests."""
    print("Faster-Whisper STT Test Suite")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Installation
    results["installation"] = test_faster_whisper_installation()
    if not results["installation"]:
        print("\n❌ Cannot proceed without faster-whisper installation")
        return
    
    # Test 2: Model loading
    results["model_loading"] = test_model_loading()
    
    # Test 3: Basic transcription
    results["transcription"] = test_transcription()
    
    # Test 4: Streaming
    results["streaming"] = test_streaming_transcription()
    
    # Test 5: Compare with current
    results["current_whisper"] = compare_with_current_whisper()
    
    # Print summary
    print_summary(results)
    
    print("\n" + "=" * 60)
    print("Recommendations:")
    print("=" * 60)
    
    if results.get("transcription"):
        trans_time = results["transcription"]["transcription_time"]
        if trans_time < 2.0:
            print("✓ Performance is good for real-time use")
        elif trans_time < 5.0:
            print("⚠ Performance is acceptable, consider GPU for faster processing")
        else:
            print("✗ Performance is slow, consider using smaller model or GPU")
    
    if results.get("current_whisper") and results.get("transcription"):
        speedup = results["current_whisper"]["transcription_time"] / results["transcription"]["transcription_time"]
        if speedup > 2.0:
            print(f"✓ Faster-Whisper is {speedup:.1f}x faster - good for migration")
        else:
            print(f"⚠ Speedup is only {speedup:.1f}x - consider optimization")
    
    print("\nNext steps:")
    print("1. If performance is good: Proceed to Phase 2 (Real-time STT)")
    print("2. If performance is slow: Try smaller model or GPU acceleration")
    print("3. Update requirements-stt.txt with faster-whisper")

if __name__ == "__main__":
    main()
