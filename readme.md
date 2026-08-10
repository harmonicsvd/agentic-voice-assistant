# Agentic Voice Assistant

## 🎯 Project Vision

Build a natural, conversational AI assistant that combines voice interaction with intelligent task execution. Create a seamless hands-free experience where users can interact with various digital services through natural speech. The system is designed to be extensible - users can install different tools, with calendar management being the current implementation.

## 🎯 What This Does

A voice-enabled AI assistant that lets you schedule meetings and check your calendar using natural conversation. Speak naturally to book meetings, ask about your schedule, and manage your calendar without typing.

## 🔗 How It Connects

The voice assistant works with a backend service for tool execution:

```
You Speak → Voice Agent (OAuth) → Backend Service → Google Calendar API → Results → Voice Response
```

**Connection Details:**
- **Backend URL**: `http://127.0.0.1:9000`
- **Authentication**: Internal API key for secure communication
- **Backend Repo**: `agentic-tool-backend-service`
- **Shared Database**: Both services use the same Supabase PostgreSQL instance for user profiles and OAuth tokens
- **Architecture**: Backend service directly calls Google Calendar API using user OAuth tokens (eliminated intermediate API call)

## 🎤 What You Can Do

Users can have natural conversations with the AI assistant. For example:
- "Book a meeting with John tomorrow at 3pm"
- "What meetings do I have today?"
- "Show me my schedule for this week"

### **How It Works:**
1. You speak naturally through the web interface
2. AI understands your intent using LangGraph
3. Voice agent authenticates users via Google OAuth and stores refresh tokens
4. Voice agent calls backend service to execute calendar operations
5. Backend service uses OAuth tokens to directly access Google Calendar API
6. Results are spoken back to you

## 🏗️ Technology Stack

### **Voice & AI:**
- **Pipecat 1.6.0**: Speech-to-speech AI framework for real-time voice processing
- **Whisper STT**: Speech recognition (faster-whisper) for accurate speech-to-text
- **Piper TTS**: Text-to-speech synthesis for natural voice output
- **Groq LLM**: AI reasoning (Llama-3.3-70B-versatile) for intelligent conversation
- **LangGraph**: Conversation orchestration and state management
- **WebSocket**: Real-time bidirectional audio communication via FastAPI WebSocket transport
- **Protobuf Serialization**: Efficient frame serialization for WebSocket communication
- **Silero VAD**: Voice activity detection for speech start/stop detection

### **Backend:**
- **FastAPI**: Web framework
- **Python 3.12**: Async/await patterns
- **PostgreSQL**: User data and profiles (hosted on Supabase)
- **psycopg[binary]**: PostgreSQL database driver
- **Google Calendar API**: Calendar integration
- **Google OAuth**: User authentication

### **Frontend:**
- **React 19**: Modern React with hooks
- **Vite**: Fast build tool
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Pipecat Client**: WebSocket voice communication

##  How to Run

### **Setup**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
```

### **Start Services**
```bash
# Option 1: Start all services at once using the startup script
cd ../
./start-all.sh

# Option 2: Start services individually
# Start voice agent (port 8000)
python -m uvicorn app.main:app --reload

# Start frontend (port 5173)
cd frontend && npm run dev

# Start backend service (port 9000) - in separate terminal
cd ../agentic-tool-backend-service
python -m uvicorn apps.api.main:app --reload
```

### **Environment Variables**
- `DATABASE_URL`: Supabase PostgreSQL connection string (shared with backend)
- `GROQ_API_KEY`: Groq API key for LLM
- `GOOGLE_OAUTH_CLIENT_ID`: Google OAuth client ID (shared with backend)
- `GOOGLE_OAUTH_CLIENT_SECRET`: Google OAuth client secret (shared with backend)
- `APP_SECRET_KEY`: FastAPI secret key
- `INTERNAL_API_KEY`: Internal API key for backend communication (must match backend's `PROFILE_INTERNAL_API_KEY`)
- `WEATHER_AGENT_BASE_URL`: Backend service URL (`http://127.0.0.1:9000`)
- `WEATHER_AGENT_INTERNAL_API_KEY`: Backend service API key (must match backend's `WEATHER_INTERNAL_API_KEY`)

### **Database Setup**
- **Provider**: Supabase (PostgreSQL hosting)
- **Shared Instance**: Both voice assistant and backend service use the same database
- **Purpose**: User profiles, authentication data, OAuth tokens, and application state
- **Note**: Database schema is managed in the backend service (`agentic-tool-backend-service/migrations/`)
- **Important**: Database must include `google_refresh_token` column in `user_profiles` table for backend service to access Google Calendar

## 🌐 Access Points

- **Voice Interface**: `http://localhost:5173/assistant`
- **Login Page**: `http://localhost:5173/login`
- **Profile Setup**: `http://localhost:5173/setup`
- **API Health**: `http://localhost:8000/health`
- **WebSocket Endpoint**: `ws://localhost:8000/ws/pipecat` (real-time voice communication)

## 🔌 WebSocket Communication

**Real-time Voice Pipeline:**
- **Endpoint**: `ws://localhost:8000/ws/pipecat`
- **Transport**: FastAPI WebSocket with Protobuf frame serialization
- **Audio Processing**: 16kHz sample rate, bidirectional audio streaming
- **VAD**: Silero VAD for detecting speech start/stop

**Voice Processing Flow:**
1. Client connects via WebSocket with user authentication
2. Audio streams from client to server (16kHz)
3. Whisper STT converts speech to text in real-time
4. LangGraph processes intent and manages conversation state
5. LLM generates contextual responses
6. Piper TTS converts text to speech
7. Audio streams back to client for playback

## 🔐 Authentication

Uses Google OAuth for secure user authentication:
- Users sign in with their Google account
- Profile setup required before using voice features
- Google Calendar access permissions requested
- OAuth refresh tokens stored in database for backend service access

##  OAuth Token Management

### **Authentication Flow:**
1. User authenticates via voice agent's Google OAuth flow (`/auth/google/login`)
2. Voice agent receives OAuth refresh token from Google
3. Refresh token stored in shared database (`user_profiles.google_refresh_token`)
4. Backend service fetches user profile via internal API when executing tools
5. Backend service uses refresh token to access Google Calendar API directly

### **Security Notes:**
- OAuth tokens are stored securely in the shared database
- Internal API keys protect profile data access
- Google OAuth scopes are limited to calendar access only
- Refresh tokens are preserved during profile updates

## 🏗️ System Architecture

### **Microservices Design:**
The system follows a microservices architecture with clear separation of concerns:

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│  Voice Agent     │────▶│  Backend        │
│   (React)       │     │  (Port 8000)     │     │  Service        │
│   Port 5173     │     │                  │     │  (Port 9000)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │                          │
                                │                          │
                                ▼                          ▼
                        ┌──────────────┐          ┌──────────────┐
                        │ PostgreSQL   │          │ Google       │
                        │ (Supabase)   │          │ Calendar API │
                        └──────────────┘          └──────────────┘
```

### **Component Responsibilities:**
- **Frontend**: User interface, WebSocket client, OAuth initiation
- **Voice Agent**: Authentication, conversation management, voice processing
- **Backend Service**: Tool execution, API integrations, data processing
- **Shared Database**: User profiles, OAuth tokens, application state
- **External Services**: Google Calendar API, OAuth providers

### **Communication Patterns:**
- **Frontend ↔ Voice Agent**: WebSocket for real-time voice, HTTP for authentication
- **Voice Agent ↔ Backend**: HTTP with internal API key authentication
- **Voice Agent ↔ Database**: Direct PostgreSQL connection
- **Backend ↔ Database**: Direct PostgreSQL connection for profile access
- **Backend ↔ External APIs**: Direct HTTP calls with OAuth authentication
