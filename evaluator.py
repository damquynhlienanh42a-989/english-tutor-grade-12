import os
import google.generativeai as genai

# Cấu hình AI
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def evaluate_answer(student_answer, expected_answer):
    if not expected_answer:
        return {'feedback': "", 'is_correct': True, 'similarity': 1.0}

    # Lời nhắc (Prompt) gửi cho Gemini
    prompt = f"""
    Bạn là một giáo viên tiếng Anh bản ngữ. Hãy chấm điểm câu trả lời của học sinh.
    Câu hỏi yêu cầu đáp án tương tự như: "{expected_answer}"
    Học sinh trả lời: "{student_answer}"

    Hãy phản hồi theo định dạng JSON như sau:
    {{
        "is_correct": true hoặc false (chọn true nếu đúng về nghĩa, chấp nhận lỗi nhỏ),
        "feedback": "Nhận xét ngắn gọn bằng tiếng Việt, sửa lỗi ngữ pháp nếu có, khen ngợi nếu hay."
    }}
    Lưu ý: Nếu câu trả lời quá ngắn, hãy nhắc học sinh viết đầy đủ câu.
    """

    try:
        response = model.generate_content(prompt)
        # Lấy kết quả từ AI (đoạn này em đã xử lý để nó lấy đúng JSON)
        import json
        import re
        content = response.text
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        result = json.loads(json_match.group())
        
        return {
            'feedback': result.get('feedback', 'Great job!'),
            'is_correct': result.get('is_correct', True),
            'similarity': 1.0 if result.get('is_correct') else 0.5
        }
    except Exception as e:
        return {
            'feedback': "Great effort! Keep practicing.",
            'is_correct': True,
            'similarity': 0.8
        }

def get_encouraging_message():
    import random
    messages = ["Keep it up! 🌟", "Great work! 💪", "Excellent effort! 🎉"]
    return random.choice(messages)
