from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import googlemaps
from datetime import datetime  # Only import the `datetime` class from the module
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'Sagar321'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Singh%40123@localhost/smart_city'
db = SQLAlchemy(app)


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
    date = db.Column(db.DateTime, default=datetime.utcnow)  # Corrected here
    done_time = db.Column(db.DateTime, nullable=True)  # Add done_time as nullable


class CriminalReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    criminal_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)  # Corrected here

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
    incidents = Incident.query.filter_by(city=city).all()  # Make sure to include summary and other necessary fields
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
        incident.done_time = datetime.utcnow()  # Set done_time when marking as covered
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

    # Get the incidents for the current month (from the 1st day of the current month)
    current_month_incidents = Incident.query.filter_by(city=city).filter(Incident.date >= datetime.utcnow().replace(day=1)).all()

    # Get the incidents for the previous month
    previous_month_incidents = Incident.query.filter_by(city=city).filter(Incident.date < datetime.utcnow().replace(day=1)).all()

    # Calculate total incidents for current and previous months
    current_month_count = len(current_month_incidents)
    previous_month_count = len(previous_month_incidents)

    # Calculate covered incidents for current and previous months
    current_month_covered_count = len([incident for incident in current_month_incidents if incident.covered])
    previous_month_covered_count = len([incident for incident in previous_month_incidents if incident.covered])

    # Calculate the response rate (covered incidents / total incidents) for both months
    if current_month_count > 0:
        current_month_response_rate = (current_month_covered_count / current_month_count) * 100
    else:
        current_month_response_rate = 0

    if previous_month_count > 0:
        previous_month_response_rate = (previous_month_covered_count / previous_month_count) * 100
    else:
        previous_month_response_rate = 0

    # Calculate the change rate for incidents between the two months
    if previous_month_count > 0:
        change_rate = ((current_month_count - previous_month_count) / previous_month_count) * 100
    else:
        change_rate = 'N/A'  # No previous data to compare with

    # Calculate the average time to mark incidents as "Done" (in minutes)
    total_time_taken = 0
    total_incidents = 0

    # Calculate total time taken for all incidents that have been marked as "Done"
    for incident in current_month_incidents + previous_month_incidents:
        if incident.done_time:  # If the incident has been marked as "Done"
            time_taken = incident.done_time - incident.date  # Calculate time from incident date to done time
            total_time_taken += time_taken.total_seconds()
            total_incidents += 1

    # Calculate the average time taken to mark incidents as "Done" (in minutes)
    if total_incidents > 0:
        avg_time_to_mark_done = total_time_taken / total_incidents / 60  # Convert seconds to minutes
    else:
        avg_time_to_mark_done = 0

    # Render the crime graph page with the updated data
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the database tables
    app.run(debug=True)
