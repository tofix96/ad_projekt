import json
import pandas as pd

def validate_data(data):
    required_keys = {'godzina', 'cisnienie', 'tetno'}
    for entry in data:
        if not required_keys.issubset(entry):
            raise ValueError(f"Invalid data entry: {entry}")

def generate_html(chart_configs, data_file='data.json', output_file='blood_pressure_chart.html'):
    try:
        # Wczytanie danych z pliku JSON
        with open(data_file, 'r') as file:
            data = json.load(file)
        
        validate_data(data)

        # Konwersja danych do ramki danych Pandas
        df = pd.DataFrame(data)

        # Wyodrębnienie danych o ciśnieniu krwi
        hours = df['godzina'].tolist()

        bp_chart_json = ""
        hr_chart_json = ""

        for chart_config in chart_configs:
            if chart_config['title']['text'] == 'Wykres ciśnienia krwi':
                systolic_pressures = df['cisnienie'].apply(lambda x: x[0]).tolist()
                diastolic_pressures = df['cisnienie'].apply(lambda x: x[1]).tolist()
                chart_config['xAxis']['categories'] = hours
                chart_config['series'][0]['data'] = systolic_pressures
                chart_config['series'][1]['data'] = diastolic_pressures
                bp_chart_json = json.dumps(chart_config)
            elif chart_config['title']['text'] == 'Tętno':
                heart_rates = df['tetno'].tolist()
                chart_config['xAxis']['categories'] = hours
                chart_config['series'][0]['data'] = heart_rates
                hr_chart_json = json.dumps(chart_config)
        
        # Wczytanie szablonu HTML
        with open('chart_template.html', 'r') as file:
            html_code = file.read()

        # Wstawienie chart_json do szablonu HTML
        html_code_with_charts = html_code.format(chart_json=bp_chart_json, heart_rate_chart_json=hr_chart_json)

        # Zapisanie kodu do pliku HTML
        with open(output_file, 'w') as file:
            file.write(html_code_with_charts)

        print(f"Zapisano plik HTML jako '{output_file}'")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Invalid data: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    sample_chart_configs = [
        {
            'chart': {'type': 'line'},
            'title': {'text': 'Wykres ciśnienia krwi'},
            'xAxis': {'categories': []},
            'yAxis': {'title': {'text': 'Ciśnienie krwi (mmHg)'}},
            'legend': {'enabled': True},
            'plotOptions': {'line': {'marker': {'enabled': True}}},
            'series': [
                {'name': 'Ciśnienie skurczowe', 'data': []},
                {'name': 'Ciśnienie rozkurczowe', 'data': []}
            ]
        },
        {
            'chart': {'type': 'line'},
            'title': {'text': 'Tętno'},
            'xAxis': {'categories': []},
            'yAxis': {'title': {'text': 'Tętno (uderzenia na minutę)'}},
            'legend': {'enabled': False},
            'plotOptions': {'line': {'marker': {'enabled': True}}},
            'series': [{'name': 'Tętno', 'data': []}]
        }
    ]

    generate_html(sample_chart_configs)
