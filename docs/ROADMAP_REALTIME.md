# Real-Time Voice WebSocket Roadmap

## Objective
Replace VAPI with custom real-time WebSocket implementation for bidirectional voice streaming.

## Current State
- ✅ STT (Faster-Whisper) - works with full audio files
- ✅ LLM (Mistral + LangGraph) - works with text
- ✅ Tools (calendar, meetings) - works
- ✅ TTS (Piper) - works with full audio files
- ✅ Session management - works
- ✅ Multi-turn conversation - works
- ❌ WebSocket endpoint - missing
- ❌ Audio streaming - missing
- ❌ VAD (Voice Activity Detection) - missing
- ❌ Interrupt handling - missing

## Architecture

### Backend (FastAPI)
1. **WebSocket Endpoint** (`/voice/ws`)
   - Accept WebSocket connections
   - Handle session_id for multi-turn
   - Bidirectional audio streaming

2. **Audio Buffer Management**
   - Accumulate incoming audio chunks
   - Convert to WAV format for STT
   - Buffer management (size limits)

3. **VAD (Voice Activity Detection)**
   - Detect when user stops speaking
   - Silence threshold detection
   - Trigger pipeline on speech end

4. **Pipeline Trigger**
   - Run STT → LLM → Tools → TTS on VAD trigger
   - Use existing LangGraph orchestration
   - Maintain session state

5. **Streaming TTS**
   - Modify TTS to stream audio chunks
   - Send chunks via WebSocket as generated
   - Low latency response

6. **Interrupt Handling**
   - Detect user speaking during TTS
   - Stop current TTS generation
   - Clear audio buffer
   - Resume listening

7. **Greeting Message**
   - Send greeting audio on connect
   - "Hello, I'm your voice assistant. How can I help?"

### Frontend (WebSocket Client)
1. **WebSocket Connection**
   - Connect to backend
   - Handle reconnection
   - Pass session_id

2. **Audio Capture**
   - Microphone access
   - Stream audio chunks to backend
   - Sample rate/format matching

3. **Audio Playback**
   - Play incoming audio chunks
   - Queue management
   - Smooth playback

## Implementation Steps

### Phase 1: WebSocket Infrastructure
- [ ] Add `websockets` to requirements-stt.txt ✅ DONE
- [ ] Add `python-multipart` to requirements-stt.txt ✅ DONE
- [ ] Install websockets library
- [ ] Create basic WebSocket endpoint in app/main.py
- [ ] Test WebSocket connection with simple echo

### Phase 2: Audio Streaming
- [ ] Implement audio buffer for incoming chunks
- [ ] Add WAV header generation for buffered audio
- [ ] Stream audio chunks from frontend
- [ ] Test audio chunk reception

### Phase 3: VAD Integration
- [ ] Add VAD library (webrtcvad or silero-vad)
- [ ] Implement silence detection logic
- [ ] Trigger pipeline on speech end
- [ ] Test VAD with audio samples

### Phase 4: Pipeline Integration
- [ ] Connect buffered audio to STT
- [ ] Run LangGraph pipeline on VAD trigger
- [ ] Handle LLM responses
- [ ] Execute tools as needed

### Phase 5: Streaming TTS
- [ ] Modify TTS to generate chunks
- [ ] Stream chunks via WebSocket
- [ ] Add WAV headers to chunks
- [ ] Test streaming audio playback

### Phase 6: Interrupt Handling
- [ ] Detect user speech during TTS
- [ ] Stop TTS generation
- [ ] Clear audio buffer
- [ ] Resume listening state
- [ ] Test interrupt scenarios

### Phase 7: Greeting & Polish
- [ ] Generate greeting audio
- [ ] Send greeting on connect
- [ ] Add error handling
- [ ] Add logging
- [ ] Performance optimization

### Phase 8: Frontend Client
- [ ] Create WebSocket client script
- [ ] Implement microphone capture
- [ ] Implement audio playback
- [ ] Add session management
- [ ] Test end-to-end

## Dependencies to Add
- `websockets` - WebSocket server/client
- `python-multipart` - For file uploads
- `webrtcvad` or `silero-vad` - Voice Activity Detection

## Key Challenges
1. **Audio Format** - Ensure consistent WAV format (16kHz, mono, 16-bit)
2. **Latency** - Minimize delay between speech and response
3. **Buffer Size** - Balance between responsiveness and accuracy
4. **Interrupt Detection** - Accurately detect user interruptions
5. **Session State** - Maintain state across WebSocket messages

## Testing Strategy
1. Unit test each component (VAD, buffering, streaming)
2. Integration test with WebSocket echo
3. End-to-end test with real audio
4. Load test with concurrent connections
5. Interrupt scenario testing

## Success Criteria
- [ ] WebSocket connects and stays stable
- [ ] Audio chunks stream bidirectionally
- [ ] VAD accurately detects speech end
- [ ] Pipeline processes speech correctly
- [ ] TTS streams audio with low latency
- [ ] Interrupts work smoothly
- [ ] Greeting plays on connect
- [ ] Multi-turn conversations work
