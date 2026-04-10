import os
import google.generativeai as genai
import re
import random

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def evaluate_answer(student_answer, question_text):
    prompt = f"""You are an English teacher. Evaluate this:
    Question: {question_text}
    Student: {student_answer}
    
    1. Score: 0-10.
    2. Feedback: Chỉ rõ lỗi ngữ pháp bằng tiếng Việt và đưa ra Better Answer.
    
    Format:
    Score: [số]
    Feedback: [nội dung]"""
    
    try:
        res = model.generate_content(prompt)
        text = res.text
        # Tìm điểm số
        score_val = re.search(r"Score:\s*([\d\.]+)", text)
        score = float(score_val.group(1)) if score_val else 7.0
        # Tìm nhận xét
        feedback_val = re.search(r"Feedback:\s*(.*)", text, re.DOTALL)
        feedback = feedback_val.group(1).strip() if feedback_val else "Good effort!"
        return {"score": score, "feedback": feedback}
    except:
        return {"score": 7.0, "feedback": "Em đã hoàn thành tốt câu hỏi này!"}

def get_encouraging_message():
    return random.choice(["Great!", "Well done!", "Keep it up!"])
