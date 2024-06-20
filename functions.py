import json
import pandas as pd
from datetime import datetime

def validate_data(data):
    required_keys = {'date', 'godzina', 'cisnienie', 'tetno', 'temperatura', 'stres'}
    for entry in data:
        if not required_keys.issubset(entry):
            raise ValueError(f"Invalid data entry: {entry}")

def deserialize_dates(data):
    for entry in data:
        entry['date'] = datetime.fromisoformat(entry['date']).date()
        try:
            entry['godzina'] = datetime.fromisoformat(entry['godzina'])
        except ValueError:
            entry['godzina'] = datetime.strptime(entry['godzina'], '%H:%M:%S').time()
    return data

def load_json(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            data = deserialize_dates(data)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading JSON file: {e}")
        data = []
    return data


def save_json(file_path, data):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, default=str)

def analyze_data(data):
    df = pd.DataFrame(data)


    recommendations = []
    high_bp_detected = False
    abnormal_hr_detected = False
    abnormal_temp_detected = False
    high_stress_detected = False

    for index, row in df.iterrows():
        systolic, diastolic = row['cisnienie']
        temp = row['temperatura']
        hr = row['tetno']
        stress = row['stres']

        if not high_bp_detected:
            if systolic >= 140 or diastolic >= 90:
                recommendations.append("Nieprawidłowe ciśnienie krwi: Jeśli systoliczne ciśnienie krwi wynosi 140 mm Hg lub więcej, lub diastoliczne ciśnienie krwi wynosi 90 mm Hg lub więcej, zalecane jest skonsultowanie się z lekarzem. Wysokie ciśnienie krwi może prowadzić do poważnych schorzeń sercowo-naczyniowych, takich jak zawał serca lub udar. Zaleca się również wdrożenie zmian stylu życia, takich jak dieta DASH, regularna aktywność fizyczna, ograniczenie spożycia soli i alkoholu, rzucenie palenia oraz redukcja stresu.")
            else:
                recommendations.append("Ciśnienie krwi w normie.")
            high_bp_detected = True
        if not abnormal_hr_detected:
            if hr > 100:
                recommendations.append("Nieprawidłowe tętno: Tętno przekracza 100 uderzeń na minutę, jeśli nie wykonywałeś w tym momencie ćwiczeń fizycznych, powinieneś skonsultować się z lekarzem. Może to być oznaka problemów kardiologicznych, takich jak arytmia lub inne schorzenia serca​")
            else:
                recommendations.append("Twoje tętno mieści się w zakresie 60-100 uderzeń na minutę, jest to uznawane za normalne wartości.")
            abnormal_hr_detected = True
        if not abnormal_temp_detected:
            if temp < 37.4:
                recommendations.append("Temperatura w normie")
            else:
                recommendations.append("Temperatura przekracza 37,4°C, może to być oznaka infekcji lub innego schorzenia. Zaleca skonsultowanie się z lekarzem.")
            abnormal_temp_detected = True
        if not high_stress_detected:
            if stress > 70:
                recommendations.append("Poziom stresu przekracza 70, warto rozważyć techniki redukcji stresu, takie jak medytacja, ćwiczenia relaksacyjne, regularna aktywność fizyczna czy konsultacja z psychologiem. Wysoki stres może prowadzić do wielu problemów zdrowotnych, w tym nadciśnienia i problemów sercowo-naczyniowych")
            else:
                recommendations.append("Poziom stresu jest niski")
            high_stress_detected = True
    
    return recommendations


def generate_chart_config():
    with open('data.json', 'r') as file:
        data = json.load(file)
    
    validate_data(data)
    df = pd.DataFrame(data)
    hours = df['godzina'].tolist()

    bp_chart_config = {
        'chart': {'type': 'line'},
        'title': {'text': 'Wykres ciśnienia krwi'},
        'xAxis': {'categories': hours},
        'yAxis': {'title': {'text': 'Ciśnienie krwi (mmHg)'}},
        'legend': {'enabled': True},
        'plotOptions': {'line': {'marker': {'enabled': True}}},
        'series': [
            {'name': 'Ciśnienie skurczowe', 'data': df['cisnienie'].apply(lambda x: x[0]).tolist()},
            {'name': 'Ciśnienie rozkurczowe', 'data': df['cisnienie'].apply(lambda x: x[1]).tolist()}
        ]
    }

    hr_chart_config = {
        'chart': {'type': 'line'},
        'title': {'text': 'Tętno'},
        'xAxis': {'categories': hours},
        'yAxis': {'title': {'text': 'Tętno (uderzenia na minutę)'}},
        'legend': {'enabled': False},
        'plotOptions': {'line': {'marker': {'enabled': True}}},
        'series': [{'name': 'Tętno', 'data': df['tetno'].tolist()}]
    }

    stress_chart_config = {
        'chart': {'type': 'line'},
        'title': {'text': 'Poziom stresu'},
        'xAxis': {'categories': hours},
        'yAxis': {'title': {'text': 'Poziom stresu'}},
        'legend': {'enabled': False},
        'plotOptions': {'line': {'marker': {'enabled': True}}},
        'series': [{'name': 'Stres', 'data': df['stres'].tolist()}]
    }

    return bp_chart_config, hr_chart_config, stress_chart_config

def check_alerts(latest_data, settings):
    alerts = []
    if latest_data['tetno'] > int(settings['heart_rate_threshold']):
        alerts.append(f"Tętno przekroczyło próg: {latest_data['tetno']} > {settings['heart_rate_threshold']}")
    if latest_data['cisnienie'][0] > int(settings['blood_pressure_systolic_threshold']):
        alerts.append(f"Ciśnienie skurczowe przekroczyło próg: {latest_data['cisnienie'][0]} > {settings['blood_pressure_systolic_threshold']}")
    if latest_data['cisnienie'][1] > int(settings['blood_pressure_diastolic_threshold']):
        alerts.append(f"Ciśnienie rozkurczowe przekroczyło próg: {latest_data['cisnienie'][1]} > {settings['blood_pressure_diastolic_threshold']}")
    if latest_data['temperatura'] > float(settings['temperature_threshold']):
        alerts.append(f"Temperatura przekroczyła próg: {latest_data['temperatura']} > {settings['temperature_threshold']}")
    if latest_data['stres'] > int(settings['stress_threshold']):
        alerts.append(f"Poziom stresu przekroczył próg: {latest_data['stres']} > {settings['stress_threshold']}")
    return alerts