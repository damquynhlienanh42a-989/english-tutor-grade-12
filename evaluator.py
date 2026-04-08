import difflib

def calculate_similarity(student_answer, expected_answer):
    """
    Calculate similarity between student answer and expected answer.
    
    Args:
        student_answer (str): The student's answer
        expected_answer (str): The expected answer
    
    Returns:
        float: Similarity score (0.0 to 1.0)
    """
    if not expected_answer:
        return 1.0
    
    student_lower = student_answer.lower().strip()
    expected_lower = expected_answer.lower().strip()
    
    similarity = difflib.SequenceMatcher(None, student_lower, expected_lower).ratio()
    return similarity

def evaluate_answer(student_answer, expected_answer):
    """
    Evaluate the student's answer and provide feedback.
    
    Args:
        student_answer (str): The student's answer
        expected_answer (str): The expected answer
    
    Returns:
        dict: Contains 'feedback', 'is_correct', 'similarity'
    """
    if not expected_answer:
        return {
            'feedback': "",
            'is_correct': True,
            'similarity': 1.0
        }
    
    similarity = calculate_similarity(student_answer, expected_answer)
    
    if similarity >= 0.85:
        feedback = "Excellent! That's a perfect answer! ✅"
        is_correct = True
    elif similarity >= 0.70:
        feedback = "Great job! Your answer is very close! 👍"
        is_correct = True
    elif similarity >= 0.50:
        feedback = f"Good try! You're on the right track. Here's a hint: The expected answer is similar to: '{expected_answer}'. Try again or continue!"
        is_correct = False
    else:
        feedback = f"I see what you mean, but let me help you. A better answer would be: '{expected_answer}'. Would you like to try again or move on?"
        is_correct = False
    
    return {
        'feedback': feedback,
        'is_correct': is_correct,
        'similarity': similarity
    }

def get_encouraging_message():
    """Get a random encouraging message."""
    import random
    messages = [
        "You're doing great! Keep going! 🌟",
        "Wonderful progress! 💪",
        "Fantastic effort! 🎉",
        "You're improving with each answer! ⭐",
        "Great work! Keep it up! 🚀"
    ]
    return random.choice(messages)
