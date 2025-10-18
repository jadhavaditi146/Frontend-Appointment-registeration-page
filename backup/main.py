# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
from datetime import datetime, timedelta
import re
import requests
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from urllib.parse import urlparse

app = Flask(__name__)

YOUTUBE_API_KEY = "AIzaSyCcZaXXE3MODAM1BgE55ALbZMgsSHH3j3k"

# -----------------------------
# 1️⃣ Diet suggestions dictionary
# -----------------------------
CONDITIONS_DIET = {
    "diabetes": {"tips": "🍎 High-fiber foods, whole grains, leafy greens, lean proteins, avoid sugar.", "query": "diabetes diet"},
    "pcos": {"tips": "🥦 Avoid processed sugar, include protein and fiber, anti-inflammatory foods like berries, nuts, greens.", "query": "PCOS diet"},
    "weight loss": {"tips": "🥗 Fruits, veggies, lean protein, avoid junk food, hydrate well.", "query": "weight loss diet"},
    "weight gain": {"tips": "🍞 Protein-rich foods, healthy fats, frequent calorie-dense meals.", "query": "weight gain diet"},
    "high bp": {"tips": "🥬 Reduce salt, eat potassium-rich foods like bananas and greens, exercise regularly.", "query": "high blood pressure diet"},
    "cholesterol": {"tips": "🥑 Avoid fried foods, eat fiber-rich oats, avocado, nuts, healthy oils.", "query": "cholesterol diet"},
    "anemia": {"tips": "🍖 Iron-rich foods like spinach, legumes, red meat, pair with vitamin C.", "query": "anemia diet"},
    "thyroid": {"tips": "🥬 Iodine-rich foods if needed, avoid highly processed foods, balanced protein & fiber diet.", "query": "thyroid diet"},
    "kidney": {"tips": "💧 Reduce salt, moderate protein, stay hydrated, avoid processed food.", "query": "kidney diet"},
    "heart": {"tips": "❤️ Increase fruits, vegetables, whole grains, reduce saturated fats and sugar.", "query": "heart healthy diet"},
    "fever": {"tips": "🌡️ Stay hydrated, eat light foods like soups and fruits, avoid oily/heavy meals, get enough rest.", "query": "fever diet"},
    "cold": {"tips": "❄️ Warm fluids, soups, ginger tea, vitamin C-rich fruits, light meals, rest well.", "query": "cold diet"},
    "migraine": {"tips": "🧠 Stay hydrated, avoid triggers like chocolate/caffeine, eat magnesium-rich foods like nuts and leafy greens.", "query": "migraine diet"},
    "stomach upset": {"tips": "🥣 Eat bland foods like rice, toast, bananas; avoid spicy/fatty foods, drink water.", "query": "stomach upset diet"}
}

# Aliases
CONDITIONS_DIET["pcod"] = {"alias": "pcos"}

# -----------------------------
# 2️⃣ Initialize AI generator
# -----------------------------
tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-small")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-small")

# -----------------------------
# 3️⃣ Helper functions
# -----------------------------
def get_youtube_videos(query, max_results=3):
    url = (
        f"https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet&q={query}+health&maxResults={max_results}"
        f"&type=video&key={YOUTUBE_API_KEY}"
    )
    response = requests.get(url)
    data = response.json()

    videos_html = ""
    if "items" in data:
        for item in data["items"]:
            title = item["snippet"]["title"]
            video_id = item["id"]["videoId"]
            link = f"https://www.youtube.com/watch?v={video_id}"
            videos_html += f"• <a href='{link}' target='_blank'>{title}</a><br>"
    else:
        videos_html = "❌ No related videos found."

    return videos_html

def get_condition_from_input(user_input):
    user_input = user_input.lower()
    for condition, value in CONDITIONS_DIET.items():
        if "alias" in value and user_input == value["alias"]:
            return condition
        if user_input == condition:
            return condition
        if re.search(r'\b' + re.escape(condition) + r'\b', user_input):
            return condition
    return None

def generate_fallback_response(user_input):
    prompt = f"The user has the health issue '{user_input}'. Provide 2-3 concise diet tips in bullet points. End with: Not medical advice; consult a doctor."
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=60)
    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return text

# -----------------------------
# 4️⃣ News fetching function
# -----------------------------
NEWS_API_KEY = "dbe57b028aeb41e285a226a94865f7a7"

def get_articles_for_condition(condition, num_articles=3):
    query = CONDITIONS_DIET.get(condition, {}).get("query", condition)
    query = query + " health OR wellness OR nutrition"
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    url = f"https://newsapi.org/v2/everything?q={query}&from={seven_days_ago}&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    r = requests.get(url)
    data = r.json()
    articles_list = []

    if data.get("status") != "ok":
        articles_list.append(f"Error fetching articles: {data.get('message')}")
    else:
        articles = data.get("articles", [])
        if not articles:
            articles_list.append(f"No recent articles found. Try this search: https://www.google.com/search?q={query.replace(' ', '+')}+site:healthline.com")
        else:
            for article in articles[:num_articles]:
                articles_list.append(f"{article['title']}: {article['url']}")
    return articles_list

# -----------------------------
# 5️⃣ Chatbot route
# -----------------------------
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").lower()
    condition = get_condition_from_input(user_message)

    # Always generate trusted medical search links
    trusted_sites = [
        f"https://www.webmd.com/search/search_results/default.aspx?query={condition}",
        f"https://www.mayoclinic.org/search/search-results?q={condition}",
        f"https://www.nih.gov/search?utf8=%E2%9C%93&affiliate=nih&query={condition}",
    ]

    if condition:
        tips = CONDITIONS_DIET.get(condition, {}).get("tips", "❌ No diet tips found for this condition.")
        articles = get_articles_for_condition(condition)

        # ✅ Articles HTML
        if articles:
            articles_html = ""
            for article in articles:
                if ": " in article:
                    title, url = article.split(": ", 1)
                    articles_html += f"• <a href='{url}' target='_blank'>{title}</a><br>"
                else:
                    articles_html += f"• {article}<br>"
        else:
            articles_html = ""
            for site in trusted_sites:
                articles_html += f"• <a href='{site}' target='_blank'>{site}</a><br>"

        # ✅ YouTube videos (Real Titles)
        videos_html = get_youtube_videos(condition)

        bot_reply = f"""
<b>Diet Tips:</b><br>{tips}<br><br>
<b>Trusted Medical Resources:</b><br>{articles_html}<br>
<b>Videos:</b><br>{videos_html}<br>
<i>⚠️ This is not medical advice. Please consult a doctor.</i>
"""
    else:
        bot_reply = "❌ No helpful tips available for this condition. Please consult a doctor."

    return jsonify({"reply": bot_reply})



# -----------------------------
# 6️⃣ Database connection
# -----------------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="doctor_appointment"
    )

# -----------------------------
# 7️⃣ Routes for pages (homepage, book, etc.)
# -----------------------------
@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/book', methods=['GET', 'POST'])
def book():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, specialization FROM doctors")
    doctors = cursor.fetchall()

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        age = request.form.get('age')
        doctor_id = request.form.get('doctor_id')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        message = request.form.get('message')
        booking_time = datetime.now()

        if appointment_time and len(appointment_time) == 5:
            appointment_time += ":00"

        sql = """
        INSERT INTO appointments (full_name, email, phone, age, doctor_id, appointment_date, appointment_time, message, booking_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (full_name, email, phone, age, doctor_id, appointment_date, appointment_time, message, booking_time))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('confirmation'))

    cursor.close()
    conn.close()
    return render_template('Book.html', doctors=doctors)

@app.route('/confirmation')
def confirmation():
    return "<h2>✅ Your appointment has been booked successfully!</h2><p>We will contact you shortly to confirm.</p>"

@app.route('/my-appointments', methods=['GET', 'POST'])
def my_appointments():
    appointments = []
    user_identifier = None
    if request.method == 'POST':
        user_identifier = request.form.get('user_identifier')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT a.id, a.full_name, a.email, a.phone, a.age, a.appointment_date, a.appointment_time,
                   a.status, d.name AS doctor_name, d.specialization AS doctor_specialization
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.email = %s OR a.phone = %s
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        """
        cursor.execute(query, (user_identifier, user_identifier))
        appointments = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template('MyAppointments.html', appointments=appointments, user_identifier=user_identifier)

@app.route('/about')
def about():
    return render_template('About.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        subject = request.form.get('subject')
        message = request.form.get('message')

        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO contacts (name, email, phone, subject, message) VALUES (%s,%s,%s,%s,%s)"
        cursor.execute(sql, (name, email, phone, subject, message))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('contact_success'))

    return render_template('Contacts.html')

@app.route('/contact-success')
def contact_success():
    return "<h2>✅ Thank you for reaching out! We'll get back to you soon.</h2>"

@app.route('/doctors')
def doctors_list():
    return render_template('Doctors.html')

# -----------------------------
# 8️⃣ Run the app
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
