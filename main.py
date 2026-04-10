import os
from flask import Flask, render_template, request, jsonify, session
from conversation_logic import ConversationSession
from data_loader import load_unit, list_available_units
import evaluator

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/units/list')
def list_units():
    # Trả về đầy đủ các Unit có trong dữ liệu
    units = []
    for u_num in sorted(list_available_units()):
        u_data = load_unit(u_num)
        if u_data:
            units.append({"unit": u_num, "title": u_data.get("title", f"Unit {u_num}")})
    return jsonify({"units": units})

@app.route('/units/start', methods=['POST'])
def start():
    data = request.json
    unit_num = data.get('unit')
    session['unit'] = unit_num
    session['name'] = data.get('student_name')
    session['history_count'] = 0 # Đếm số câu đã làm
    session['scores'] = []
    
    conv = ConversationSession(unit_num)
    return jsonify({"question": conv.get_current_question(), "title": conv.get_title()})

@app.route('/units/answer', methods=['POST'])
def answer():
    data = request.json
    ans = data.get('answer', '')
    unit_num = session.get('unit')
    
    conv = ConversationSession(unit_num)
    # Khôi phục đúng vị trí dựa trên số câu đã trả lời
    count = session.get('history_count', 0)
    conv.current_index = count
    
    current_q = conv.get_current_question()
    
    # AI chấm điểm và sửa lỗi ngữ pháp chuẩn
    res = evaluator.evaluate_answer(ans, current_q)
    
    # Cập nhật điểm và số câu
    scores = session.get('scores', [])
    scores.append(res['score'])
    session['scores'] = scores
    session['history_count'] = count + 1
    
    # Tiến tới câu tiếp theo
    next_step = conv.process_answer(ans)
    
    return jsonify({
        "score": res['score'],
        "feedback": res['feedback'],
        "next_question": next_step['next_question'],
        "completed": next_step['completed']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
