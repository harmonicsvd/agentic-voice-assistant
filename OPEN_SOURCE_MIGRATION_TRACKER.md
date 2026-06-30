# Open Source Voice Stack Migration Tracker

## Project Overview
**Goal**: Migrate from VAPI to fully open-source voice AI stack while maintaining existing functionality (Ram + Sham integration).

**Current State**: 
- VAPI handles: STT, LLM, TTS, tool calling, session management
- Ram (voice-scheduling-agent): Calendar, auth, profile, UI
- Sham (weather-agent): Weather intelligence, RAG
- STT Lab: Whisper fine-tuning experience

**Target State**:
- Open-source STT: Faster-Whisper (streaming)
- Open-source LLM: Mistral 7B via Ollama
- Open-source TTS: Piper TTS
- Custom implementation: Tool calling, session management

---

## Technology Choices

### Speech-to-Text (STT)
**Choice**: Faster-Whisper
- **Why**: 4x faster than original Whisper, built-in streaming support, MIT licensed
- **Model**: `base` or `small` (balance speed/accuracy)
- **Features**: VAD (Voice Activity Detection), streaming segments
- **Installation**: `pip install faster-whisper`
- **Hardware**: CPU is sufficient, GPU optional for faster processing

### Brain (LLM)
**Choice**: Mistral 7B via Ollama
- **Why**: Fast, excellent tool calling, Apache 2.0 license, easy deployment
- **Alternative**: Llama 3.1 8B (if better reasoning needed)
- **Installation**: `ollama pull mistral`
- **Features**: Native function calling, fast inference, good reasoning
- **Hardware**: 8GB RAM minimum, 16GB recommended

### Text-to-Speech (TTS)
**Choice**: Piper TTS
- **Why**: Fast (~100ms latency), lightweight, good quality
- **Voice**: `en_US-lessac-medium` (natural male voice)
- **Alternative**: XTTS v2 (better quality, slower)
- **Installation**: `pip install piper-tts piper-phonemize`
- **Hardware**: CPU sufficient, very lightweight

---

## Implementation Phases

### Phase 1: Component Testing & Setup
**Goal**: Validate each component independently before integration.

#### Step 1.1: Test Faster-Whisper STT
- [x] Install faster-whisper in voice-scheduling-agent
- [x] Create test script using existing audio files
- [ ] Compare performance vs current Whisper
- [ ] Test streaming capabilities with VAD
- [ ] Measure latency and accuracy

**File**: `scripts/test_faster_whisper.py` ✅ CREATED
**Status**: IN PROGRESS - Ready to run tests

#### Step 1.2: Setup Mistral 7B via Ollama
- [ ] Install Ollama on local machine
- [ ] Pull Mistral 7B model
- [ ] Create test script for basic inference
- [ ] Test function calling capabilities
- [ ] Measure response latency

**File**: `scripts/test_mistral_ollama.py`

#### Step 1.3: Test Piper TTS
- [ ] Install Piper TTS dependencies
- [ ] Download voice model (en_US-lessac-medium)
- [ ] Create test script for basic synthesis
- [ ] Test audio quality and speed
- [ ] Measure synthesis latency

**File**: `scripts/test_piper_tts.py`

#### Step 1.4: Integration Test
- [ ] Create end-to-end test script
- [ ] Test: Audio → STT → LLM → TTS → Audio
- [ ] Measure total pipeline latency
- [ ] Identify bottlenecks

**File**: `scripts/test_full_pipeline.py`

---

### Phase 2: Real-Time STT Implementation
**Goal**: Replace current start-stop STT with streaming STT.

#### Step 2.1: Update STT Module
- [ ] Install faster-whisper in requirements
- [ ] Refactor `app/stt.py` to use faster-whisper
- [ ] Implement streaming transcription class
- [ ] Add VAD for speech segment detection
- [ ] Test with existing audio files

**Files**: 
- `app/stt.py` (refactor)
- `requirements-stt.txt` (update)

#### Step 2.2: Create Streaming WebSocket
- [ ] Add new WebSocket endpoint: `/ws/stt/stream`
- [ ] Implement real-time chunk processing
- [ ] Send partial transcripts as they arrive
- [ ] Handle final transcript assembly
- [ ] Add error handling and reconnection logic

**Files**:
- `app/main.py` (add streaming WebSocket)
- `app/streaming_stt.py` (new module)

#### Step 2.3: Update Frontend for Streaming
- [ ] Modify `index.html` to handle streaming transcripts
- [ ] Add real-time transcript display
- [ ] Implement partial transcript handling
- [ ] Add visual feedback for processing state
- [ ] Test with backend streaming endpoint

**Files**:
- `index.html` (update WebSocket handling)

---

### Phase 3: LLM Brain Integration
**Goal**: Replace VAPI's LLM with Mistral 7B for tool calling.

#### Step 3.1: LLM Service Module
- [ ] Create `app/llm_service.py` module
- [ ] Implement Ollama client wrapper
- [ ] Add function calling logic
- [ ] Implement prompt templates for tool routing
- [ ] Add conversation memory management

**Files**:
- `app/llm_service.py` (new)
- `app/prompts.py` (new)

#### Step 3.2: Tool Calling System
- [ ] Define tool schemas (calendar, weather, etc.)
- [ ] Implement tool router logic
- [ ] Add tool execution handlers
- [ ] Integrate with existing backend endpoints
- [ ] Test tool calling accuracy

**Files**:
- `app/tools.py` (new)
- `app/tool_router.py` (new)

#### Step 3.3: Conversation State Management
- [ ] Implement session management
- [ ] Add conversation history tracking
- [ ] Implement context window management
- [ ] Add user profile integration
- [ ] Test multi-turn conversations

**Files**:
- `app/session_manager.py` (new)
- `app/conversation_memory.py` (new)

---

### Phase 4: TTS Integration
**Goal**: Add voice output capability using Piper TTS.

#### Step 4.1: TTS Service Module
- [ ] Create `app/tts_service.py` module
- [ ] Implement Piper TTS wrapper
- [ ] Add audio streaming capabilities
- [ ] Implement voice selection logic
- [ ] Test synthesis quality and speed

**Files**:
- `app/tts_service.py` (new)
- `requirements-tts.txt` (new)

#### Step 4.2: Audio Response Endpoint
- [ ] Add WebSocket endpoint for audio streaming
- [ ] Implement real-time audio streaming
- [ ] Add text fallback option
- [ ] Handle audio format conversion
- [ ] Test with frontend audio player

**Files**:
- `app/main.py` (add TTS WebSocket)
- `index.html` (add audio player)

---

### Phase 5: Full Pipeline Integration
**Goal**: Connect all components into seamless voice conversation.

#### Step 5.1: Unified Conversation WebSocket
- [ ] Create single WebSocket for full conversation
- [ ] Implement bidirectional audio/text streaming
- [ ] Add interrupt handling (user can interrupt AI)
- [ ] Implement turn-taking logic
- [ ] Add silence detection for turn changes

**Files**:
- `app/main.py` (add conversation WebSocket)
- `app/conversation_manager.py` (new)

#### Step 5.2: Frontend Conversation UI
- [ ] Update UI for natural conversation flow
- [ ] Add visual speaking indicators
- [ ] Implement audio waveform visualization
- [ ] Add interrupt button
- [ ] Polish user experience

**Files**:
- `index.html` (major UI update)

#### Step 5.3: RAG Integration
- [ ] Connect to existing Sham RAG system
- [ ] Implement document query routing
- [ ] Add context injection for LLM
- [ ] Test document-aware conversations
- [ ] Optimize retrieval relevance

**Files**:
- `app/llm_service.py` (add RAG integration)
- `app/rag_client.py` (new)

---

### Phase 6: Skill System Implementation
**Goal**: Implement modular skill system from idea.md.

#### Step 6.1: Skill Framework
- [ ] Define skill interface/base class
- [ ] Implement skill registry
- [ ] Add skill loading system
- [ ] Create skill metadata structure
- [ ] Test skill discovery and loading

**Files**:
- `app/skills/base.py` (new)
- `app/skills/registry.py` (new)

#### Step 6.2: Core Skills
- [ ] Implement calendar skill
- [ ] Implement document skill
- [ ] Implement weather skill (integrate Sham)
- [ ] Implement communication skill
- [ ] Test each skill independently

**Files**:
- `app/skills/calendar_skill.py` (new)
- `app/skills/document_skill.py` (new)
- `app/skills/weather_skill.py` (new)
- `app/skills/communication_skill.py` (new)

#### Step 6.3: Skill Router
- [ ] Implement intent classification
- [ ] Add skill matching logic
- [ ] Implement skill execution pipeline
- [ ] Add skill composition (multiple skills)
- [ ] Test complex multi-skill requests

**Files**:
- `app/skills/router.py` (new)

---

### Phase 7: Profession System
**Goal**: Implement profession-aware behavior from idea.md.

#### Step 7.1: Profession Profiles
- [ ] Define profession profile structure
- [ ] Create civil_engineer profile
- [ ] Add profession-specific prompts
- [ ] Implement profession loading
- [ ] Test profession behavior differences

**Files**:
- `app/professions/base.py` (new)
- `app/professions/civil_engineer.py` (new)

#### Step 7.2: Profession Integration
- [ ] Integrate profession with skill router
- [ ] Add profession-specific workflows
- [ ] Implement profession templates
- [ ] Add profession rules engine
- [ ] Test profession-aware responses

**Files**:
- `app/professions/manager.py` (new)

---

### Phase 8: Testing & Optimization
**Goal**: Ensure reliability and performance.

#### Step 8.1: Performance Testing
- [ ] Measure end-to-end latency
- [ ] Test under load
- [ ] Identify bottlenecks
- [ ] Optimize critical paths
- [ ] Set performance targets

#### Step 8.2: Error Handling
- [ ] Add comprehensive error handling
- [ ] Implement graceful degradation
- [ ] Add retry logic
- [ ] Test failure scenarios
- [ ] Add logging and monitoring

#### Step 8.3: User Testing
- [ ] Test with real users
- [ ] Gather feedback
- [ ] Iterate on UX
- [ ] Fix discovered issues
- [ ] Polish experience

---

## Architecture Diagram

### Current Architecture
```
Browser → VAPI → Ram Backend → Sham (Weather)
         ↑       ↑
         |       └─ Calendar, Auth, Profile
         └─ Handles: STT, LLM, TTS, Tools
```

### Target Architecture
```
Browser → Ram Backend (Open Source)
         ↓
    WebSocket Manager
         ↓
    ┌────┴────┬──────────┬──────────┐
    ↓         ↓          ↓          ↓
 STT        LLM        TTS      Skills
(faster-   (Mistral)  (Piper)  (Custom)
Whisper)     ↓          ↓          ↓
          └────┴───────┴──────────┘
                    ↓
              Tool Router
                    ↓
              ┌─────┴─────┐
              ↓           ↓
           Calendar     Sham
              ↓           ↓
           Google      Weather
           Calendar    Intelligence
```

---

## Configuration Requirements

### Environment Variables
```env
# STT Configuration
STT_MODEL_SIZE=small
STT_DEVICE=cpu  # or cuda/mps
STT_LANGUAGE=en

# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=512

# TTS Configuration
TTS_VOICE_MODEL=en_US-lessac-medium
TTS_SAMPLE_RATE=22050
TTS_SPEED=1.0

# Skill Configuration
ENABLE_RAG=true
ENABLE_SKILLS=true
DEFAULT_PROFESSION=civil_engineer
```

---

## Hardware Requirements

### Minimum (Development)
- CPU: 4 cores
- RAM: 16GB
- Storage: 10GB
- GPU: Not required

### Recommended (Production)
- CPU: 8 cores
- RAM: 32GB
- Storage: 20GB SSD
- GPU: NVIDIA GPU with 8GB VRAM (optional but recommended)

---

## Timeline Estimates

### Phase 1: Component Testing (1-2 days)
- STT testing: 4 hours
- LLM testing: 4 hours
- TTS testing: 4 hours
- Integration test: 4 hours

### Phase 2: Real-Time STT (2-3 days)
- STT module update: 1 day
- Streaming WebSocket: 1 day
- Frontend updates: 1 day

### Phase 3: LLM Integration (3-4 days)
- LLM service: 1 day
- Tool calling: 1 day
- Session management: 1 day
- Testing: 1 day

### Phase 4: TTS Integration (2-3 days)
- TTS service: 1 day
- Audio streaming: 1 day
- Frontend audio: 1 day

### Phase 5: Full Pipeline (3-4 days)
- Unified WebSocket: 2 days
- Frontend UI: 1 day
- RAG integration: 1 day

### Phase 6: Skills (4-5 days)
- Skill framework: 1 day
- Core skills: 2 days
- Skill router: 1 day
- Testing: 1 day

### Phase 7: Professions (2-3 days)
- Profession profiles: 1 day
- Integration: 1 day
- Testing: 1 day

### Phase 8: Testing (2-3 days)
- Performance: 1 day
- Error handling: 1 day
- User testing: 1 day

**Total Estimated Time**: 19-27 days

---

## Risk Assessment

### High Risk
- **LLM Latency**: Mistral 7B might be slow on CPU
  - Mitigation: Use smaller model or GPU
- **STT Accuracy**: Faster-whisper might have different accuracy
  - Mitigation: Fine-tune with existing STT lab

### Medium Risk
- **TTS Quality**: Piper might sound robotic
  - Mitigation: Test multiple voices, fallback to XTTS
- **WebSocket Stability**: Real-time streaming might be unstable
  - Mitigation: Add reconnection logic, fallback to HTTP

### Low Risk
- **Integration Complexity**: Many moving parts
  - Mitigation: Incremental testing, good logging

---

## Success Criteria

### Phase 1 Success
- All components tested independently
- Pipeline latency < 3 seconds
- Accuracy comparable to VAPI

### Phase 2 Success
- Real-time transcription working
- Latency < 500ms for STT
- UI updates smoothly

### Phase 3 Success
- Tool calling works correctly
- Conversation memory functional
- LLM responses coherent

### Phase 4 Success
- TTS audio quality acceptable
- Synthesis latency < 300ms
- Audio streaming stable

### Phase 5 Success
- Full conversation flow working
- User can interrupt AI
- RAG integration functional

### Phase 6 Success
- Skills system modular
- Skill routing accurate
- Multiple skills composable

### Phase 7 Success
- Profession behavior different
- Context-aware responses
- Templates working

### Phase 8 Success
- Performance targets met
- Error handling robust
- User feedback positive

---

## Next Steps

**Immediate Action**: Start Phase 1.1 - Test Faster-Whisper STT

**Command**: 
```bash
cd voice-scheduling-agent
pip install faster-whisper
# Create test script
```

**Priority Order**:
1. Phase 1: Component Testing (Validate choices)
2. Phase 2: Real-Time STT (Critical path)
3. Phase 3: LLM Integration (Core intelligence)
4. Phase 4: TTS Integration (Voice output)
5. Phase 5: Full Pipeline (Integration)
6. Phase 6: Skills (Advanced features)
7. Phase 7: Professions (Differentiation)
8. Phase 8: Testing (Quality assurance)

---

## Notes

- Keep VAPI integration as fallback during migration
- Test each phase thoroughly before moving to next
- Document any deviations from this plan
- Update this tracker as we learn more
- Consider creating feature branches for each phase
