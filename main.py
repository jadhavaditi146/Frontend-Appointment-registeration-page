from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="doctor_appointment"
    )

# Home Page
@app.route('/')
def home():
    return render_template('homepage.html')

# Doctors Page
@app.route('/book', methods=['GET', 'POST'])
def book():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch doctors for dropdown
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
            appointment_time += ":00"  # Convert HH:MM → HH:MM:SS for MySQL
        
        sql = """
        INSERT INTO appointments (full_name, email, phone, age, doctor_id, appointment_date, appointment_time, message, booking_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (full_name, email, phone, age, doctor_id, appointment_date, appointment_time, message, booking_time)
        
        cursor.execute(sql, values)
        conn.commit()
        
        cursor.close()
        conn.close()
        return redirect(url_for('confirmation'))
    
    cursor.close()
    conn.close()
    return render_template('Book.html', doctors=doctors)


# Confirmation Page
@app.route('/confirmation')
def confirmation():
    return "<h2>✅ Your appointment has been booked successfully!</h2><p>We will contact you shortly to confirm.</p>"

# View My Appointments
@app.route('/my-appointments', methods=['GET', 'POST'])
def my_appointments():
    appointments = []  # Default empty list
    user_identifier = None

    if request.method == 'POST':
        # Get email or phone number from form
        user_identifier = request.form.get('user_identifier')

        # Connect to DB
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch appointments joined with doctor details
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

    # Render template with appointments (empty list if none found)
    return render_template('MyAppointments.html', appointments=appointments, user_identifier=user_identifier)
# About Page
@app.route('/about')
def about():
    return render_template('About.html')

# Contact Page
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
        sql = """
        INSERT INTO contacts (name, email, phone, subject, message)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (name, email, phone, subject, message))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('contact_success'))

    return render_template('Contacts.html')

@app.route('/doctors')
def doctors_list():
    return render_template('Doctors.html')


@app.route('/contact-success')
def contact_success():
    return "<h2>✅ Thank you for reaching out! We'll get back to you soon.</h2>"

if __name__ == '__main__':
    app.run(debug=True)
