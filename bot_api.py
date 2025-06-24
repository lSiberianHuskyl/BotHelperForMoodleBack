
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from g4f.client import Client as G4FClient

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get("DATABASE_URL")

def ask_neural_network(question):
    try:
        client = G4FClient()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты — помощник на курсе по изучению PHP, отвечающий на вопросы кратко и понятно."},
                {"role": "user", "content": f"Ответь на вопрос, не превышая 1000 символов:\n{question}"}
            ],
            stream=False,
        )
        answer = response.choices[0].message.content
        if len(answer) > 1000:
            answer = answer[:1000].rstrip() + "..."
        return answer
    except Exception as e:
        print(f"Ошибка при вызове нейросети: {e}")
        return "Извините, сейчас я не могу дать ответ на этот вопрос."

def find_answer(keywords):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        match_counts = " + ".join([f"(question ILIKE %s)" for _ in keywords])
        sql = f"""
            SELECT question, answer, ({match_counts}) AS match_count
            FROM faq
            WHERE {" OR ".join(["question ILIKE %s" for _ in keywords])}
            ORDER BY match_count DESC
        """
        params = [f"%{word}%" for word in keywords] * 2
        cursor.execute(sql, params)
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        if not results or results[0]['match_count'] == 0:
            return ask_neural_network(" ".join(keywords))

        max_count = results[0]['match_count']
        best_answers = [r['answer'] for r in results if r['match_count'] == max_count]
        return best_answers[0]
    except Exception as e:
        print(f"Ошибка при работе с БД: {e}")
        return "Извините, произошла ошибка."

@app.route('/')
def root():
    return "API работает! 🚀"

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        return '', 204  # отвечает "ОК" на preflight
    data = request.json
    message = data.get('message', '')
    keywords = message.lower().split()
    answer = find_answer(keywords)
    return jsonify({'reply': answer})
