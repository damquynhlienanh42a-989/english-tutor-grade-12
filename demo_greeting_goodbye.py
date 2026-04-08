#!/usr/bin/env python3
"""
Demo showing the new greeting and goodbye flow
"""

from bot.conversation_logic import ConversationSession

def demo_full_flow():
    """Show the complete flow with greeting and goodbye."""
    print("\n" + "="*70)
    print("DEMO: Complete Conversation Flow (Unit 1)")
    print("="*70 + "\n")
    
    session = ConversationSession(1)
    
    # Show greeting questions
    print("🎯 BEGINNING: Greeting Questions\n")
    print(f"🤖 Bot: {session.get_current_question()}\n")
    print("👤 Student: Hello! My name is Sarah.\n")
    
    result = session.process_answer("Hello! My name is Sarah.")
    print(f"💬 {result['feedback']}\n")
    print(f"🤖 Bot: {result['next_question']}\n")
    
    print("👤 Student: I'm doing well, thank you for asking!\n")
    result = session.process_answer("I'm doing well, thank you for asking!")
    print(f"💬 {result['feedback']}\n")
    print(f"🤖 Bot: {result['next_question']}\n")
    
    # Skip to end
    print("\n" + "─"*70)
    print("... [Main dialogue continues] ...")
    print("─"*70 + "\n")
    
    # Fast forward to extra questions
    while not session.is_in_extra:
        session.process_answer("Sample answer")
    
    # Show extra questions
    print("🎯 EXTRA QUESTIONS:\n")
    
    for i in range(len(session.extra_questions)):
        q = session.get_current_question()
        if q:
            print(f"🤖 Bot: {q}\n")
            
            if i == 2:  # Last one is goodbye
                print("👤 Student: I feel great about this conversation!\n")
                result = session.process_answer("I feel great about this conversation!")
                print(f"💬 {result['feedback']}\n")
                if result['next_question']:
                    print(f"🎉 {result['next_question']}\n")
                break
            else:
                print(f"👤 Student: [Student answers question {i+1}]\n")
                result = session.process_answer("Sample answer")
                print(f"💬 {result['feedback']}\n")
    
    print("="*70)
    print("✅ Conversation Complete!")
    print("="*70 + "\n")

def show_all_units_structure():
    """Show structure of all units."""
    print("\n" + "="*70)
    print("ALL UNITS - UPDATED STRUCTURE")
    print("="*70 + "\n")
    
    for unit_num in range(1, 6):
        session = ConversationSession(unit_num)
        if session.is_valid():
            print(f"📚 Unit {unit_num}: {session.get_title()}")
            print(f"   ✅ Greeting questions: 2 (name + feeling)")
            print(f"   📝 Main dialogue: {len(session.dialogue) - 2} exchanges")
            print(f"   🎯 Extra questions: {len(session.extra_questions) - 1} regular")
            print(f"   👋 Goodbye question: 1 (feeling + goodbye)")
            print()

if __name__ == "__main__":
    show_all_units_structure()
    demo_full_flow()
    
    print("="*70)
    print("🚀 Run the full chatbot: python run_chatbot.py")
    print("="*70 + "\n")
