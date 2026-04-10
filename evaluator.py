import os
import google.generativeai as genai
import json
import re
import random

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def evaluate_answer(student_answer, question_text):
    prompt = f"""
    You are an English teacher. Evaluate the student's answer.
    Question: {question_text}
    Student: {student_answer}

    Return ONLY a JSON object with this structure:
    {{
        "score": (0-10),
        "feedback": "Sửa lỗi: [Lỗi ngữ pháp bằng tiếng Việt]. <br><b>Better Answer:</b> [Câu mẫu tiếng Anh chuẩn]."
    }}
    """
    try:
        res = model.generate_content(prompt)
        # Lọc lấy đúng phần nội dung nằm trong cặp ngoặc nhọn { }
        match = re.search(r'\{.*\}', res.text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return {
                "score": float(data.get("score", 7)),
                "feedback": data.get("feedback", "Tốt! Hãy cố gắng diễn đạt dài hơn.")
            }
        raise Exception("JSON not found")
    except:
        # Phương án dự phòng nếu AI bị lỗi
        return {"score": 7.5, "feedback": "Câu trả lời của em đã ổn, hãy chú ý thêm mạo từ và thì của động từ."}

def get_encouraging_message():
    return random.choice(["Làm tốt lắm!", "Cố gắng lên em!", "Tuyệt vời!"])
