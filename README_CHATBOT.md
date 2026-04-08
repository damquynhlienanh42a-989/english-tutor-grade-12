# English Conversation Practice Chatbot

A unit-based English conversation practice system for Vietnamese Grade 10 students.

## 📁 Project Structure

```
/units/
  unit1.json  - Chores at Home & Describing Family Members
  unit2.json  - Hobbies and Leisure
  unit3.json  - Shopping Problems
  unit4.json  - International Organizations (Charities)
  unit5.json  - Exam Results

/bot/
  main.py               - Main chatbot entry point
  conversation_logic.py - Conversation flow and session management
  data_loader.py        - JSON file loading utilities
  evaluator.py          - Answer comparison and feedback generation
  __init__.py          - Package initializer

run_chatbot.py - Quick launcher script
```

## 🚀 How to Run

### Option 1: Using the launcher script (Recommended)
```bash
python run_chatbot.py
```

### Option 2: Direct execution
```bash
python -m bot.main
```

## 💡 How to Use

1. **Start the chatbot**
   ```
   python run_chatbot.py
   ```

2. **Choose a unit to practice**
   ```
   Type: Practice Unit 1
   (or Unit 2, 3, 4, or 5)
   ```

3. **Answer the questions**
   - Bot will ask questions from the dialogue
   - Type your answers
   - Bot will compare with expected answers
   - Bot will encourage you and give helpful feedback

4. **Complete extra questions**
   - After main dialogue, bot asks 1-2 extra questions
   - These help you practice more freely

5. **Get final feedback**
   - Bot gives you positive encouragement
   - You can practice another unit or quit

## ✨ Features

✅ **5 Complete Units** - Covering different conversation topics
✅ **Smart Answer Evaluation** - Compares your answer with expected response
✅ **Gentle Corrections** - Provides hints without discouragement
✅ **Encouraging Feedback** - Always positive and motivating
✅ **Extra Questions** - Additional practice after main dialogue
✅ **Progress Tracking** - Guides you through each question step-by-step

## 📚 Available Units

- **Unit 1**: Chores at Home & Describing Family Members
- **Unit 2**: Hobbies and Leisure
- **Unit 3**: Shopping Problems
- **Unit 4**: International Organizations (Charities)
- **Unit 5**: Exam Results

## 🎯 Answer Evaluation

The bot compares your answer with the expected answer:

- **85%+ similarity**: "Excellent! Perfect answer! ✅"
- **70-84% similarity**: "Great job! Very close! 👍"
- **50-69% similarity**: Gentle hint provided
- **Below 50%**: Shows expected answer and offers to retry

## 🎓 Example Session

```
🎓 ENGLISH CONVERSATION PRACTICE CHATBOT 🎓

Welcome! I'm here to help you practice English conversations.

Available units:
  • Unit 1: Chores at Home & Describing Family Members
  • Unit 2: Hobbies and Leisure
  • Unit 3: Shopping Problems
  • Unit 4: International Organizations (Charities)
  • Unit 5: Exam Results

To start practicing, type: Practice Unit X (where X is 1-5)

💭 Command: Practice Unit 1

📚 Starting Unit 1: Chores at Home & Describing Family Members

🤖 Bot: Hello! Thank you for joining this short interview...

👤 You: [Your answer here]

💬 Excellent! That's a perfect answer! ✅

🤖 Bot: [Next question...]
```

## 🛠️ Technical Details

### data_loader.py
- Loads JSON files from `/units` folder
- Validates unit data
- Lists available units

### evaluator.py
- Calculates answer similarity using difflib
- Generates feedback based on similarity score
- Provides encouraging messages

### conversation_logic.py
- Manages conversation session state
- Tracks progress through dialogue
- Handles extra questions
- Generates final feedback

### main.py
- Command parsing ("Practice Unit X")
- User interaction loop
- Session management
- Welcome/exit messages

## 🔧 Customization

To add more units:
1. Create `units/unit6.json` following the same format
2. Update `list_available_units()` range in `data_loader.py`
3. The bot will automatically detect and load it!

## 📝 JSON Format

Each unit file follows this structure:
```json
{
  "unit": 1,
  "title": "Unit Title",
  "dialogue": [
    {
      "bot": "Bot's question (EXACT wording preserved)",
      "expected": "Expected student answer"
    }
  ],
  "extra_questions": [
    "Extra question 1",
    "Extra question 2"
  ]
}
```

**Important**: The bot NEVER changes your dialogue wording!

## 🎉 Credits

Created for Vietnamese Grade 10 English conversation practice.
All dialogue content preserved exactly as provided.
