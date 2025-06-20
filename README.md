# 82ndDrop

**Create stunning, fast, AI-powered videos — in just a few seconds.**

## Overview

82ndDrop is an AI-powered service that helps creators rapidly generate 8-second TikTok-style videos using guided prompts. Users describe what they want to make, and our multi-agent system returns 3 crafted prompts — one for the center video (main content), one for the top (context or teaser), and one for the bottom (text reenactment or subtitle style). These prompts can be used directly in tools like Gemini, Sora, or any video editor. This MVP phase focuses on delivering the prompts only — full video generation and stitching will come in a later version.

## Tech Stack

- **Frontend:** Angular 19 (with Angular Material)
- **Backend:** Firebase (Firestore, Functions, Auth)
- **AI Models:** Gemini, Veo, Sora
- **Agent Framework:** Google ADK (Agent Development Kit)

## Agents

- `Guide Agent`: Helps shape initial ideas into viable video concepts
- `TaskMaster Agent`: Breaks down tasks for video generation
- `Search Agent`: Finds references or creative inspiration
- `PromptWriter Agent`: Crafts prompts for Gemini/Veo/Sora

## Submission Goals (ADK Hackathon)

- [ ] Live demo (Firebase hosted)
- [ ] GitHub repo (this one!)
- [ ] Public demo video
- [ ] Architecture diagram
- [ ] Multi-agent system working in production
- [ ] MVP: Prompt-only system that generates 3-part video scripts (top, center, bottom)
- [ ] Future: Full in-app video generation using Gemini/Sora APIs as they become available
