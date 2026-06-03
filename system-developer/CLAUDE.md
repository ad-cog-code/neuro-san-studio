# System Developer — AI-Powered SDLC Pipeline

## THIS PROJECT
Port: 5003
Run: python app/main.py -> http://localhost:5003

## What It Is
A web application where a user types a brief requirement, watches an AI development
team (Neuro SAN multi-agent pipeline) work through the full SDLC, receives shippable
MVP increments with clear run instructions, and provides feedback to iterate.

## Tech Stack
- Flask + Flask-SocketIO (real-time updates)
- SQLite (session/artifact tracking)
- Neuro SAN (multi-agent orchestration via HOCON)
- Bootstrap 5 + vanilla JS

## Agent Network
Registered at: registries/sdlc_pipeline.hocon
Agents: sdlc_orchestrator -> industry_sme -> business_analyst -> product_owner ->
        architect -> frontend_developer -> backend_developer ->
        peer_reviewer -> qa_tester -> business_validator -> technical_writer
