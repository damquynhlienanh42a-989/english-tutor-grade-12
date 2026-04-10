import os
import google.generativeai as genai
import json
import re
import random

# Cấu hình AI Gemini
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def evaluate_answer(student_answer, expected_answer):
    """
    Hàm chấm điểm khắt khe, soi lỗi ngữ pháp và đưa ra Better Answer
    """
    prompt = f"""
    Bạn là một giáo viên tiếng Anh bản ngữ đang dạy học sinh lớp 10 Việt Nam. 
    Hãy soi lỗi cực kỳ kỹ lưỡng và chấm điểm khắt khe.

    Câu hỏi/Đáp án mẫu: "{expected_answer}"
    Học sinh trả lời: "{student_answer}"

    Nhiệm vụ của bạn:
    1. SOI LỖI NGỮ PHÁP (BẮT BUỘC): Kiểm tra chia động từ, thì, mạo từ, số ít/số nhiều.
    2. CHẤM ĐIỂM (Thang 10): 
       - 10: Đúng hoàn toàn.
       - 7-9: Đúng ý nhưng sai ngữ pháp nhẹ (ví dụ thiếu 's', sai thì).
       - Dưới 5: Sai cấu trúc câu nghiêm trọng hoặc lạc đề.
    3. Trả về kết quả duy nhất dưới dạng JSON:
    {{
        "score": số_điểm,
        "feedback": "<b>Sửa lỗi:</b> [Chỉ rõ lỗi sai cụ thể] <br><b>Better Answer:</b> [Câu mẫu chuẩn] <br><b>Nhận xét:</b> [Lời khuyên tiếng Việt]"
    }}
    """
    try:
        response = model.generate_content(prompt)
        # Tìm đoạn JSON trong phản hồi của AI
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        result = json.loads(json_match.group())
        
        return {
            'feedback': result.get('feedback', 'Hãy chú ý hơn cấu trúc câu nhé!'),
            'score': float(result.get('score', 0)),
            'is_correct': float(result.get('score', 0)) >= 5
        }
    except:
        return {
            'feedback': "Cô chưa đọc được câu này, em thử diễn đạt lại nhé!",
            'score': 5.0,
            'is_correct': True
        }

def get_encouraging_message():
    """
    Hàm khích lệ học sinh (Cần thiết để hệ thống không bị lỗi Import)
    """
    messages = [
        "Làm tốt lắm, cố gắng phát huy nhé! 🌟",
        "Cô tin em có thể làm tốt hơn ở câu sau! 💪",
        "Sửa lại một chút lỗi nhỏ là hoàn hảo rồi! 🎉",
        "Tuyệt vời! Cùng tiếp tục bài học nào! 🚀",
        "Sắp về đích rồi, cố gắng lên em! 🏆"
    ]
    return random.choice(messages)
