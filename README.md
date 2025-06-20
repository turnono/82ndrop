# 82nDrop

**Create stunning, fast, AI-powered videos — in just a few seconds.**

## Overview

82nDrop is an AI-powered service that helps creators rapidly generate 8-second TikTok-style videos using guided prompts. Users describe what they want to make, and our multi-agent system returns 3 crafted prompts — one for the center video (main content), one for the top (context or teaser), and one for the bottom (text reenactment or subtitle style). These prompts can be used directly in tools like Gemini, Sora, or any video editor. This MVP phase focuses on delivering the prompts only — full video generation and stitching will come in a later version.

In the MVP phase, there is no use of memory or persistent storage for agent interactions. All processing is stateless and happens per request, with the results returned in a simple JSON format containing top, center, and bottom prompts. Memory handling and session continuity may be introduced in future versions.

## Tech Stack

- **Frontend:** Angular 19 (with Angular Material)
- **Backend:** Firebase (Firestore, Functions, Auth)
- **AI Models:** Gemini, Veo, Sora
- **Agent Framework:** Google ADK (Agent Development Kit)

## Agents

- `TaskMaster Agent`: Coordinates the overall pipeline for prompt generation
- `Guide Agent`: Shapes the initial user input into a structured video idea
- `Search Agent`: Enriches the idea with relevant inspiration or reference material
- `PromptWriter Agent`: Crafts three output prompts (top, center, bottom)

## Output Format

Each request returns a simple structured payload:

```json
{
  "top": "...",
  "center": "...",
  "bottom": "..."
}
```

This structure allows the frontend to immediately display or export the prompt triplet for manual use in Gemini, Sora, or other video-generation tools.

## 🔧 Prompt Schema Design (MVP)

The prompt generation pipeline is designed around a flexible schema that captures the essential components for generating compelling short-form videos. The system uses the following key elements to build the top/center/bottom prompt triplet:

### 🧠 Core Prompt Components

1. **Character / Subject**

   - Description of who is featured: person, animal, AI, or fictional character.
   - Attributes: voice/accent, attitude, background, role (e.g., vlogger, prisoner, consultant).

2. **Scene / Setting**

   - Where it takes place: physical location, mood, props, and time of day.

3. **Visual Style**

   - Look and feel: cinematic, cartoon, podcast-style, mockumentary, selfie-cam, etc.

4. **Purpose / Action**
   - What is happening or being said: monologue, dialogue, announcement, commentary, etc.

### 🎥 Use Case Variants

Depending on the selected video type (e.g., vlogging, movie remake, gorilla podcast), the system will bias the generation with predefined context templates — but the user can override any element manually.

| Type               | Extra Features Considered                            |
| ------------------ | ---------------------------------------------------- |
| Vlogging           | Eye contact, selfie-style framing, personal tone     |
| Gorilla Podcast    | All characters gorillas, podcast mics, casual banter |
| Movie Remakes      | Known characters/scenes, dramatic storytelling       |
| Business Explainer | Clear messaging, product or service framing          |
| AI Satire          | Meta-awareness, glitch/humor styling                 |

### 🛠️ User Overrides

Users can inject their own input at any point in the process. The system is designed to accept partial or full overrides of the generated suggestions for character, setting, style, or intent — allowing for creative freedom and fine-tuning.

## Submission Goals (ADK Hackathon)

- [ ] Live demo (Firebase hosted)
- [ ] GitHub repo (this one!)
- [ ] Public demo video
- [ ] Architecture diagram
- [ ] Multi-agent system working in production
- [ ] MVP: Prompt-only system that generates 3-part video scripts (top, center, bottom)
- [ ] Future: Full in-app video generation using Gemini/Sora APIs as they become available
