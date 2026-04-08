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
app.secret_key = os.urandom(24)  # For session management

model = genai.GenerativeModel("gemini-2.0-flash")
model_fallback = genai.GenerativeModel("gemini-2.0-flash-lite")


# Database connection helper
def get_db_connection():
    """Get a connection to the PostgreSQL database."""
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def save_student_result(
    student_name, student_class, unit_number, unit_title, qa_pairs, score_percentage
):
    """Save student result to database."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO student_results
            (student_name, student_class, unit_number, unit_title, total_questions, correct_answers, score_percentage, qa_pairs)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
            (
                student_name,
                student_class,
                unit_number,
                unit_title,
                len(qa_pairs),
                sum(1 for q in qa_pairs if q.get("score", 0) >= 60),
                score_percentage,
                Json(qa_pairs),
            ),
        )

        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving result: {e}")
        return False


# Load questions from file
def load_questions():
    try:
        with open("questions.json", "r", encoding="utf-8") as f:
            return json.load(f)["questions"]
    except:
        return ["What do you do to stay healthy?"]


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/questions", methods=["GET", "POST"])
def questions():
    if request.method == "POST":
        data = request.get_json()
        questions_list = data.get("questions", [])
        # Save questions to file
        with open("questions.json", "w", encoding="utf-8") as f:
            json.dump({"questions": questions_list}, f, ensure_ascii=False, indent=2)
        return jsonify({"success": True})
    else:
        # Get current questions
        return jsonify({"questions": load_questions()})


@app.route("/get-question", methods=["POST"])
def get_question():
    data = request.get_json()
    question_index = data.get("index", 0)
    questions_list = load_questions()

    if question_index < len(questions_list):
        return jsonify({"question": questions_list[question_index], "hasMore": True})
    else:
        return jsonify({"question": None, "hasMore": False})


# ============= UNIT-BASED CONVERSATION ROUTES =============


@app.route("/units/list", methods=["GET"])
def list_units():
    """Get all available units."""
    units = []
    for unit_num in list_available_units():
        unit_data = load_unit(unit_num)
        if unit_data:
            units.append({"unit": unit_num, "title": unit_data.get("title", "")})
    return jsonify({"units": units})


@app.route("/units/start", methods=["POST"])
def start_unit():
    """Start a unit conversation."""
    data = request.get_json()
    unit_number = data.get("unit", 1)
    student_name = data.get("student_name", "Anonymous")
    student_class = data.get("student_class", "")

    # Create new session
    conv_session = ConversationSession(unit_number)

    if not conv_session.is_valid():
        return jsonify({"error": "Invalid unit"}), 400

    # Store session data
    session["unit_number"] = unit_number
    session["student_name"] = student_name
    session["student_class"] = student_class
    session["current_index"] = 0
    session["is_in_extra"] = False
    session["extra_index"] = 0
    session["qa_history"] = []
    session["completed"] = False
    session["scores"] = []
    session["result_saved"] = False

    # Get first question
    first_question = conv_session.get_current_question()

    return jsonify(
        {
            "unit": unit_number,
            "title": conv_session.get_title(),
            "question": first_question,
        }
    )


def _smart_fallback_evaluation(student_answer, expected_answer):
    """Local fallback when all AI models are unavailable. Evaluates based on length and completeness."""
    answer_words = student_answer.strip().split()
    word_count = len(answer_words)
    text = student_answer.strip()

    # --- Verb presence check ---
    has_verb_hint = any(w in text.lower() for w in [
        "is", "are", "was", "were", "have", "has", "do", "does", "did",
        "like", "love", "enjoy", "prefer", "want", "think", "feel",
        "go", "went", "come", "came", "use", "used", "learn", "learned",
        "can", "could", "will", "would", "should", "am", "believe", "allow",
        "make", "makes", "made", "help", "helps", "need", "needs", "know"
    ])

    # --- Detect simple grammar issues ---
    grammar_issues = []
    if text and text[0].islower():
        grammar_issues.append("Câu chưa viết hoa chữ đầu")
    if " i " in f" {text.lower()} " or text.lower().startswith("i "):
        if " I " not in f" {text} " and not text.startswith("I "):
            grammar_issues.append('Đại từ "I" phải viết hoa')
    if not text.endswith((".", "!", "?")):
        grammar_issues.append("Câu chưa có dấu chấm cuối")
    if "don't" in text.lower() or "doesn't" in text.lower() or "isn't" in text.lower():
        pass  # contractions OK
    grammar_errors = ", ".join(grammar_issues) if grammar_issues else "Không phát hiện lỗi rõ ràng."

    # --- Generate Better Answer (improved version of student's own sentence) ---
    # Fix capitalization and punctuation as baseline
    better = text
    if better and better[0].islower():
        better = better[0].upper() + better[1:]
    # Fix standalone lowercase "i"
    better = re.sub(r'\bi\b', 'I', better)
    # Ensure ends with a period
    if better and better[-1] not in ".!?":
        better += "."
    # If very short, suggest an expansion hint
    if word_count < 5:
        better = f"{better} (Thêm: because / so that / which helps me...)"
    elif word_count < 8 and "because" not in better.lower() and "so" not in better.lower():
        better = better.rstrip(".") + ", because it is important for my future."

    # --- Score ---
    if word_count < 3:
        score = 35
        explanation = "Câu quá ngắn, chưa diễn đạt được ý. Hãy nói thành một câu đầy đủ với chủ ngữ và động từ."
    elif word_count < 5:
        score = 55 if has_verb_hint else 42
        explanation = "Câu có ý đúng nhưng còn ngắn. Hãy thêm lý do hoặc ví dụ để câu hoàn chỉnh hơn."
    elif word_count < 8:
        score = 68 if has_verb_hint else 58
        explanation = "Câu đủ ý cơ bản! Thêm một lý do ('because...') sẽ giúp câu trả lời mạnh hơn nhiều."
    elif word_count < 15:
        score = 75 if has_verb_hint else 70
        explanation = "Câu trả lời tốt! Có thể dùng từ nối (however, moreover, therefore) để câu trôi chảy hơn."
    else:
        score = 82
        explanation = "Câu trả lời dài, chi tiết và rõ ràng — rất tốt! Tiếp tục luyện tập để diễn đạt tự nhiên hơn."

    return {
        "score": score,
        "original": student_answer,
        "grammar_errors": grammar_errors,
        "better_answer": better,
        "explanation": explanation,
    }


def _parse_gemini_response(text, student_answer):
    """Parse the structured Gemini response text into new E-Mate format."""
    score = None
    original = student_answer
    grammar_errors = ""
    better_answer = ""
    explanation = ""

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        upper = line.upper()
        if upper.startswith("SCORE:"):
            try:
                score = int("".join(filter(str.isdigit, line.split(":", 1)[1])))
                score = max(0, min(100, score))
            except:
                pass
        elif upper.startswith("ORIGINAL:"):
            original = line.split(":", 1)[1].strip()
        elif "NGỮ PHÁP" in upper or upper.startswith("L\u1ed6I"):
            grammar_errors = line.split(":", 1)[1].strip() if ":" in line else grammar_errors
        elif upper.startswith("BETTER ANSWER:"):
            better_answer = line.split(":", 1)[1].strip()
        elif "GI\u1EA2I TH\u00cdCH" in upper or upper.startswith("GI\u1EA2I"):
            explanation = line.split(":", 1)[1].strip() if ":" in line else explanation

    if score is None:
        return None
    return {
        "score": score,
        "original": original or student_answer,
        "grammar_errors": grammar_errors,
        "better_answer": better_answer or student_answer,
        "explanation": explanation,
    }


def evaluate_and_feedback(
    student_answer, expected_answer, question, student_name, is_extra=False
):
    """
    Use Gemini to score and give detailed feedback on a student's answer.
    Tries gemini-2.0-flash first, then gemini-1.5-flash, then local fallback.
    Returns dict: { 'score': int, 'strengths': str, 'mistakes': str, 'suggestions': str, 'improved': str }
    """
    prompt = f"""You are E-Mate, an AI English Teacher for Vietnamese high school students. Your goal is to evaluate speech, score based on length, and fix grammar mistakes.

Question: "{question}"
Student name: {student_name}
Student's answer: "{student_answer}"

1. SCORING RULES (word count + relevance combined):
   - Under 3 words: Score 0-35 (too short, always low).
   - 3-4 words: Relevant & correct → 52-58. Vague or off-topic → 35-45.
   - 5-7 words: Relevant & correct → 65-72. Vague → 55-62.
   - 8-14 words: Score 72-78.
   - 15 words or more: Score 82+.
   - KEY RULE: A short but clearly relevant and correct answer scores HIGHER than a long irrelevant one. Relevance to the question matters as much as length.

2. EVALUATION & GRAMMAR FIXING:
   - Identify grammar errors (tenses, plural/singular, prepositions, articles, etc.).
   - Provide a Better Answer that is natural and academically correct, based on the student's own ideas.
   - Do NOT replace their answer with a model answer — improve what they actually said.

3. Reply in EXACTLY this format (no extra text):
Score: [number]
Original: {student_answer}
Lỗi ngữ pháp: [Chỉ ra lỗi sai bằng tiếng Việt. Nếu không có lỗi, ghi "Không có lỗi."]
Better Answer: [Phiên bản tiếng Anh đã sửa lỗi và nâng cấp từ vựng dựa trên câu của học sinh]
Giải thích: [Giải thích ngắn gọn bằng tiếng Việt tại sao nên dùng Better Answer]"""

    gen_config = genai.types.GenerationConfig(max_output_tokens=280, temperature=0.7)

    for attempt_model, label in [(model, "gemini-2.0-flash"), (model_fallback, "gemini-1.5-flash")]:
        for attempt in range(2):
            try:
                response = attempt_model.generate_content(prompt, generation_config=gen_config)
                result = _parse_gemini_response(response.text.strip(), student_answer)
                if result:
                    return result
                break  # bad parse but no quota error — don't retry
            except Exception as e:
                err = str(e)
                print(f"Gemini evaluation error ({label}, attempt {attempt+1}): {e}")
                if "429" in err and attempt == 0:
                    time.sleep(3)  # brief wait before retry
                    continue
                break  # not a rate limit error, or second attempt failed

    # All AI calls failed — use smart local fallback
    print("Using local fallback evaluation (all AI models unavailable)")
    return _smart_fallback_evaluation(student_answer, expected_answer)


@app.route("/units/answer", methods=["POST"])
def process_unit_answer():
    """Process student answer in unit conversation."""
    data = request.get_json()
    student_answer = data.get("answer", "")

    # Get session data
    unit_number = session.get("unit_number", 1)
    student_name = session.get("student_name", "Anonymous")
    student_class = session.get("student_class", "")
    current_index = session.get("current_index", 0)
    is_in_extra = session.get("is_in_extra", False)
    extra_index = session.get("extra_index", 0)
    qa_history = session.get("qa_history", [])
    scores = session.get("scores", [])

    # Recreate session
    conv_session = ConversationSession(unit_number)
    conv_session.current_index = current_index
    conv_session.is_in_extra = is_in_extra
    conv_session.extra_index = extra_index
    conv_session.qaHistory = qa_history

    # Get the current question and expected answer BEFORE processing
    current_question_text = conv_session.get_current_question()
    expected_answer = ""
    if not is_in_extra and current_index < len(conv_session.dialogue):
        expected_answer = conv_session.dialogue[current_index].get("expected", "")

    # Process answer (advances indexes)
    result = conv_session.process_answer(student_answer)

    # Get real AI score + personalized feedback
    evaluation = evaluate_and_feedback(
        student_answer=student_answer,
        expected_answer=expected_answer,
        question=current_question_text or "",
        student_name=student_name,
        is_extra=is_in_extra,
    )
    answer_score = evaluation["score"]

    # Track scores across the session
    scores.append(answer_score)

    # Record this Q&A pair into session history
    if current_question_text and not is_in_extra:
        qa_entry = {
            "question": current_question_text,
            "answer": student_answer,
            "score": answer_score,
            "grammar_errors": evaluation.get("grammar_errors", ""),
            "better_answer": evaluation.get("better_answer", ""),
        }
        qa_history.append(qa_entry)

    # Detect when main dialogue just finished (transition into extra questions)
    main_just_completed = (not is_in_extra) and conv_session.is_in_extra

    # Update session
    session["current_index"] = conv_session.current_index
    session["is_in_extra"] = conv_session.is_in_extra
    session["extra_index"] = conv_session.extra_index
    session["completed"] = result["completed"]
    session["scores"] = scores
    session["qa_history"] = qa_history

    # Save result to database when main dialogue finishes OR full completion
    # Use session flag to save only once
    already_saved = session.get("result_saved", False)
    if (main_just_completed or result["completed"]) and not already_saved:
        avg_score = round(sum(scores) / len(scores), 1) if scores else 80.0
        save_student_result(
            student_name=student_name,
            student_class=student_class,
            unit_number=unit_number,
            unit_title=conv_session.get_title(),
            qa_pairs=qa_history,
            score_percentage=avg_score,
        )
        session["result_saved"] = True

    return jsonify(
        {
            "score": answer_score,
            "original": evaluation.get("original", student_answer),
            "grammar_errors": evaluation.get("grammar_errors", ""),
            "better_answer": evaluation.get("better_answer", ""),
            "explanation": evaluation.get("explanation", ""),
            "next_question": result["next_question"],
            "completed": result["completed"],
            "main_completed": main_just_completed,
        }
    )


@app.route("/evaluate", methods=["POST"])
def evaluate():
    data = request.get_json()
    qa_pairs = data.get("qa_pairs", [])

    # Create evaluation prompt
    qa_text = "\n".join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in qa_pairs])

    eval_prompt = f"""
    You are a very supportive and encouraging English teacher celebrating a Grade 10 student's speaking practice.
    
    Student's answers:
    {qa_text}
    
    IMPORTANT: Be MAINLY encouraging! Focus on what they did RIGHT, not mistakes.
    
    Evaluate their STRENGTHS in:
    1. Communication - Did they express their ideas? (0-4 points)
    2. Effort and engagement - Did they try their best? (0-3 points)  
    3. Content - Did they answer the questions? (0-3 points)
    
    Provide encouraging feedback (scores of 7-10 are common - be generous!):
    1. Total score out of 10
    2. Start with VERY enthusiastic celebration like: "Outstanding!", "Amazing work!", "That's fantastic!", 
       "Excellent job!", "Wonderful performance!", "You did great!", "Superb!", "Brilliant!", "Incredible effort!"
    3. 2-3 sentences praising WHAT THEY DID WELL - their vocabulary, effort, ideas, communication, or any strengths
    4. ONE gentle growth tip phrased positively (e.g., "To make your answers even better, try adding more examples!" 
       "Next time, you could describe even more details - you're doing great!")
    5. End with powerful motivation like: "Keep up the excellent work!", "You're becoming a great English speaker!", 
       "I'm so proud of your progress!", "You're doing amazing - keep it up!", "Your English is improving every day!"
    
    Keep it very warm, celebratory, and uplifting (4-5 sentences total). Make students feel PROUD!
    Format: "Score: X/10. [Celebration!] [Praise their strengths]. [Positive growth tip]. [Powerful motivation!]"
    """

    try:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = model.generate_content(
                    eval_prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=200, temperature=0.8
                    ),
                )
                result = response.text.strip()
                return jsonify({"evaluation": result})
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    time.sleep(2**attempt)
                    continue
                raise e
    except Exception as e:
        return jsonify(
            {
                "evaluation": f"Score: 8/10. Fantastic effort! You showed great courage in practicing your English speaking skills. Keep up the amazing work - you're doing wonderfully!"
            }
        )


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        user_message = (data.get("message") or "").strip()

        system_prompt = (
            "You are a very enthusiastic and encouraging English conversation partner for Vietnamese Grade 10 students. "
            "IMPORTANT: Keep responses VERY short - just 1 sentence with encouraging words. "
            "Always start with varied encouraging phrases like: 'Awesome!', 'That's great!', 'Fantastic!', 'Wonderful!', "
            "'Excellent!', 'Well done!', 'Nice job!', 'Perfect!', 'Amazing!', 'Super!', 'Brilliant!', 'Great answer!' "
            "Then add ONE brief positive comment about their answer to motivate them. "
            "Use simple B1 English. Be very enthusiastic, warm, and encouraging to build their confidence."
        )

        # Retry logic for rate limiting
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = model.generate_content(
                    f"{system_prompt}\n\nStudent: {user_message}",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.8, max_output_tokens=100
                    ),
                )
                return jsonify({"reply": response.text})

            except Exception as api_error:
                error_msg = str(api_error)

                # Check if it's a rate limit error
                if "429" in error_msg or "Resource exhausted" in error_msg:
                    if attempt < max_retries - 1:
                        # Wait before retrying (exponential backoff)
                        wait_time = 2**attempt
                        print(
                            f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        return jsonify(
                            {
                                "reply": "I'm receiving too many requests right now. Please wait a few seconds and try again."
                            }
                        ), 429
                else:
                    # Other errors
                    raise api_error

    except Exception as e:
        print("ERROR /chat:", e)
        error_msg = str(e)

        # Provide helpful error messages
        if "429" in error_msg or "Resource exhausted" in error_msg:
            return jsonify(
                {
                    "reply": "Too many requests! Please wait a moment before sending another message."
                }
            ), 429
        else:
            return jsonify(
                {
                    "reply": "Sorry, I couldn't respond due to a server error. Please try again."
                }
            ), 500


@app.route("/results")
def view_results():
    """View all student results (teacher dashboard)."""
    return render_template("results.html")


@app.route("/api/my-results", methods=["GET"])
def get_my_results():
    """Get results for the current session student only."""
    student_name = session.get("student_name", "")
    if not student_name:
        return jsonify({"results": [], "student_name": ""})
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, unit_number, unit_title, total_questions,
                   score_percentage, completed_at
            FROM student_results
            WHERE student_name = %s
            ORDER BY completed_at DESC
        """,
            (student_name,),
        )
        results = []
        for row in cur.fetchall():
            results.append(
                {
                    "id": row[0],
                    "unit_number": row[1],
                    "unit_title": row[2],
                    "total_questions": row[3],
                    "score_percentage": float(row[4]),
                    "completed_at": row[5].strftime("%Y-%m-%d %H:%M"),
                }
            )
        cur.close()
        conn.close()
        return jsonify({"results": results, "student_name": student_name})
    except Exception as e:
        print(f"Error getting my results: {e}")
        return jsonify({"results": [], "student_name": student_name})


@app.route("/api/results", methods=["GET"])
def get_results():
    """Get all student results from database."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, student_name, student_class, unit_number, unit_title, total_questions,
                   correct_answers, score_percentage, completed_at
            FROM student_results
            ORDER BY completed_at DESC
        """)

        results = []
        for row in cur.fetchall():
            results.append(
                {
                    "id": row[0],
                    "student_name": row[1],
                    "student_class": row[2] or "",
                    "unit_number": row[3],
                    "unit_title": row[4],
                    "total_questions": row[5],
                    "correct_answers": row[6],
                    "score_percentage": float(row[7]),
                    "completed_at": row[8].strftime("%d/%m/%Y %H:%M"),
                }
            )

        cur.close()
        conn.close()

        return jsonify({"results": results})
    except Exception as e:
        print(f"Error getting results: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Quick stats for the chatbot homepage."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                COUNT(*) AS total_sessions,
                COUNT(DISTINCT student_name) AS total_students,
                ROUND(AVG(score_percentage)::numeric, 1) AS avg_score,
                COUNT(DISTINCT unit_number) AS units_used
            FROM student_results
        """)
        row = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({
            "total_sessions": int(row[0]),
            "total_students": int(row[1]),
            "avg_score": float(row[2]) if row[2] else 0,
            "units_used": int(row[3]),
        })
    except Exception as e:
        print(f"Stats error: {e}")
        return jsonify({"total_sessions": 0, "total_students": 0, "avg_score": 0, "units_used": 0})


@app.route("/api/results/summary", methods=["GET"])
def get_results_summary():
    """Per-student summary: sessions count, avg score, best score, units done."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                student_name,
                student_class,
                COUNT(*) AS sessions,
                ROUND(AVG(score_percentage)::numeric, 1) AS avg_score,
                MAX(score_percentage) AS best_score,
                COUNT(DISTINCT unit_number) AS units_done,
                MAX(completed_at) AS last_active
            FROM student_results
            GROUP BY student_name, student_class
            ORDER BY last_active DESC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        summary = []
        for r in rows:
            summary.append({
                "student_name": r[0],
                "student_class": r[1] or "",
                "sessions": r[2],
                "avg_score": float(r[3]),
                "best_score": float(r[4]),
                "units_done": r[5],
                "last_active": r[6].strftime("%d/%m/%Y %H:%M"),
            })
        return jsonify({"summary": summary})
    except Exception as e:
        print(f"Error getting summary: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/results/session/<int:session_id>", methods=["GET"])
def get_session_detail(session_id):
    """Get Q&A details for a specific session."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, student_name, student_class, unit_number, unit_title,
                   score_percentage, qa_pairs, completed_at
            FROM student_results WHERE id = %s
        """, (session_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return jsonify({"error": "Not found"}), 404
        return jsonify({
            "id": row[0],
            "student_name": row[1],
            "student_class": row[2] or "",
            "unit_number": row[3],
            "unit_title": row[4],
            "score_percentage": float(row[5]),
            "qa_pairs": row[6] or [],
            "completed_at": row[7].strftime("%d/%m/%Y %H:%M"),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
