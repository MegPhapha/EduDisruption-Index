import csv
import json
import os
from collections import Counter

def load_data():
    data = []
    regions_events = Counter()
    tier_counts = Counter()
    coverage_counts = Counter()
    with open('data/clean/mali_map_data.csv', mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in ['lat', 'lng', 'edi', 'total_schools', 'closed_schools', 'pct_closed', 'total_conflict_events', 'events_per_100k', 'population']:
                row[key] = float(row[key])
            data.append(row)
            regions_events[row['region']] += int(row['total_conflict_events'])
            tier_counts[row['risk']] += 1
            coverage_counts[row['coverage']] += 1
    return data, regions_events, tier_counts, coverage_counts

def get_markers_js(data, colors):
    js = ""
    for r in data:
        color = colors.get(r['risk'], "#999999")
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
        js += f"L.circleMarker([{r['lat']}, {r['lng']}], {{radius: {max(6, r['edi'] * 25)}, fillColor: '{color}', color: '#fff', weight: 1, opacity: 1, fillOpacity: 0.85}}).addTo(map).bindPopup(`{popup}`);\n"
    return js

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

def build_scatter_datasets(data):
    datasets = []
    for region, color in REGION_COLORS.items():
        full, gap = [], []
        for r in data:
            if r['region'] != region: continue
            point = {
                'x': max(0.1, r['events_per_100k']),
                'y': r['pct_closed'],
                'r': max(5, min(22, (r['population'] ** 0.5) / 60)),
                'cercle': r['cercle'],
                'edi': r['edi'],
                'coverage': r['coverage'],
                'risk': r['risk'],
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
    data, regions_events, tier_counts, coverage_counts = load_data()
    colors = {"Critical": "#b30000", "High": "#e34a33", "Medium": "#fdbb84", "Low": "#2ca25f", "Data-Limited": "#999999"}
    markers_js = get_markers_js(data, colors)
    scatter_datasets = build_scatter_datasets(data)

    # Top-10 EDI excluding Data-Limited so the headline ranking is defensible
    top_10 = sorted([d for d in data if d['risk'] != 'Data-Limited'], key=lambda x: x['edi'], reverse=True)[:10]
    reg_labels = sorted(regions_events.keys())
    reg_vals = [regions_events[r] for r in reg_labels]
    tier_order = ["Critical", "High", "Medium", "Low", "Data-Limited"]
    tier_vals = [tier_counts.get(t, 0) for t in tier_order]
    tier_palette = [colors[t] for t in tier_order]
    n_data_limited = tier_counts.get('Data-Limited', 0)
    n_total = sum(tier_counts.values())

    # 1. INDEX.HTML — main map
    index_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Mali EDI Map</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ font-family: -apple-system, 'Segoe UI', sans-serif; margin: 0; }}
        #map {{ height: 100vh; width: 100%; }}
        .nav-btn {{ position: absolute; top: 20px; right: 20px; z-index: 1000; background: #1a2a3a; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: 600; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
        .header-info {{ position: absolute; top: 20px; left: 60px; z-index: 1000; background: white; padding: 12px 16px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); max-width: 380px; }}
        .header-info h1 {{ margin: 0 0 4px 0; font-size: 16px; color: #1a2a3a; }}
        .header-info p {{ margin: 0; font-size: 12px; color: #4a5568; line-height: 1.4; }}
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
        <p>Composite score combining ACLED conflict events and OCHA school closures, weighted by population. Grey markers = Data-Limited cercles where school-data coverage is insufficient; tier reflects conflict signal only.</p>
    </div>
    <div class="legend">
        <div class="row"><span class="swatch" style="background:#b30000"></span>Critical</div>
        <div class="row"><span class="swatch" style="background:#e34a33"></span>High</div>
        <div class="row"><span class="swatch" style="background:#fdbb84"></span>Medium</div>
        <div class="row"><span class="swatch" style="background:#2ca25f"></span>Low</div>
        <div class="row"><span class="swatch" style="background:#999999"></span>Data-Limited</div>
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

    # 2. DASHBOARD.HTML — 3-column single-screen layout. Map removed; scatter chart is centerpiece.
    dashboard_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Mali EDI Dashboard</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{ --navy: #1a2a3a; --bg: #f4f7f9; --border: #e2e8f0; --muted: #4a5568; }}
        * {{ box-sizing: border-box; }}
        body {{ font-family: -apple-system, 'Segoe UI', sans-serif; margin: 0; background: var(--bg); color: #1a202c; }}
        .header {{ background: var(--navy); color: white; padding: 16px 28px; display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ margin: 0; font-size: 20px; font-weight: 600; }}
        .header .meta {{ font-size: 13px; color: #cbd5e0; }}
        .header .meta a {{ color: #fee08b; text-decoration: none; margin-left: 16px; border: 1px solid #fee08b; padding: 4px 12px; border-radius: 4px; font-weight: 600; font-size: 12px; }}
        .container {{
            display: grid;
            grid-template-columns: minmax(280px, 22%) 1fr minmax(310px, 27%);
            grid-template-rows: 1fr 1fr;
            gap: 12px;
            padding: 12px;
            height: calc(100vh - 64px);
        }}
        .card {{ background: white; border-radius: 8px; padding: 14px 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); display: flex; flex-direction: column; min-height: 0; min-width: 0; overflow: hidden; }}
        .card h3 {{ margin: 0 0 6px 0; font-size: 11px; font-weight: 700; color: var(--navy); letter-spacing: 0.6px; text-transform: uppercase; padding-bottom: 8px; border-bottom: 1px solid var(--border); flex-shrink: 0; }}
        .card .sub {{ font-size: 11px; color: var(--muted); margin: 0 0 10px 0; line-height: 1.45; flex-shrink: 0; }}
        .chart-wrap {{ position: relative; flex: 1; min-height: 0; }}
        .scatter-card {{ grid-row: 1 / span 2; }}
        .note {{ font-size: 12px; line-height: 1.55; color: var(--muted); margin: 0; }}
        .note b {{ color: var(--navy); }}
        .note .stat {{ display: inline-block; padding: 1px 6px; background: #edf2f7; border-radius: 3px; font-weight: 600; color: var(--navy); }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Mali Education Disruption Index (EDI) Dashboard</h1>
        <div class="meta">Data Period: 2020 – 2024 <a href="index.html">View Map →</a></div>
    </div>
    <div class="container">
        <!-- Left column: donut (top), top-10 (bottom) -->
        <div class="card">
            <h3>Risk Distribution</h3>
            <div class="chart-wrap"><canvas id="donut"></canvas></div>
        </div>
        <div class="card">
            <h3>Top 10 Risk Cercles (EDI)</h3>
            <div class="chart-wrap"><canvas id="bar"></canvas></div>
        </div>

        <!-- Center: scatter chart spans both rows -->
        <div class="card scatter-card">
            <h3>Conflict Intensity × School Closure</h3>
            <p class="sub">Each bubble = one cercle. Size ∝ √population, color = region. <b>Hollow rings</b> mark cercles with limited or missing school-data coverage — closure signal not trustworthy. The chart separates two shortlists: cercles in the upper-right are flagged by both signals; cercles isolated on one axis tell EBI which signal is driving the assessment and where field verification matters most.</p>
            <div class="chart-wrap"><canvas id="scatter"></canvas></div>
        </div>

        <!-- Right column: regional bar (top), methodology note (bottom) -->
        <div class="card">
            <h3>Conflict Events by Region</h3>
            <div class="chart-wrap"><canvas id="reg"></canvas></div>
        </div>
        <div class="card">
            <h3>Methodology Note</h3>
            <p class="note"><span class="stat">{n_data_limited} of {n_total}</span> cercles are flagged <b>Data-Limited</b> — school-data coverage is insufficient to assess closure rate, so triage relies on the conflict signal and field-team verification. These are excluded from the Top 10 ranking to keep the headline list defensible.</p>
            <p class="note" style="margin-top:8px;">EDI weights: <b>60%</b> percentage of matched schools closed; <b>40%</b> ACLED conflict events per 100k population (2020–2024).</p>
            <p class="note" style="margin-top:8px;"><b>Sources:</b> ACLED, OCHA Mali school registry, OCHA admin-2 population estimates — all open data via HDX. Spatial view available on the <a href="index.html" style="color:var(--navy); font-weight:600;">map page</a>.</p>
        </div>
    </div>
    <script>
        new Chart(document.getElementById('donut'), {{
            type: 'doughnut',
            data: {{ labels: {json.dumps(tier_order)}, datasets: [{{ data: {json.dumps(tier_vals)}, backgroundColor: {json.dumps(tier_palette)}, borderWidth: 2, borderColor: '#fff' }}] }},
            options: {{
                maintainAspectRatio: false,
                cutout: '62%',
                plugins: {{
                    legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }}, boxWidth: 12, padding: 8 }} }},
                    tooltip: {{ callbacks: {{ label: function(ctx) {{ return ctx.label + ': ' + ctx.raw + ' cercles'; }} }} }}
                }}
            }}
        }});

        new Chart(document.getElementById('bar'), {{
            type: 'bar',
            data: {{ labels: {json.dumps([x['cercle'] for x in top_10])}, datasets: [{{ label: 'EDI', data: {json.dumps([x['edi'] for x in top_10])}, backgroundColor: '#1a2a3a', borderRadius: 3 }}] }},
            options: {{
                indexAxis: 'y',
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ beginAtZero: true, max: 0.8, grid: {{ color: '#edf2f7' }} }},
                    y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 11 }} }} }}
                }}
            }}
        }});

        new Chart(document.getElementById('reg'), {{
            type: 'bar',
            data: {{ labels: {json.dumps(reg_labels)}, datasets: [{{ label: 'Events', data: {json.dumps(reg_vals)}, backgroundColor: '#fdbb84', borderRadius: 3 }}] }},
            options: {{
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ ticks: {{ font: {{ size: 10 }}, maxRotation: 45, minRotation: 45 }}, grid: {{ display: false }} }},
                    y: {{ beginAtZero: true, grid: {{ color: '#edf2f7' }} }}
                }}
            }}
        }});

        new Chart(document.getElementById('scatter'), {{
            type: 'bubble',
            data: {{ datasets: {json.dumps(scatter_datasets)} }},
            options: {{
                maintainAspectRatio: false,
                scales: {{
                    x: {{ type: 'logarithmic', title: {{ display: true, text: 'Conflict events per 100k population (log scale)', font: {{ size: 11 }} }}, grid: {{ color: '#edf2f7' }} }},
                    y: {{ min: 0, max: 105, title: {{ display: true, text: '% of matched schools closed', font: {{ size: 11 }} }}, grid: {{ color: '#edf2f7' }} }}
                }},
                plugins: {{
                    legend: {{ position: 'right', labels: {{ font: {{ size: 10 }}, boxWidth: 10, padding: 6 }} }},
                    tooltip: {{ callbacks: {{ label: function(ctx) {{ var p = ctx.raw; return p.cercle + ' — EDI ' + p.edi + ' (' + p.risk + ', ' + p.coverage + ')'; }} }} }}
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
