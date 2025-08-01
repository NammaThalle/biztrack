# Documentation

This directory contains documentation for the Business Tracker Bot.

## Architecture

The bot uses LangGraph for workflow orchestration with automatic memory management through Gemini's chat sessions.

## Key Components

- **LangGraph Workflow**: State-driven workflow with conditional routing
- **Gemini Integration**: Automatic conversation history management
- **Neo4j Storage**: Graph database for business relationships
- **Telegram Integration**: Rich MarkdownV2 formatting 