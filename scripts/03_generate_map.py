import csv
import json
import os
from collections import Counter

def load_data():
    data = []
    regions_events = Counter()
    tier_counts = Counter()
    with open('data/clean/mali_map_data.csv', mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in ['lat', 'lng', 'edi', 'total_schools', 'closed_schools', 'pct_closed', 'total_conflict_events', 'events_per_100k', 'population']:
                row[key] = float(row[key])
            data.append(row)
            regions_events[row['region']] += int(row['total_conflict_events'])
            tier_counts[row['risk']] += 1
    return data, regions_events, tier_counts

def get_markers_js(data, colors):
    js = ""
    for r in data:
        color = colors.get(r['risk'], "#999999")
        popup = f"""
            <div style='font-family: Arial; min-width: 200px;'>
                <h3 style='margin:0 0 5px 0;'>{r['cercle']}</h3>
                <span style='color:white; background:{color}; padding:2px 6px; border-radius:3px; font-size:11px;'>{r['risk']} RISK</span>
                <hr style='border:0; border-top:1px solid #eee; margin:10px 0;'>
                <table style='width:100%; font-size:12px;'>
                    <tr><td><b>Region:</b></td><td align='right'>{r['region']}</td></tr>
                    <tr><td><b>EDI Score:</b></td><td align='right'>{r['edi']}</td></tr>
                    <tr><td><b>Closed Schools:</b></td><td align='right'>{int(r['closed_schools'])}</td></tr>
                    <tr><td><b>Conflict Events:</b></td><td align='right'>{int(r['total_conflict_events'])}</td></tr>
                </table>
            </div>
        """
        js += f"L.circleMarker([{r['lat']}, {r['lng']}], {{radius: {max(6, r['edi'] * 25)}, fillColor: '{color}', color: '#fff', weight: 1, opacity: 1, fillOpacity: 0.8}}).addTo(map).bindPopup(`{popup}`);\n"
    return js

def generate():
    data, regions_events, tier_counts = load_data()
    colors = {"Critical": "#b30000", "High": "#e34a33", "Medium": "#fdbb84", "Low": "#2ca25f"}
    markers_js = get_markers_js(data, colors)
    
    # 1. GENERATE INDEX.HTML (Map Only)
    index_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mali EDI Map</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            body {{ font-family: sans-serif; margin: 0; }}
            #map {{ height: 100vh; width: 100%; }}
            .nav-btn {{ position: absolute; top: 20px; right: 20px; z-index: 1000; background: #1a2a3a; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
            .header-info {{ position: absolute; top: 20px; left: 60px; z-index: 1000; background: white; padding: 10px 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }}
            .header-info h1 {{ margin: 0; font-size: 18px; }}
        </style>
    </head>
    <body>
        <a href="dashboard.html" class="nav-btn">View Analytics Dashboard →</a>
        <div class="header-info"><h1>Mali Education Disruption Index</h1></div>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([16.5, -4.0], 6);
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{ attribution: '&copy; CARTO' }}).addTo(map);
            fetch('https://github.com/wmgeolab/geoBoundaries/raw/main/releaseData/gbOpen/MLI/ADM0/geoBoundaries-MLI-ADM0.geojson').then(res => res.json()).then(geo => {{ L.geoJSON(geo, {{ style: {{ color: '#000', weight: 3, fillOpacity: 0 }} }}).addTo(map); }});
            {markers_js}
        </script>
    </body>
    </html>
    """
    
    # 2. GENERATE DASHBOARD.HTML
    top_10 = sorted(data, key=lambda x: x['edi'], reverse=True)[:10]
    reg_labels = sorted(regions_events.keys())
    reg_vals = [regions_events[r] for r in reg_labels]
    
    dashboard_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mali EDI Dashboard</title>
        <meta charset="utf-8" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"></script>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: sans-serif; margin: 0; background: #f4f7f9; }}
            .header {{ background: #1a2a3a; color: white; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; }}
            .nav-link {{ color: #fee08b; text-decoration: none; font-weight: bold; border: 1px solid #fee08b; padding: 5px 15px; border-radius: 4px; }}
            .container {{ display: grid; grid-template-columns: 350px 1fr 350px; gap: 15px; padding: 15px; height: calc(100vh - 70px); }}
            .card {{ background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; flex-direction: column; }}
            #map {{ border-radius: 8px; height: 100%; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Mali EDI Analytics Dashboard</h1>
            <a href="index.html" class="nav-link">← Back to Main Map</a>
        </div>
        <div class="container">
            <div class="card"><h3>Risk Distribution</h3><canvas id="donut"></canvas></div>
            <div id="map" class="card"></div>
            <div class="card"><h3>Top 10 Risk Cercles</h3><canvas id="bar"></canvas><h3>Regional Conflict</h3><canvas id="reg"></canvas></div>
        </div>
        <script>
            var map = L.map('map').setView([16.5, -4.0], 6);
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png').addTo(map);
            {markers_js}
            new Chart(document.getElementById('donut'), {{ type: 'doughnut', data: {{ labels: {json.dumps(["Critical","High","Medium","Low"])}, datasets: [{{ data: {json.dumps([tier_counts[t] for t in ["Critical","High","Medium","Low"]])}, backgroundColor: ["#b30000","#e34a33","#fdbb84","#2ca25f"] }}] }} }});
            new Chart(document.getElementById('bar'), {{ type: 'bar', data: {{ labels: {json.dumps([x['cercle'] for x in top_10])}, datasets: [{{ label: 'EDI', data: {json.dumps([x['edi'] for x in top_10])}, backgroundColor: '#1a2a3a' }}] }}, options: {{ indexAxis: 'y' }} }});
            new Chart(document.getElementById('reg'), {{ type: 'bar', data: {{ labels: {json.dumps(reg_labels)}, datasets: [{{ label: 'Events', data: {json.dumps(reg_vals)}, backgroundColor: '#fdbb84' }}] }} }});
        </script>
    </body>
    </html>
    """

    with open('index.html', 'w') as f: f.write(index_html)
    with open('dashboard.html', 'w') as f: f.write(dashboard_html)
    print("Generated index.html and dashboard.html")

generate()
