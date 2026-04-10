import google.generativeai as genai
import os

# Cấu hình Gemini API
# Lưu ý: Bạn phải thêm GEMINI_API_KEY vào 'Secrets' trên Replit hoặc 'Environment Variables' trên Render
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def evaluate_answer(answer, question):
    prompt = f"""
    You are an AI English Teacher for Grade 10-12 students.
    
    Task: Evaluate the student's answer based on the given question.
    Question: "{question}"
    Student's Answer: "{answer}"
    
    Instructions:
    1. Score: 0.0 to 10.0 (Consider grammar, vocabulary, and relevance).
    2. Feedback: MUST BE IN ENGLISH. 
    3. No Repetition: Do NOT use generic praise like "Great idea". Be specific.
    4. Structure:
       - Point out a specific grammar/spelling mistake.
       - Provide a 'Suggested sentence' that is more natural.

    Return EXACTLY in this format:
    Score: [number]
    Feedback: [Your specific English feedback]
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        
        # Xử lý chuỗi để lấy Score và Feedback
        score = 5.0
        feedback = "Good effort! Try to write a longer sentence."
        
        if "Score:" in text and "Feedback:" in text:
            score_str = text.split("Score:")[1].split("Feedback:")[0].strip()
            # Loại bỏ các ký tự lạ nếu có
            score = float(''.join(c for c in score_str if c.isdigit() or c == '.'))
            feedback = text.split("Feedback:")[1].strip()
            
        return {"score": score, "feedback": feedback}
    except Exception as e:
        print(f"Error in evaluator: {e}")
        return {"score": 5.0, "feedback": "Nice try! Let's practice more on this topic."}
