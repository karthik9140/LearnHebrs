from flask import Flask, request, render_template, send_from_directory, url_for
import mysql.connector
import os

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')

@app.route('/static/<path:filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='rkarthik9140@',
        database='herbal_db'
    )

@app.route('/', methods=['GET', 'POST'])
def search():
    results = []
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        query = request.form['search']
        print(f"Search query: {query}")  
        sql = """
            SELECT d.name, d.medicinal_plants, d.natural_excipients, di.image_path, di.image_type
            FROM drug d
            LEFT JOIN drugimg di ON d.drug_id = di.drug_id
            WHERE d.name LIKE %s
        """
        cursor.execute(sql, (f"%{query}%",))
    else:
        sql = """
            SELECT d.name, d.medicinal_plants, d.natural_excipients, di.image_path, di.image_type
            FROM drug d
            LEFT JOIN drugimg di ON d.drug_id = di.drug_id
        """
        cursor.execute(sql)

    rows = cursor.fetchall()
    for row in rows:
        name, plants, excipients, image_path, image_type = row
        results.append({
            'name': name,
            'plants': plants,
            'excipients': excipients,
            'image_path': image_path,
            'image_type': image_type
        })

    cursor.close()
    conn.close()
    return render_template('search.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
