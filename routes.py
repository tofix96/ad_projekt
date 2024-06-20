from collections import defaultdict
from flask import Flask, render_template, request, jsonify, Response, redirect, url_for
from functions import load_json, save_json, validate_data, analyze_data, check_alerts, generate_chart_config
import json
import pandas as pd
from datetime import date, datetime
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    data = load_json('data.json')
    if data:
        latest_data = data[-1]
    else:
        latest_data = {}
    
    if not os.path.exists('settings.json'):
        default_settings = {
            "heart_rate_threshold": 100,
            "blood_pressure_systolic_threshold": 140,
            "blood_pressure_diastolic_threshold": 90,
            "temperature_threshold": 37.5,
            "stress_threshold": 70
        }
        with open('settings.json', 'w') as file:
            json.dump(default_settings, file)
    
    with open('settings.json', 'r') as file:
        settings = json.load(file)

    if data:
        latest_data = data[-1]
    else:
        latest_data = {}

    alerts = check_alerts(latest_data, settings)
    
    return render_template('index.html', latest_data=latest_data, alerts=alerts)

@app.route('/bp_chart')
def bp_chart():
    bp_chart_config, _, _ = generate_chart_config()
    return render_template('bp_chart.html', bp_chart_config=json.dumps(bp_chart_config))

@app.route('/hr_chart')
def hr_chart():
    _, hr_chart_config, _ = generate_chart_config()
    return render_template('hr_chart.html', hr_chart_config=json.dumps(hr_chart_config))

@app.route('/stress_chart')
def stress_chart():
    _, _, stress_chart_config = generate_chart_config()
    return render_template('stress_chart.html', stress_chart_config=json.dumps(stress_chart_config))

@app.route('/update_data', methods=['POST'])
def update_data():
    new_data = request.json
    try:
        validate_data(new_data)
        with open('data.json', 'w') as file:
            json.dump(new_data, file)
        return jsonify({"status": "success"}), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/health_notes', methods=['GET', 'POST'])
def health_notes():
    if request.method == 'POST':
        note = request.form['note']
        new_note = {
            'note': note,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        with open('notes.json', 'a') as file:
            json.dump(new_note, file)
            file.write('\n')

    notes = []
    try:
        with open('notes.json', 'r') as file:
            notes = [json.loads(line) for line in file]
    except FileNotFoundError:
        pass

    return render_template('health_notes.html', notes=notes)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    default_settings = {
        "heart_rate_threshold": 100,
        "blood_pressure_systolic_threshold": 140,
        "blood_pressure_diastolic_threshold": 90,
        "temperature_threshold": 37.5,
        "stress_threshold": 70
    }

    if request.method == 'POST':
        settings = {
            "heart_rate_threshold": request.form['heart_rate_threshold'],
            "blood_pressure_systolic_threshold": request.form['blood_pressure_systolic_threshold'],
            "blood_pressure_diastolic_threshold": request.form['blood_pressure_diastolic_threshold'],
            "temperature_threshold": request.form['temperature_threshold'],
            "stress_threshold": request.form['stress_threshold']
        }
        with open('settings.json', 'w') as file:
            json.dump(settings, file)
    else:
        if not os.path.exists('settings.json'):
            with open('settings.json', 'w') as file:
                json.dump(default_settings, file)
        with open('settings.json', 'r') as file:
            settings = json.load(file)
    
    return render_template('settings.html', settings=settings)

@app.route('/check_alerts')
def check_alerts_view():
    with open('data.json', 'r') as file:
        data = json.load(file)
    latest_data = data[-1]

    with open('settings.json', 'r') as file:
        settings = json.load(file)

    alerts = check_alerts(latest_data, settings)
    
    return render_template('alerts.html', alerts=alerts)

@app.route('/history')
def history():
    history_data = load_json('history.json')

    grouped_data = defaultdict(list)
    for entry in history_data:
        grouped_data[entry['date']].append(entry)

    grouped_data = {day.strftime('%Y-%m-%d'): entries for day, entries in grouped_data.items()}

    return render_template('history.html', grouped_data=grouped_data)

@app.route('/export_csv')
def export_csv():
    with open('data.json', 'r') as file:
        data = json.load(file)
    df = pd.DataFrame(data)
    csv_data = df.to_csv(index=False)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=mydata.csv"}
    )

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.json'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            try:
                new_data = load_json(file_path)
                validate_data(new_data)

                # Przeniesienie danych z data.json do history.json
                existing_data = load_json('data.json')
                history_data = load_json('history.json')
                history_data.extend(existing_data)
                save_json('history.json', history_data)

                # Zapisanie nowych danych do data.json
                save_json('data.json', new_data)

                return redirect(url_for('index'))
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON file: {e}")
                return "Invalid JSON file", 400
    return render_template('upload.html')


@app.route('/analyze')
def analyze():
    data = load_json('data.json')
    recommendations = analyze_data(data)
    return render_template('analysis.html', recommendations=recommendations)
