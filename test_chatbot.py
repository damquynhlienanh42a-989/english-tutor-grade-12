#!/usr/bin/env python3
"""
Quick test script to demonstrate the chatbot functionality
"""

from bot.conversation_logic import ConversationSession
from bot.data_loader import list_available_units

def demo_unit_1():
    """Demonstrate Unit 1 conversation flow."""
    print("\n" + "="*60)
    print("DEMO: Unit 1 - Chores at Home & Describing Family Members")
    print("="*60 + "\n")
    
    session = ConversationSession(1)
    
    if not session.is_valid():
        print("❌ Failed to load Unit 1")
        return
    
    print(f"📚 Unit Title: {session.get_title()}\n")
    
    # Simulate a few answers
    test_answers = [
        "I usually wash the dishes and tidy my bedroom.",
        "I wash the dishes six times a week, except Sunday.",
        "I tidy my bedroom twice a week."
    ]
    
    # First question
    q = session.get_current_question()
    print(f"🤖 Bot: {q}\n")
    
    for i, answer in enumerate(test_answers):
        print(f"👤 Student: {answer}\n")
        
        result = session.process_answer(answer)
        
        if result['feedback']:
            print(f"💬 Feedback: {result['feedback']}\n")
        
        if result['next_question'] and not result['completed']:
            print(f"🤖 Bot: {result['next_question']}\n")
        
        if i >= 2:  # Just show first 3 exchanges
            break
    
    print("\n✅ Demo complete! The bot continues through all dialogue and extra questions.\n")

def show_all_units():
    """Show all available units."""
    print("\n" + "="*60)
    print("AVAILABLE UNITS")
    print("="*60 + "\n")
    
    units = list_available_units()
    
    for unit_num in units:
        session = ConversationSession(unit_num)
        if session.is_valid():
            print(f"📚 Unit {unit_num}: {session.get_title()}")
            print(f"   - Main dialogue: {len(session.dialogue)} exchanges")
            print(f"   - Extra questions: {len(session.extra_questions)}")
            print()

if __name__ == "__main__":
    print("\n🎓 CHATBOT TEST & DEMONSTRATION 🎓\n")
    
    show_all_units()
    demo_unit_1()
    
    print("="*60)
    print("To run the full interactive chatbot:")
    print("  python run_chatbot.py")
    print("="*60 + "\n")
