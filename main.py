from flask import Flask, request, jsonify, render_template, session
import google.generativeai as genai
from dotenv import load_dotenv
import os
import re
import time
import json
import psycopg2
from psycopg2.extras import Json
from datetime import datetime
from conversation_logic import ConversationSession
from data_loader import load_unit, list_available_units

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
app.secret_key = os.urandom(24)

model = genai.GenerativeModel("gemini-1.5-flash") # Dùng bản ổn định nhất cho giáo dục

# --- Database Helpers ---
def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def save_student_result(student_name, student_class, unit_number, unit_title, qa_pairs, score_percentage):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO student_results 
            (student_name, student_class, unit_number, unit_title, total_questions, correct_answers, score_percentage, qa_pairs)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (student_name, student_class, unit_number, unit_title, len(qa_pairs),
              sum(1 for q in qa_pairs if q.get("score", 0) >= 60), score_percentage, Json(qa_pairs)))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving result: {e}")
        return False

# --- Core Logic ---
def evaluate_with_gemini(student_answer, question, student_name):
    """Hàm 'não bộ' soi lỗi khắt khe và chấm điểm 100"""
    prompt = f"""You are E-Mate, a strict English Teacher. Fix grammar and score the answer.
    Question: "{question}"
    Student: {student_name}
    Answer: "{student_answer}"

    Rules:
    - Score 0-100 based on grammar & relevance.
    - If answer is too short (under 3 words), score < 40.
    - Identify specific grammar mistakes in Vietnamese.
    - Provide a 'Better Answer' based on the student's original idea.

    Format:
    Score: [number 0-100]
    Grammar: [Lỗi sai bằng tiếng Việt]
    Better Answer: [Câu sửa lại chuẩn]
    Explanation: [Giải thích ngắn gọn]"""

    try:
        response = model.generate_content(prompt)
        text = response.text
        
        # Tách dữ liệu từ phản hồi của AI
        score = int(re.search(r"Score:\s*(\d+)", text).group(1)) if re.search(r"Score:\s*(\d+)", text) else 50
        grammar = re.search(r"Grammar:\s*(.*)", text).group(1) if re.search(r"Grammar:\s*(.*)", text) else "Không rõ lỗi."
        better = re.search(r"Better Answer:\s*(.*)", text).group(1) if re.search(r"Better Answer:\s*(.*)", text) else student_answer
        explain = re.search(r"Explanation:\s*(.*)", text).group(1) if re.search(r"Explanation:\s*(.*)", text) else ""
        
        return {"score": score, "grammar": grammar, "better": better, "explain": explain}
    except:
        return {"score": 50, "grammar": "Lỗi kết nối AI", "better": student_answer, "explain": ""}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/units/list", methods=["GET"])
def list_units():
    units = []
    for unit_num in list_available_units():
        unit_data = load_unit(unit_num)
        if unit_data:
            units.append({"unit": unit_num, "title": unit_data.get("title", "")})
    return jsonify({"units": units})

@app.route("/units/start", methods=["POST"])
def start_unit():
    data = request.get_json()
    unit_number = data.get("unit", 1)
    student_name = data.get("student_name", "Anonymous")
    student_class = data.get("student_class", "")

    session["unit_number"] = unit_number
    session["student_name"] = student_name
    session["student_class"] = student_class
    session["qa_history"] = []
    session["scores"] = []
    
    conv_session = ConversationSession(unit_number)
    return jsonify({"unit": unit_number, "title": conv_session.get_title(), "question": conv_session.get_current_question()})

@app.route("/units/answer", methods=["POST"])
def process_unit_answer():
    data = request.get_json()
    student_answer = data.get("answer", "")
    
    # Khôi phục session
    unit_num = session.get("unit_number")
    student_name = session.get("student_name")
    qa_history = session.get("qa_history", [])
    scores = session.get("scores", [])

    conv_session = ConversationSession(unit_num)
    conv_session.qaHistory = qa_history # Đồng bộ lịch sử
    current_q = conv_session.get_current_question()

    # AI chấm điểm và sửa lỗi
    eval_res = evaluate_with_gemini(student_answer, current_q, student_name)
    
    # Lưu vào lịch sử
    scores.append(eval_res["score"])
    qa_history.append({
        "question": current_q,
        "answer": student_answer,
        "score": eval_res["score"]
    })

    # Tiến tới câu tiếp theo
    result = conv_session.process_answer(student_answer)
    
    # Cập nhật session
    session["qa_history"] = qa_history
    session["scores"] = scores

    # Kiểm tra hoàn thành bài để lưu DB
    if result["completed"]:
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0
        save_student_result(student_name, session.get("student_class"), unit_num, conv_session.get_title(), qa_history, avg_score)

    return jsonify({
        "score": eval_res["score"],
        "grammar_errors": eval_res["grammar"],
        "better_answer": eval_res["better"],
        "explanation": eval_res["explain"],
        "next_question": result["next_question"],
        "completed": result["completed"]
    })

# Giữ nguyên các hàm bổ trợ khác của chị bên dưới...
@app.route("/api/stats", methods=["GET"])
def get_stats():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*), COUNT(DISTINCT student_name), AVG(score_percentage), COUNT(DISTINCT unit_number) FROM student_results")
        row = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({"total_sessions": row[0], "total_students": row[1], "avg_score": float(row[2] or 0), "units_used": row[3]})
    except:
        return jsonify({"total_sessions": 0, "total_students": 0, "avg_score": 0, "units_used": 0})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
