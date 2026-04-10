import os
import psycopg2
from flask import Flask, render_template, request, jsonify, session
from psycopg2.extras import Json
from conversation_logic import ConversationSession
from data_loader import load_unit, list_available_units
import evaluator

app = Flask(__name__)
# Sử dụng Secret Key từ Environment hoặc tạo ngẫu nhiên để bảo mật session
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

def save_to_db(name, unit, score, history):
    try:
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            print("DB Error: DATABASE_URL not found")
            return
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO student_results (student_name, unit_number, score_percentage, qa_pairs) 
            VALUES (%s, %s, %s, %s)
        """, (name, unit, score * 10, Json(history)))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e: 
        print(f"DB Error: {e}")

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/units/list')
def list_units():
    units = [{"unit": u, "title": load_unit(u).get("title", f"Unit {u}")} for u in sorted(list_available_units())]
    return jsonify({"units": units})

@app.route('/units/start', methods=['POST'])
def start():
    data = request.json
    session['unit'] = data.get('unit')
    session['name'] = data.get('student_name')
    session['history'] = []
    conv = ConversationSession(data.get('unit'))
    return jsonify({"question": conv.get_current_question(), "title": conv.get_title()})

@app.route('/units/answer', methods=['POST'])
def answer():
    data = request.json
    ans = data.get('answer', '')
    unit_num = session.get('unit')
    
    conv = ConversationSession(unit_num)
    history = session.get('history', [])
    conv.current_index = len(history)
    current_q = conv.get_current_question()
    
    # AI sẽ chấm điểm và trả về feedback Tiếng Anh dựa trên file evaluator.py mới
    res = evaluator.evaluate_answer(ans, current_q)
    
    history.append({"q": current_q, "a": ans, "s": res['score']})
    session['history'] = history
    
    next_step = conv.process_answer(ans)
    
    if next_step['completed']:
        if len(history) > 0:
            avg = sum(h['s'] for h in history) / len(history)
            save_to_db(session.get('name'), unit_num, avg, history)

    return jsonify({
        "score": res['score'],
        "feedback": res['feedback'],
        "next_question": next_step['next_question'],
        "completed": next_step['completed']
    })

if __name__ == '__main__':
    # Render yêu cầu host 0.0.0.0 và port 5000 hoặc theo biến môi trường PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
