# English Speaking Practice Chatbot

## Project Overview
An English speaking practice chatbot designed for Vietnamese Grade 10 students. The chatbot helps students practice speaking English about charity topics using voice input/output, provides encouraging feedback, and automatically scores their performance.

## Current State - November 12, 2025
✅ **Fully functional and ready to use**

## Features
1. **Voice Input** - Students can speak their answers using microphone
2. **Voice Output** - Chatbot speaks questions and feedback using default clear voice
3. **Teacher Panel** - Teachers can create and save custom speaking activity questions
4. **Customizable Questions** - Questions stored in questions.json, easily editable
5. **Encouraging Feedback** - Bot gives comments like "Awesome!", "That's great!", "Wonderful!" after each answer
6. **Automatic Scoring** - Evaluates student performance out of 10 points based on:
   - Grammar and vocabulary (0-4 points)
   - Relevance to questions (0-3 points)
   - Completeness of answers (0-3 points)
7. **Personalized Advice** - Provides specific tips for improvement after scoring

## Current Questions (Charity Topic)
1. What is your favourite charity?
2. When was it set up?
3. What is its aim?
4. What work has it done?
5. What else has it done?
6. Why do you like it?

## Technology Stack
- **Backend**: Flask (Python)
- **AI Model**: Google Gemini API (gemini-2.0-flash)
- **Voice Recognition**: Browser Web Speech API
- **Text-to-Speech**: Browser Speech Synthesis API
- **Storage**: JSON file for questions

## API Configuration
- Using Google Gemini API instead of OpenAI (due to quota issues)
- API key stored as `GEMINI_API_KEY` in Replit secrets
- Includes retry logic with exponential backoff for rate limiting

## File Structure
- `main.py` - Flask backend with API routes
- `templates/index.html` - Frontend interface with voice controls
- `questions.json` - Stores teacher's custom questions
- `requirements.txt` - Python dependencies

## Key Routes
- `/` - Main chatbot interface
- `/chat` - Chat endpoint (POST) - processes student responses with AI
- `/questions` - Get/save questions (GET/POST)
- `/get-question` - Get next question in sequence (POST)
- `/evaluate` - Score student's complete activity (POST)

## User Preferences
- Responses must be 1-2 sentences maximum
- Natural, conversational tone (not formal teacher voice)
- Encouraging and positive feedback
- Clear default voice (not baby voice - easier to hear)
- Port 5000 for web server

## Recent Changes (Nov 12, 2025)
- Added teacher panel for managing custom questions
- Implemented automatic scoring system with personalized feedback
- Added varied encouraging comments during conversation
- Optimized voice settings for clarity (default voice, rate 1.1)
- Questions focus on charity topic for Grade 10 curriculum

## How It Works
1. Teacher creates/edits questions in the yellow panel
2. Student clicks "Start Speaking Activity"
3. Chatbot asks questions one by one (speaks them aloud)
4. Student answers by typing or using microphone
5. Bot gives encouraging feedback after each answer
6. After all questions, student receives score + improvement advice
7. All feedback is spoken aloud for better engagement

## Notes
- Chatbot gives short, natural responses to keep students engaged
- Voice is clear default browser voice for easy understanding
- AI provides context-aware encouragement and feedback
- System automatically handles API rate limiting with retries
