from flask import Flask, request, jsonify, render_template
from groq import Groq
import mysql.connector
import base64
import re

app = Flask(__name__)
client = Groq(api_key="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")

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="rkarthik9140@",
    database="herbal_db"
)
cursor = conn.cursor(dictionary=True)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/chat")
def chat():
    return render_template("chatbot_page.html")

@app.route("/search/<tablet_name>")
def search(tablet_name):
    query = "SELECT * FROM HerbalAlternatives WHERE tablet_name LIKE %s"
    cursor.execute(query, (f"%{tablet_name}%",))
    result = cursor.fetchone()

    if result:
        image_base64 = base64.b64encode(result["image"]).decode("utf-8")
        response = f"""
        <b>Tablet Name:</b> {result['tablet_name']}<br>
        <b>Herbal Alternatives:</b> {result['herbal_alternatives']}<br>
        <b>Natural Excipients:</b> {result['natural_excipients']}<br><br>
        <img src="data:image/jpeg;base64,{image_base64}" width="200">
        """
    else:
        response = ""

    return render_template("search_result.html", tablet_name=tablet_name, response=response)

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
        response = f"<b>learn:</b><br>{formatted_reply}<br><hr>"

    except Exception as e:
        response = f"Sorry, LLaMA response failed. Please try again. Error: {str(e)}"
        return jsonify({"reply": response})

    query = "SELECT * FROM HerbalAlternatives WHERE tablet_name LIKE %s"
    cursor.execute(query, (f"%{tablet_name}%",))
    result = cursor.fetchone()

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

if __name__ == "__main__":
    app.run(debug=True)
