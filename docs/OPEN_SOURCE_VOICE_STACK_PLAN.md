# Architecture Decision: Build the Voice Assistant Around LangGraph, Not Pipecat Flows

## Vision

This project is **not** intended to be a simple voice scheduling assistant.

The long-term goal is to build a **general-purpose personal AI assistant** that can:

* Understand the user's work and personal context.
* Maintain long-term memory.
* Execute complex, multi-step reasoning.
* Plan and complete tasks autonomously.
* Install and use downloadable skills/plugins.
* Integrate with external services (Google Calendar, Gmail, GitHub, Slack, Notion, Spotify, etc.).
* Support MCP (Model Context Protocol) servers and external tools.
* Work primarily through a real-time voice interface while remaining extensible to other interfaces.

Because of this vision, the assistant should **not** be architected as a finite-state conversational flow.

---

# Recommendation

Use **LangGraph as the cognitive engine**.

Use **Pipecat only as the real-time voice pipeline**.

Pipecat should handle:

* WebSocket communication
* Audio streaming
* Voice Activity Detection (VAD)
* Speech-to-Text
* Text-to-Speech
* Interruptions (barge-in)
* Audio buffering
* Streaming responses

LangGraph should handle:

* Conversation reasoning
* Planning
* Memory
* Tool selection
* Skill routing
* Multi-step workflows
* Long-running tasks
* Agent state
* Decision making

Pipecat should never become responsible for business logic or planning.

---

# Desired Architecture

```
React Frontend

↓

Pipecat Client

↓

WebSocket

↓

Pipecat Server

↓

STT

↓

LangGraph Assistant

    ├── Planner
    ├── Memory Manager
    ├── Conversation State
    ├── Tool Router
    ├── Skill Registry
    ├── MCP Client
    ├── User Context
    └── Agent Executor

↓

Tools

↓

TTS

↓

User
```

---

# Core Principle

Pipecat is the **voice operating layer**.

LangGraph is the **assistant's brain**.

Every new capability should be implemented as a tool or skill that LangGraph can invoke.

---

# Skills

The assistant should support dynamically adding new capabilities.

Example skills:

* Calendar
* Gmail
* Outlook
* GitHub
* Slack
* Spotify
* Notion
* Google Drive
* File Search
* Web Search
* Weather
* Home Assistant
* MCP Servers

Skills should be modular and independently installable without changing the assistant's core architecture.

The assistant should maintain a registry of available skills and decide at runtime which one to use.

---

# Memory

The assistant should support multiple memory layers.

## Short-Term Memory

Current conversation state.

## Working Memory

Information collected while solving a task.

Example:

* meeting title
* participants
* deadline
* selected repository

## Long-Term Memory

Persistent user knowledge.

Examples:

* preferred meeting duration
* working hours
* favorite coding language
* recurring contacts
* project information
* communication style
* installed skills

---

# Agent Workflow

Instead of fixed conversation nodes, requests should be processed as graphs.

Example:

```
User Request

↓

Understand Intent

↓

Planner

↓

Determine Required Skills

↓

Retrieve Memory

↓

Execute Tools

↓

Validate Result

↓

Generate Response

↓

Speak Response
```

The graph should support loops, retries, branching, waiting for external events, and resuming interrupted work.

---

# Interruptions

Voice interruptions should not destroy agent state.

Example:

User:
"Schedule a meeting with Alex tomorrow."

↓

Assistant starts planning.

↓

User interrupts:

"Actually, what's my next meeting?"

↓

Assistant answers.

↓

Resumes previous scheduling task.

The planning state should remain inside LangGraph while Pipecat only handles the interruption in the audio stream.

---

# Tool Execution

Tools should be stateless whenever possible.

Examples:

* create_calendar_event()
* search_email()
* search_github()
* send_slack_message()
* search_documents()

LangGraph decides when and why to call a tool.

Tools should never make planning decisions.

---

# MCP Support

The architecture should be designed so MCP servers can be added without modifying the core assistant.

Examples:

* GitHub MCP
* Google Drive MCP
* Filesystem MCP
* Browser MCP
* Database MCP

LangGraph should treat MCP servers as additional tool providers.

---

# Design Goals

The architecture should prioritize:

* modularity
* extensibility
* maintainability
* low latency
* clear separation of concerns
* reusable skills
* scalable reasoning
* production readiness

Avoid tightly coupling voice handling with business logic.

---

# What to Avoid

Do not implement the assistant as a collection of Pipecat Flow nodes controlling all business logic.

Do not embed planning logic directly into prompts.

Do not mix voice transport, conversation orchestration, and business logic into the same layer.

Do not create one giant agent with hundreds of tools.

---

# Final Recommendation

Use Pipecat for everything related to voice.

Use LangGraph for everything related to intelligence.

Treat voice as one interface to the assistant—not the architecture itself.

The resulting system should behave like a modular AI operating system where new skills, tools, memories, and reasoning capabilities can be added over time without requiring major architectural changes.

---

# Implementation Notes

* **Phased implementation**: Start with simpler LangGraph agent, add complexity gradually
* **State persistence**: Use Postgres for long-term memory (already available)
* **Skill registry**: Dynamic loading from existing `/app/skills/` structure
* **Hybrid approach**: Simple LangChain agents for basic tasks, LangGraph for complex workflows
* **Performance**: Add caching for frequent queries, optimize graph execution
* **Error handling**: Graceful degradation when tools fail

