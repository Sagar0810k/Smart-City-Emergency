from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai
from dotenv import load_dotenv
import os
from apscheduler.schedulers.background import BackgroundScheduler


load_dotenv()

# Flask app configuration
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "Singh321")  # Use .env for security
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "mysql+pymysql://root:Singh%40123@localhost/smart_city")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
    
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")  # Updated model name

# ------------------ DATABASE MODELS ------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(225), nullable=False)
    city = db.Column(db.String(120))

class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    covered = db.Column(db.Boolean, default=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    done_time = db.Column(db.DateTime, nullable=True)

class CriminalReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    criminal_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------ ROUTES ------------------

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    password_hash = generate_password_hash(request.form['password'])
    user = User(username=request.form['username'], password=password_hash, city=request.form['city'])
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(username=request.form['username']).first()
    if user and check_password_hash(user.password, request.form['password']):
        session['user_id'] = user.id
        session['city'] = user.city
        return redirect(url_for('dashboard'))
    return "Invalid credentials"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    city = session['city']
    incidents = Incident.query.filter_by(city=city).all()
    return render_template('dashboard.html', incidents=incidents, city=city)

@app.route('/report_incident', methods=['POST'])
def report_incident():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    incident = Incident(location=data['location'], summary=data['summary'], city=session['city'])
    db.session.add(incident)
    db.session.commit()
    return jsonify({'message': 'Incident reported successfully'})

@app.route('/mark_covered/<int:id>', methods=['GET'])
def mark_covered(id):
    incident = Incident.query.get(id)
    if incident:
        incident.covered = True
        incident.done_time = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Incident not found'})

@app.route('/report_criminal', methods=['POST'])
def report_criminal():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    criminal = CriminalReport(criminal_name=data['criminal_name'], location=data['location'], city=session['city'])
    db.session.add(criminal)
    db.session.commit()
    return jsonify({'message': 'Criminal activity reported successfully'})

@app.route('/crime_graph')
def crime_graph():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    city = session['city']
    current_month_incidents = Incident.query.filter_by(city=city).filter(Incident.date >= datetime.utcnow().replace(day=1)).all()
    previous_month_incidents = Incident.query.filter_by(city=city).filter(Incident.date < datetime.utcnow().replace(day=1)).all()

    current_month_count = len(current_month_incidents)
    previous_month_count = len(previous_month_incidents)
    current_month_covered_count = len([incident for incident in current_month_incidents if incident.covered])
    previous_month_covered_count = len([incident for incident in previous_month_incidents if incident.covered])

    current_month_response_rate = (current_month_covered_count / current_month_count) * 100 if current_month_count > 0 else 0
    previous_month_response_rate = (previous_month_covered_count / previous_month_count) * 100 if previous_month_count > 0 else 0
    change_rate = ((current_month_count - previous_month_count) / previous_month_count) * 100 if previous_month_count > 0 else 'N/A'

    total_time_taken = sum((incident.done_time - incident.date).total_seconds() for incident in current_month_incidents + previous_month_incidents if incident.done_time)
    avg_time_to_mark_done = (total_time_taken / len(current_month_incidents + previous_month_incidents)) / 60 if len(current_month_incidents + previous_month_incidents) > 0 else 0

    return render_template(
        'crime_graph.html',
        current_month=current_month_count,
        previous_month=previous_month_count,
        current_month_response_rate=current_month_response_rate,
        previous_month_response_rate=previous_month_response_rate,
        change_rate=change_rate,
        avg_time_to_mark_done=avg_time_to_mark_done,
        city=city
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ------------------ BACKGROUND TASK: FETCH INCIDENTS ------------------

def fetch_incidents():
    print("Fetching new incidents using Gemini AI...")
    query = "Find the latest reported incidents in major cities in India within the last hour."

    try:
        response = model.generate_content([query])  # Use list for query
        if response and hasattr(response, 'text'):
            new_incidents = response.text.strip().split("\n")

            with app.app_context():
                for incident in new_incidents:
                    parts = incident.split("-")
                    if len(parts) >= 2:
                        location, summary = parts[0].strip(), parts[1].strip()
                        existing_incident = Incident.query.filter_by(location=location, summary=summary).first()

                        if not existing_incident:
                            new_incident = Incident(location=location, summary=summary, city="Unknown")
                            db.session.add(new_incident)

                db.session.commit()
                print("Incidents updated successfully!")

    except Exception as e:
        print(f"Error fetching incidents: {e}")

# Schedule incident fetching every 30 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_incidents, 'interval', minutes=30)
scheduler.start()

with app.app_context():
    fetch_incidents()

# ------------------ RUN FLASK APP ------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
