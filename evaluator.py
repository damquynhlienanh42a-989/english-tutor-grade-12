import os
import google.generativeai as genai
import json
import re

# Cấu hình AI
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def evaluate_answer(student_answer, expected_answer):
    if not expected_answer:
        return {'feedback': "", 'is_correct': True, 'similarity': 1.0}

    # Lời nhắc (Prompt) gửi cho Gemini - Ép AI không nói luyên thuyên
    prompt = f"""
    Bạn là một giáo viên tiếng Anh thực tế, KHÔNG nói luyên thuyên.
    Học sinh trả lời: "{student_answer}"
    Đáp án mẫu: "{expected_answer}"

    Nhiệm vụ:
    1. Chỉ nhận xét dựa trên những gì học sinh đã viết. TUYỆT ĐỐI không tự vẽ thêm các tình tiết khác.
    2. Nếu câu đúng: Khen ngắn gọn bằng tiếng Việt.
    3. Nếu câu sai: Sửa lỗi ngữ pháp (Better Answer) sao cho giữ nguyên ý của học sinh nhất có thể.
    4. Trả lời bằng tiếng Việt ở phần giải thích để học sinh dễ hiểu.

    Trả về JSON theo định dạng:
    {{
        "is_correct": true hoặc false,
        "feedback": "Lời nhận xét tiếng Việt + Better Answer: [Câu sửa lỗi sát ý]"
    }}
    """

    try:
        response = model.generate_content(prompt)
        content = response.text
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        result = json.loads(json_match.group())
        
        return {
            'feedback': result.get('feedback', 'Good job! Keep it up.'),
            'is_correct': result.get('is_correct', True),
            'similarity': 1.0 if result.get('is_correct') else 0.5
        }
    except Exception as e:
        return {
            'feedback': "Good try! Let's continue.",
            'is_correct': True,
            'similarity': 0.8
        }

def get_encouraging_message():
    import random
    messages = ["Keep it up! 🌟", "Great work! 💪", "Excellent effort! 🎉"]
    return random.choice(messages)
