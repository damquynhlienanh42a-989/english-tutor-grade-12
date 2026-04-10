import os
from flask import Flask, render_template, request, jsonify, session
from conversation_logic import ConversationSession
import evaluator # Gọi file ở Bước 1

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Danh sách bài học (Chị có thể thêm tiếp ở đây)
UNITS = {
    1: "Family Life", 10: "Ecosystems" 
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/units/list')
def list_units():
    return jsonify({"units": [{"unit": k, "title": v} for k, v in UNITS.items()]})

@app.route('/units/start', methods=['POST'])
def start_unit():
    data = request.json
    unit_num = data.get('unit')
    student_name = data.get('student_name')
    session['unit'] = unit_num
    session['name'] = student_name
    session['scores'] = []
    
    conv = ConversationSession(unit_num)
    return jsonify({"question": conv.get_current_question(), "title": UNITS.get(unit_num)})

@app.route('/units/answer', methods=['POST'])
def handle_answer():
    data = request.json
    ans = data.get('answer')
    unit_num = session.get('unit')
    
    # Khôi phục vị trí câu hỏi
    conv = ConversationSession(unit_num)
    current_scores = session.get('scores', [])
    conv.current_index = len(current_scores)
    
    # Lấy đáp án mẫu để AI chấm
    expected = "" # Có thể lấy từ conv.dialogue nếu có
    
    # Chấm điểm từ Bước 1
    res = evaluator.evaluate_answer(ans, expected)
    current_scores.append(res['score'])
    session['scores'] = current_scores
    
    # Tiến tới câu tiếp
    next_data = conv.process_answer(ans)
    
    # Gửi dữ liệu về Giao diện (Đảm bảo tên ngăn kéo là 'score' và 'feedback')
    return jsonify({
        "score": res['score'],
        "feedback": res['feedback'],
        "next_question": next_data['next_question'],
        "completed": next_data['completed']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
