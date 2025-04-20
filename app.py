from flask import Flask, render_template, request, jsonify, send_from_directory
from groq import Groq
import mysql.connector
import os
import base64
import re

app = Flask(__name__)

client = Groq(api_key="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")

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='rkarthik9140@',
        database='herbal_db'
    )

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/chat')
def chatbot():
    return render_template('chatbot_page.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        search_query = request.form['search']
        sql = """
            SELECT d.name, d.medicinal_plants, d.natural_excipients, di.image_path
            FROM drug d
            LEFT JOIN drugimg di ON d.drug_id = di.drug_id
            WHERE d.name LIKE %s
        """
        cursor.execute(sql, (f"%{search_query}%",))
    else:
        sql = """
            SELECT d.name, d.medicinal_plants, d.natural_excipients, di.image_path
            FROM drug d
            LEFT JOIN drugimg di ON d.drug_id = di.drug_id
        """
        cursor.execute(sql)

    rows = cursor.fetchall()
    for row in rows:
        name, plants, excipients, image_path = row
        results.append({
            'name': name,
            'plants': plants,
            'excipients': excipients,
            'image_path': image_path
        })

    cursor.close()
    conn.close()
    return render_template('search.html', results=results)

@app.route('/static/<path:filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/chat", methods=["POST"])
def chat_message():
    user_msg = request.json["message"]
    tablet_name = user_msg.strip().capitalize()

    messages = [
        {"role": "system", "content": "You are a helpful herbal guide."},
        {"role": "user", "content": user_msg}
    ]

    try:
        response_llm = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages
        )
        raw_reply = response_llm.choices[0].message.content.strip()
        formatted_reply = re.sub(r'- ', '🔸 ', raw_reply).replace('\n', '<br>')
        response = f"<b>Learn:</b><br>{formatted_reply}<br><hr>"

    except Exception as e:
        response = f"Sorry, LLaMA response failed. Error: {str(e)}"
        return jsonify({"reply": response})

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM HerbalAlternatives WHERE tablet_name LIKE %s", (f"%{tablet_name}%",))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        image_base64 = base64.b64encode(result["image"]).decode("utf-8")
        db_info = (
            f"<b>📦 Tablet Name:</b> {result['tablet_name']}<br>"
            f"<b>🌿 Herbal Alternatives:</b> {result['herbal_alternatives']}<br>"
            f"<b>🍃 Natural Excipients:</b> {result['natural_excipients']}<br><br>"
            f"<img src='data:image/jpeg;base64,{image_base64}' width='200'>"
        )
        response += f"<b>📚 Additional Database Info:</b><br>{db_info}"

    return jsonify({"reply": response})

if __name__ == '__main__':
    app.run(debug=True)
