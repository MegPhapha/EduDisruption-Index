import csv
import json
import os
from collections import Counter

# Region color palette for scatter chart
REGION_COLORS = {
    'Bamako': '#e41a1c',
    'Gao': '#377eb8',
    'Kayes': '#4daf4a',
    'Kidal': '#984ea3',
    'Koulikoro': '#ff7f00',
    'Mopti': '#a65628',
    'Ségou': '#f781bf',
    'Sikasso': '#666666',
    'Tombouctou': '#17becf',
}

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
        is_gap = r['coverage'] in ('Limited', 'Conflict-only')
        opacity = 0.45 if is_gap else 0.8
        dash = "dashArray: '4,4', " if r['coverage'] == 'Conflict-only' else ""
        popup = f"""
            <div style='font-family: Arial; min-width: 230px;'>
                <h3 style='margin:0 0 5px 0;'>{r['cercle']}</h3>
                <span style='color:white; background:{color}; padding:2px 6px; border-radius:3px; font-size:11px;'>{r['risk']}</span>
                <span style='color:#333; background:#eee; padding:2px 6px; border-radius:3px; font-size:11px; margin-left:4px;'>Coverage: {r['coverage']}</span>
                <hr style='border:0; border-top:1px solid #eee; margin:10px 0;'>
                <table style='width:100%; font-size:12px;'>
                    <tr><td><b>Region:</b></td><td align='right'>{r['region']}</td></tr>
                    <tr><td><b>EDI score:</b></td><td align='right'>{r['edi']}</td></tr>
                    <tr><td><b>Schools matched:</b></td><td align='right'>{int(r['total_schools'])}</td></tr>
                    <tr><td><b>Closed schools:</b></td><td align='right'>{int(r['closed_schools'])} ({r['pct_closed']}%)</td></tr>
                    <tr><td><b>Conflict events:</b></td><td align='right'>{int(r['total_conflict_events'])} ({r['events_per_100k']}/100k)</td></tr>
                </table>
            </div>
        """
        js += f"L.circleMarker([{r['lat']}, {r['lng']}], {{radius: {max(6, r['edi'] * 25)}, fillColor: '{color}', color: '#fff', weight: 1, {dash}opacity: 1, fillOpacity: {opacity}}}).addTo(map).bindPopup(`{popup}`);\n"
    return js

def build_scatter_datasets(data):
    # Each region becomes one dataset; points are cercles. Hollow ring for data-gap cercles.
    datasets = []
    for region, color in REGION_COLORS.items():
        full, gap = [], []
        for r in data:
            if r['region'] != region: continue
            point = {
                'x': max(0.1, r['events_per_100k']),
                'y': r['pct_closed'],
                'r': max(4, min(22, (r['population'] ** 0.5) / 60)),
                'cercle': r['cercle'],
                'edi': r['edi'],
                'coverage': r['coverage'],
            }
            if r['coverage'] in ('Limited', 'Conflict-only'):
                gap.append(point)
            else:
                full.append(point)
        if full:
            datasets.append({
                'label': region,
                'data': full,
                'backgroundColor': color + 'CC',
                'borderColor': color,
                'borderWidth': 1,
            })
        if gap:
            datasets.append({
                'label': region + ' (data-gap)',
                'data': gap,
                'backgroundColor': 'rgba(255,255,255,0.0)',
                'borderColor': color,
                'borderWidth': 2,
                'borderDash': [4, 3],
            })
    return datasets

def generate():
    data, regions_events, tier_counts = load_data()
    colors = {"Critical": "#b30000", "High": "#e34a33", "Medium": "#fdbb84", "Low": "#2ca25f", "Data-Limited": "#999999"}
    markers_js = get_markers_js(data, colors)

    # Top-10 EDI excluding Data-Limited so the headline ranking is defensible
    top_10 = sorted([d for d in data if d['risk'] != 'Data-Limited'], key=lambda x: x['edi'], reverse=True)[:10]
    reg_labels = sorted(regions_events.keys())
    reg_vals = [regions_events[r] for r in reg_labels]
    tier_order = ["Critical", "High", "Medium", "Low", "Data-Limited"]
    tier_vals = [tier_counts.get(t, 0) for t in tier_order]
    tier_palette = [colors[t] for t in tier_order]

    scatter_datasets = build_scatter_datasets(data)

    # 1. INDEX.HTML — main map
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
            .header-info {{ position: absolute; top: 20px; left: 60px; z-index: 1000; background: white; padding: 10px 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); max-width: 360px; }}
            .header-info h1 {{ margin: 0 0 4px 0; font-size: 16px; }}
            .header-info p {{ margin: 0; font-size: 12px; color: #444; }}
            .legend {{ position: absolute; bottom: 20px; left: 20px; z-index: 1000; background: white; padding: 10px 14px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); font-size: 12px; }}
            .legend .row {{ display: flex; align-items: center; margin: 3px 0; }}
            .legend .swatch {{ width: 14px; height: 14px; border-radius: 50%; margin-right: 8px; border: 1px solid #fff; box-shadow: 0 0 0 1px #888; }}
            .legend .dashed {{ border: 2px dashed #555; background: transparent; box-shadow: none; }}
        </style>
    </head>
    <body>
        <a href="dashboard.html" class="nav-btn">View Analytics Dashboard →</a>
        <div class="header-info">
            <h1>Mali Education Disruption Index</h1>
            <p>Composite score combining ACLED conflict events and OCHA school closures, weighted by population. Dashed markers = limited school-data coverage; tier reflects conflict signal only.</p>
        </div>
        <div class="legend">
            <div class="row"><span class="swatch" style="background:#b30000"></span>Critical</div>
            <div class="row"><span class="swatch" style="background:#e34a33"></span>High</div>
            <div class="row"><span class="swatch" style="background:#fdbb84"></span>Medium</div>
            <div class="row"><span class="swatch" style="background:#2ca25f"></span>Low</div>
            <div class="row"><span class="swatch" style="background:#999999"></span>Data-Limited</div>
            <div class="row"><span class="swatch dashed"></span>Coverage gap</div>
        </div>
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

    # 2. DASHBOARD.HTML — 2-row layout: top row has donut/map/bars; bottom row has full-width scatter
    dashboard_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mali EDI Dashboard</title>
        <meta charset="utf-8" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: sans-serif; margin: 0; background: #f4f7f9; }}
            .header {{ background: #1a2a3a; color: white; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; }}
            .nav-link {{ color: #fee08b; text-decoration: none; font-weight: bold; border: 1px solid #fee08b; padding: 5px 15px; border-radius: 4px; }}
            .container {{ display: grid; grid-template-columns: 320px 1fr 320px; grid-template-rows: minmax(360px, 45vh) minmax(360px, 50vh); gap: 14px; padding: 14px; }}
            .card {{ background: white; border-radius: 8px; padding: 14px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; flex-direction: column; min-height: 0; }}
            .card h3 {{ margin: 0 0 8px 0; font-size: 14px; color: #1a2a3a; }}
            .card .sub {{ font-size: 11px; color: #666; margin: 0 0 8px 0; }}
            #map {{ border-radius: 8px; flex: 1; min-height: 0; }}
            .scatter-card {{ grid-column: 1 / span 3; }}
            .scatter-wrap {{ position: relative; flex: 1; min-height: 0; }}
            canvas {{ max-width: 100%; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 style="margin:0; font-size:18px;">Mali EDI Analytics Dashboard</h1>
            <a href="index.html" class="nav-link">← Back to Main Map</a>
        </div>
        <div class="container">
            <div class="card">
                <h3>Risk Distribution</h3>
                <p class="sub">Cercles per tier across Mali. Data-Limited cercles have N&lt;3 matched schools and conflict-rate &lt;100/100k.</p>
                <canvas id="donut"></canvas>
            </div>
            <div id="map" class="card" style="padding:0; overflow:hidden;"></div>
            <div class="card">
                <h3>Top 10 EDI cercles (Data-Limited excluded)</h3>
                <p class="sub">Highest composite risk among cercles with reliable school-data coverage.</p>
                <canvas id="bar"></canvas>
                <h3 style="margin-top:14px;">Conflict events by region</h3>
                <canvas id="reg"></canvas>
            </div>
            <div class="card scatter-card">
                <h3>Two signals, two shortlists: conflict intensity vs school closure rate</h3>
                <p class="sub">Each bubble = one cercle (size ∝ √population, color = region). <b>Hollow rings</b> mark cercles where school-data coverage is partial or missing — the closure signal cannot be trusted, so triage relies on the conflict axis alone. Cercles in the upper-right are flagged by both signals; cercles isolated on one axis tell EBI which signal is driving their tier and where field verification matters most.</p>
                <div class="scatter-wrap"><canvas id="scatter"></canvas></div>
            </div>
        </div>
        <script>
            var map = L.map('map').setView([16.5, -4.0], 6);
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png').addTo(map);
            fetch('https://github.com/wmgeolab/geoBoundaries/raw/main/releaseData/gbOpen/MLI/ADM0/geoBoundaries-MLI-ADM0.geojson').then(res => res.json()).then(geo => {{ L.geoJSON(geo, {{ style: {{ color: '#000', weight: 2, fillOpacity: 0 }} }}).addTo(map); }});
            {markers_js}

            new Chart(document.getElementById('donut'), {{
                type: 'doughnut',
                data: {{ labels: {json.dumps(tier_order)}, datasets: [{{ data: {json.dumps(tier_vals)}, backgroundColor: {json.dumps(tier_palette)} }}] }},
                options: {{ plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }} }}, maintainAspectRatio: false }}
            }});

            new Chart(document.getElementById('bar'), {{
                type: 'bar',
                data: {{ labels: {json.dumps([x['cercle'] for x in top_10])}, datasets: [{{ label: 'EDI', data: {json.dumps([x['edi'] for x in top_10])}, backgroundColor: '#1a2a3a' }}] }},
                options: {{ indexAxis: 'y', plugins: {{ legend: {{ display: false }} }}, maintainAspectRatio: false }}
            }});

            new Chart(document.getElementById('reg'), {{
                type: 'bar',
                data: {{ labels: {json.dumps(reg_labels)}, datasets: [{{ label: 'Events', data: {json.dumps(reg_vals)}, backgroundColor: '#fdbb84' }}] }},
                options: {{ plugins: {{ legend: {{ display: false }} }}, maintainAspectRatio: false }}
            }});

            new Chart(document.getElementById('scatter'), {{
                type: 'bubble',
                data: {{ datasets: {json.dumps(scatter_datasets)} }},
                options: {{
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{ type: 'logarithmic', title: {{ display: true, text: 'Conflict events per 100k population (log scale)' }} }},
                        y: {{ min: 0, max: 105, title: {{ display: true, text: '% of matched schools closed' }} }}
                    }},
                    plugins: {{
                        legend: {{ position: 'right', labels: {{ font: {{ size: 10 }}, boxWidth: 10 }} }},
                        tooltip: {{ callbacks: {{ label: function(ctx) {{ var p = ctx.raw; return p.cercle + ' — EDI ' + p.edi + ' (' + p.coverage + ')'; }} }} }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """

    with open('index.html', 'w') as f: f.write(index_html)
    with open('dashboard.html', 'w') as f: f.write(dashboard_html)
    print("Generated index.html and dashboard.html")

generate()
