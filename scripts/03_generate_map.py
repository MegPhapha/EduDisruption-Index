import csv
import json
import os
from collections import Counter

def generate_dashboard():
    data = []
    regions_events = Counter()
    tier_counts = Counter()
    
    with open('data/clean/mali_map_data.csv', mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in ['lat', 'lng', 'edi', 'total_schools', 'closed_schools', 'pct_closed', 'total_conflict_events', 'events_per_100k', 'population']:
                row[key] = float(row[key])
            data.append(row)
            # Aggregate for charts
            regions_events[row['region']] += int(row['total_conflict_events'])
            tier_counts[row['risk']] += 1

    # Sort data for charts
    top_10_cercles = sorted(data, key=lambda x: x['edi'], reverse=True)[:10]
    region_labels = sorted(regions_events.keys())
    region_values = [regions_events[r] for r in region_labels]
    
    tier_labels = ["Critical", "High", "Medium", "Low"]
    tier_values = [tier_counts[t] for t in tier_labels]

    colors = {
        "Critical": "#b30000",
        "High": "#e34a33",
        "Medium": "#fdbb84",
        "Low": "#2ca25f"
    }

    markers_js = ""
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
        markers_js += f"""
        L.circleMarker([{r['lat']}, {r['lng']}], {{
            radius: {max(6, r['edi'] * 25)},
            fillColor: "{color}",
            color: "#fff",
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
        }}).addTo(map).bindPopup(`{popup}`);
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mali EDI Dashboard</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; margin: 0; background: #f4f7f9; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }}
            .header {{ background: #1a2a3a; color: white; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; }}
            .header h1 {{ margin: 0; font-size: 20px; }}
            
            .dashboard-container {{ display: grid; grid-template-columns: 350px 1fr 350px; grid-template-rows: 1fr 300px; gap: 15px; padding: 15px; flex-grow: 1; }}
            
            .card {{ background: white; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); padding: 15px; display: flex; flex-direction: column; }}
            .card h2 {{ margin: 0 0 15px 0; font-size: 14px; color: #555; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #eee; padding-bottom: 8px; }}
            
            #map {{ grid-column: 2 / 3; grid-row: 1 / 3; border-radius: 10px; height: 100%; }}
            .chart-container {{ position: relative; flex-grow: 1; }}
            
            .legend-item {{ display: flex; align-items: center; margin-bottom: 5px; font-size: 12px; }}
            .legend-color {{ width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Mali Education Disruption Index (EDI) Dashboard</h1>
            <div style="font-size: 12px; opacity: 0.8;">Data Period: 2020 - 2024</div>
        </div>
        
        <div class="dashboard-container">
            <!-- Left Sidebar: Donut and Bar -->
            <div class="card" style="grid-column: 1; grid-row: 1;">
                <h2>Risk Distribution</h2>
                <div class="chart-container"><canvas id="donutChart"></canvas></div>
            </div>
            
            <div class="card" style="grid-column: 1; grid-row: 2;">
                <h2>Top 10 Risk Cercles (EDI)</h2>
                <div class="chart-container"><canvas id="barChart"></canvas></div>
            </div>

            <!-- Central Map -->
            <div id="map" class="card"></div>

            <!-- Right Sidebar: Region Analysis -->
            <div class="card" style="grid-column: 3; grid-row: 1 / 3;">
                <h2>Conflict Events by Region</h2>
                <div class="chart-container"><canvas id="regionChart"></canvas></div>
                <div style="margin-top: 20px; font-size: 11px; color: #888;">
                    <p><b>Note:</b> Circle size on map corresponds to conflict volume. Risk color indicates composite disruption score.</p>
                </div>
            </div>
        </div>

        <script>
            // MAP INITIALIZATION
            var map = L.map('map', {{ zoomControl: false }}).setView([17.0, -4.0], 6);
            L.control.zoom({{ position: 'topright' }}).addTo(map);
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{ attribution: '&copy; CARTO' }}).addTo(map);

            fetch('https://github.com/wmgeolab/geoBoundaries/raw/main/releaseData/gbOpen/MLI/ADM0/geoBoundaries-MLI-ADM0.geojson')
                .then(res => res.json())
                .then(geo => {{
                    L.geoJSON(geo, {{ style: {{ color: "#333", weight: 2, fillOpacity: 0 }} }}).addTo(map);
                }});

            {markers_js}

            // CHARTS INITIALIZATION
            const ctxDonut = document.getElementById('donutChart');
            new Chart(ctxDonut, {{
                type: 'doughnut',
                data: {{
                    labels: {json.dumps(tier_labels)},
                    datasets: [{{
                        data: {json.dumps(tier_values)},
                        backgroundColor: ["#b30000", "#e34a33", "#fdbb84", "#2ca25f"],
                        borderWidth: 0
                    }}]
                }},
                options: {{ maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom', labels: {{ boxWidth: 10, font: {{ size: 11 }} }} }} }} }}
            }});

            const ctxBar = document.getElementById('barChart');
            new Chart(ctxBar, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps([x['cercle'] for x in top_10_cercles])},
                    datasets: [{{
                        label: 'EDI Score',
                        data: {json.dumps([x['edi'] for x in top_10_cercles])},
                        backgroundColor: '#1a2a3a'
                    }}]
                }},
                options: {{ indexAxis: 'y', maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }}, y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }} }} }}
            }});

            const ctxRegion = document.getElementById('regionChart');
            new Chart(ctxRegion, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(region_labels)},
                    datasets: [{{
                        label: 'Events',
                        data: {json.dumps(region_values)},
                        backgroundColor: '#fdbb84'
                    }}]
                }},
                options: {{ maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }}, y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }} }} }}
            }});
        </script>
    </body>
    </html>
    """

    os.makedirs('outputs', exist_ok=True)
    with open('outputs/mali_edi_map.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Dashboard generated: outputs/mali_edi_map.html")

if __name__ == "__main__":
    generate_dashboard()
