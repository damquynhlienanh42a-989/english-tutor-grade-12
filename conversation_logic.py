from bot.data_loader import load_unit
from bot.evaluator import evaluate_answer, get_encouraging_message
import random

class ConversationSession:
    def __init__(self, unit_number):
        """
        Initialize a conversation session for a specific unit.
        
        Args:
            unit_number (int): The unit number to practice
        """
        self.unit_data = load_unit(unit_number)
        self.unit_number = unit_number
        self.current_index = 0
        self.dialogue = self.unit_data['dialogue'] if self.unit_data else []
        self.extra_questions = self.unit_data['extra_questions'] if self.unit_data else []
        self.is_in_extra = False
        self.extra_index = 0
        self.completed = False
        
    def is_valid(self):
        """Check if the session loaded successfully."""
        return self.unit_data is not None
    
    def get_title(self):
        """Get the unit title."""
        return self.unit_data.get('title', '') if self.unit_data else ''
    
    def get_current_question(self):
        """Get the current bot question."""
        if self.is_in_extra:
            if self.extra_index < len(self.extra_questions):
                return self.extra_questions[self.extra_index]
            else:
                return None
        else:
            if self.current_index < len(self.dialogue):
                return self.dialogue[self.current_index]['bot']
            else:
                return None
    
    def process_answer(self, student_answer):
        """
        Process the student's answer and provide feedback.
        
        Args:
            student_answer (str): The student's answer
        
        Returns:
            dict: Contains 'feedback', 'next_question', 'completed'
        """
        if self.is_in_extra:
            # Extra questions don't have expected answers, just accept anything
            self.extra_index += 1
            
            if self.extra_index < len(self.extra_questions):
                return {
                    'feedback': "Thank you for sharing! " + get_encouraging_message(),
                    'next_question': self.extra_questions[self.extra_index],
                    'completed': False
                }
            else:
                # All extra questions done
                self.completed = True
                final_message = self._get_final_feedback()
                return {
                    'feedback': "Thank you for sharing! " + get_encouraging_message(),
                    'next_question': final_message,
                    'completed': True
                }
        
        else:
            # Main dialogue
            if self.current_index >= len(self.dialogue):
                return {'feedback': '', 'next_question': None, 'completed': True}
            
            current_item = self.dialogue[self.current_index]
            expected = current_item['expected']
            
            evaluation = evaluate_answer(student_answer, expected)
            
            self.current_index += 1

            # Auto-skip any closing bot message (expected == "") so student
            # doesn't have to type again — collect the text to prepend instead
            closing_prefix = ""
            while (self.current_index < len(self.dialogue) and
                   self.dialogue[self.current_index].get('expected', None) == ''):
                closing_prefix += self.dialogue[self.current_index]['bot'] + "\n\n"
                self.current_index += 1

            # Check if main dialogue is finished
            if self.current_index >= len(self.dialogue):
                # Move to extra questions
                self.is_in_extra = True
                self.extra_index = 0

                if len(self.extra_questions) > 0:
                    next_q = self.extra_questions[0]
                    return {
                        'feedback': evaluation['feedback'],
                        'next_question': f"{closing_prefix}🎯 Bonus Question:\n\n{next_q}",
                        'completed': False
                    }
                else:
                    # No extra questions
                    self.completed = True
                    final_message = self._get_final_feedback()
                    return {
                        'feedback': evaluation['feedback'],
                        'next_question': closing_prefix + final_message,
                        'completed': True
                    }
            else:
                next_q = self.dialogue[self.current_index]['bot']
                return {
                    'feedback': evaluation['feedback'],
                    'next_question': closing_prefix + next_q if closing_prefix else next_q,
                    'completed': False
                }
    
    def _get_final_feedback(self):
        """Generate final positive feedback."""
        messages = [
            f"🎉 Congratulations! You've completed Unit {self.unit_number}: {self.get_title()}!\n\nYou did an amazing job working through all the questions! Your English conversation skills are improving every day. Keep up the excellent work! 🌟\n\nWould you like to practice another unit? Just type 'Practice Unit X' (where X is 1-5)!",
            
            f"🌟 Fantastic work! You've finished Unit {self.unit_number}: {self.get_title()}!\n\nYour dedication and effort really show! You're making great progress in your English speaking abilities. I'm so proud of you! 💪\n\nReady for more practice? Type 'Practice Unit X' to start another unit!",
            
            f"👏 Excellent! You've successfully completed Unit {self.unit_number}: {self.get_title()}!\n\nYour responses were thoughtful and well-expressed. You're becoming more confident with English conversation! Keep practicing and you'll continue to improve! 🚀\n\nFeel free to practice another unit whenever you're ready!"
        ]
        return random.choice(messages)
