import os
import google.generativeai as genai
import json
import re

# Cấu hình AI Gemini
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def evaluate_answer(student_answer, expected_answer):
    if not expected_answer:
        return {'feedback': "Tốt lắm!", 'is_correct': True, 'score': 10}

    # Lời nhắc (Prompt) cực kỳ chi tiết để AI soi lỗi ngữ pháp lớp 10
    prompt = f"""
    Bạn là một giáo viên tiếng Anh chuyên nghiệp đang chấm bài cho học sinh lớp 10.
    Hãy soi lỗi cực kỳ kỹ lưỡng và chấm điểm khắt khe.

    Câu hỏi yêu cầu ý chính: "{expected_answer}"
    Học sinh trả lời: "{student_answer}"

    Nhiệm vụ của bạn:
    1. SOI LỖI NGỮ PHÁP (BẮT BUỘC): Kiểm tra chia động từ (số ít/số nhiều), thì của động từ, mạo từ (a/an/the), danh từ số nhiều, và lỗi viết hoa/dấu câu.
    2. CHẤM ĐIỂM (Thang 10): 
       - 10: Đúng hoàn toàn, không sai dù chỉ 1 dấu phẩy.
       - 8-9: Đúng ý nhưng sai 1 lỗi ngữ pháp nhỏ (ví dụ: thiếu 's', quên viết hoa).
       - 5-7: Sai cấu trúc câu hoặc sai nhiều lỗi chính tả nhưng vẫn hiểu được ý.
       - Dưới 5: Sai hoàn toàn ngữ pháp hoặc trả lời lạc đề.
    3. PHẢN HỒI (Tiếng Việt):
       - Phải chỉ rõ em đã sai ở đâu (Ví dụ: "Em quên chia động từ 'like' thành 'likes'").
       - Đưa ra "Better Answer" là câu sửa lại hoàn chỉnh, tự nhiên.

    Trả về JSON định dạng sau:
    {{
        "score": số_điểm,
        "feedback": "Nhận xét tiếng Việt cụ thể lỗi sai. Better Answer: [Câu sửa lại chuẩn]"
    }}
    """

    try:
        response = model.generate_content(prompt)
        # Lọc lấy phần JSON trong phản hồi của AI
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        result = json.loads(json_match.group())
        
        return {
            'feedback': result.get('feedback', 'Keep it up!'),
            'score': result.get('score', 0),
            'is_correct': result.get('score', 0) >= 5
        }
    except Exception as e:
        # Trường hợp lỗi, trả về điểm trung bình
        return {
            'feedback': "Cố gắng lên em nhé! Hãy chú ý ngữ pháp hơn.",
            'score': 5.0,
            'is_correct': True
        }

def get_encouraging_message():
    import random
    messages = [
        "Làm tốt lắm, cố gắng phát huy nhé! 🌟",
        "Cô tin em có thể làm tốt hơn ở câu sau! 💪",
        "Sửa lại một chút lỗi nhỏ là hoàn hảo rồi! 🎉"
    ]
    return random.choice(messages)
