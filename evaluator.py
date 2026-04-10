import os
import google.generativeai as genai
import json
import re
import random

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def evaluate_answer(student_answer, expected_answer):
    # Prompt này ép AI trả về đúng các nhãn mà Giao diện đang đợi
    prompt = f"""
    Bạn là giáo viên Tiếng Anh. Chấm điểm và sửa lỗi câu sau:
    Câu hỏi/Mẫu: {expected_answer}
    Học sinh: {student_answer}
    
    Trả về JSON:
    {{
        "score": số_điểm_0_đến_10,
        "feedback": "<b>Lỗi ngữ pháp:</b> [Sửa lỗi] <br><b>Better Answer:</b> [Câu mẫu hay hơn]"
    }}
    """
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        result = json.loads(json_match.group())
        return {
            'score': result.get('score', 5),
            'feedback': result.get('feedback', 'Good effort!')
        }
    except:
        return {'score': 5, 'feedback': 'Cô chưa đọc được câu này, em thử lại nhé!'}

def get_encouraging_message():
    messages = ["Tuyệt vời! 🔥", "Làm tốt lắm em! 🌟", "Cố gắng lên nào! 💪"]
    return random.choice(messages)
