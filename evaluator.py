import os
import google.generativeai as genai
import json
import re

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def evaluate_answer(student_answer, expected_answer):
    prompt = f"""
    Bạn là một giáo viên tiếng Anh bản ngữ đang dạy học sinh lớp 10 Việt Nam. 
    Hãy chấm điểm và sửa lỗi cho học sinh một cách chi tiết.

    Câu hỏi/Đáp án mẫu: "{expected_answer}"
    Học sinh trả lời: "{student_answer}"

    Nhiệm vụ của bạn:
    1. Chấm điểm trên thang điểm 10 (chấp nhận số thập phân như 7.5, 8.2).
    2. Kiểm tra lỗi ngữ pháp, từ vựng, cách dùng từ.
    3. Đưa ra một câu trả lời tốt hơn (Better Answer) để học sinh học tập.
    4. Nhận xét bằng tiếng Việt ngắn gọn, khích lệ.

    Trả về kết quả duy nhất dưới dạng JSON:
    {{
        "score": số_điểm,
        "feedback": "Sửa lỗi: ... <br><b>Better Answer:</b> ... <br>Nhận xét: ..."
    }}
    """
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        result = json.loads(json_match.group())
        return {
            'feedback': result.get('feedback', 'Good effort!'),
            'score': float(result.get('score', 0)),
            'is_correct': float(result.get('score', 0)) >= 5
        }
    except:
        return {'feedback': "Keep going!", 'score': 5, 'is_correct': True}
