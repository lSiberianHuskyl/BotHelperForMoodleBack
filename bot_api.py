from flask import Flask, request, jsonify
from flask_cors import CORS  # чтобы разрешить запросы с сайта
import mysql.connector
from mysql.connector import Error
from g4f.client import Client as G4FClient


app = Flask(__name__)
CORS(app)

db_config = {
    'host': 'dpg-d1bq9bodl3ps73eubtc0-a',
    'port': '5432',
    'user': 'faq_db_s4sm_user',
    'password': 'jXmGHOpnySj3B6lzvp4WvJ461g7efUV6',
    'database': 'faq_db_s4sm'
}
def ask_neural_network(question):
    try:
        client = G4FClient()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты — помощник на курсе по изучению PHP, отвечающий на вопросы кратко и понятно."},
                {"role": "user", "content": f"Ответь на вопрос, не превышая 1000 символов:\n{question}"}
            ],
            #max_tokens=1000,  # примерно до 1000 символов (зависит от токенов)
            #temperature=0.7,
            #n=1,
            #stop=None,
            stream = False,
        )
        answer = response.choices[0].message.content,
        #answer = response['choices'][0]['message']['content'].strip()
        if len(answer) > 1000:
            answer = answer[:1000].rstrip() + "..."
        return answer

    except Exception as e:
        print(f"Ошибка при вызове нейросети: {e}")
        return "Извините, сейчас я не могу дать ответ на этот вопрос."

#def ask_neural_network(question):
#    return "Функция ask_neural_network пока не реализована в API."

def find_answer(keywords):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        match_counts = " + ".join([f"(question LIKE %s)" for _ in keywords])
        sql = f"""
            SELECT question, answer, ({match_counts}) AS match_count
            FROM faq
            WHERE { " OR ".join(["question LIKE %s" for _ in keywords]) }
            ORDER BY match_count DESC
        """
        params = [f"%{word}%" for word in keywords] * 2

        cursor.execute(sql, params)
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        if not results:
            question_text = " ".join(keywords)
            return ask_neural_network(question_text)

        max_count = results[0]['match_count']

        if max_count == 0:
            question_text = " ".join(keywords)
            return ask_neural_network(question_text)

        best_answers = [r['answer'] for r in results if r['match_count'] == max_count]
        return best_answers[0]

    except Exception as e:
        print(f"Ошибка при работе с БД: {e}")
        return "Извините, произошла ошибка."
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    keywords = message.lower().split()
    answer = find_answer(keywords)
    return jsonify({'reply': answer})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)





