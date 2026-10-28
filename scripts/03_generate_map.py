import csv
import json
import os
from collections import Counter
from utils import normalize

def load_data():
    data = []
    regions_events = Counter()
    tier_counts = Counter()
    coverage_counts = Counter()
    with open('data/clean/mali_map_data.csv', mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in ['lat', 'lng', 'edi', 'total_schools', 'closed_schools', 'pct_closed', 'total_conflict_events', 'events_per_100k', 'fatalities', 'fatalities_per_100k', 'population']:
                row[key] = float(row[key])
            data.append(row)
            regions_events[row['region']] += int(row['total_conflict_events'])
            tier_counts[row['risk']] += 1
            coverage_counts[row['coverage']] += 1
    return data, regions_events, tier_counts, coverage_counts

TIER_ACTIONS = {
    'Critical': 'Field-validate first',
    'High': 'Next phase of assessment',
    'Medium': 'Monitor; sequence later',
    'Low': 'Comparatively stable',
    'Data-Limited': 'Verify data before ruling out',
}

# Score components, matching the formula in 02_build_index.py.
COMPONENTS = [
    ('Closures', 'pct_closed', 0.5, '#1a2a3a'),
    ('Events', 'events_per_100k', 0.25, '#5b7fa6'),
    ('Fatalities', 'fatalities_per_100k', 0.25, '#a9bdd3'),
]

def score_breakdown(r, maxima):
    parts = [(label, (r[key] / maxima[key]) * w if maxima[key] else 0, color) for label, key, w, color in COMPONENTS]
    bar = ''.join(f"<span style='display:block; width:{v * 100:.1f}%; background:{c};'></span>" for _, v, c in parts)
    keys = ' · '.join(f"<span style='color:{c}'>■</span> {label} {v:.2f}" for label, v, c in parts)
    gap = "<div style='color:#718096; margin-top:4px;'>No reliable school data, so the closure component may be understated.</div>" if r['coverage'] in ('Limited', 'Conflict-only') else ''
    return f"""
                <div style='font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#1a2a3a; margin:10px 0 4px;'>What drives the score</div>
                <div style='display:flex; height:10px; background:#edf2f7; border-radius:2px; overflow:hidden;'>{bar}</div>
                <div style='font-size:11px; color:#4a5568; margin-top:4px;'>{keys} = <b>{r['edi']}</b> of a possible 1.0{gap}</div>"""

def build_popup(r, colors, maxima):
    color = colors.get(r['risk'], "#999999")
    return f"""
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
                    <tr><td><b>Fatalities:</b></td><td align='right'>{int(r['fatalities'])} ({r['fatalities_per_100k']}/100k)</td></tr>
                </table>{score_breakdown(r, maxima)}
            </div>
        """

def _round_coords(c):
    return [_round_coords(x) for x in c] if isinstance(c[0], list) else [round(c[0], 3), round(c[1], 3)]

def load_boundaries(data, colors):
    # geoBoundaries names are unaccented; one spelling also differs from the OCHA population file.
    aliases = {'baraoueli': 'baroueli'}
    maxima = {key: max(r[key] for r in data) for _, key, _, _ in COMPONENTS}
    by_name = {aliases.get(normalize(r['cercle']), normalize(r['cercle'])): r for r in data}
    with open('data/raw/geoBoundaries-MLI-ADM2_simplified.geojson', encoding='utf-8') as f:
        geo = json.load(f)
    features = []
    for feat in geo['features']:
        r = by_name.get(normalize(feat['properties']['shapeName']))
        if r is None:
            raise ValueError(f"No EDI row for boundary {feat['properties']['shapeName']}")
        geom = feat['geometry']
        features.append({
            'type': 'Feature',
            'properties': {'cercle': r['cercle'], 'risk': r['risk'], 'popup': build_popup(r, colors, maxima)},
            'geometry': {'type': geom['type'], 'coordinates': _round_coords(geom['coordinates'])},
        })
    if len(features) != len(data):
        raise ValueError(f"{len(data) - len(features)} cercles have no boundary")
    return {'type': 'FeatureCollection', 'features': features}

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
    boundaries = load_boundaries(data, colors)
    scatter_datasets = build_scatter_datasets(data)

    # Top-10 EDI excluding Data-Limited so the headline ranking is defensible
    top_10 = sorted([d for d in data if d['risk'] != 'Data-Limited'], key=lambda x: x['edi'], reverse=True)[:10]
    reg_labels = sorted(regions_events.keys())
    reg_vals = [regions_events[r] for r in reg_labels]
    tier_order = ["Critical", "High", "Medium", "Low", "Data-Limited"]
    tier_vals = [tier_counts.get(t, 0) for t in tier_order]
    tier_palette = [colors[t] for t in tier_order]
    n_data_limited = tier_counts.get('Data-Limited', 0)
    n_high = tier_counts.get('High', 0)
    n_critical = tier_counts.get('Critical', 0)
    n_total = sum(tier_counts.values())

    # Stats for the "Mali at a Glance" callout card
    top_cercle = top_10[0]['cercle'] if top_10 else '—'
    top_edi = top_10[0]['edi'] if top_10 else 0
    top_region = max(regions_events, key=regions_events.get) if regions_events else '—'
    top_region_events = regions_events[top_region] if regions_events else 0
    # Per-cercle bar colour: Critical bars in dark red, others navy.
    top_10_colors = ['#b30000' if c['risk'] == 'Critical' else '#1a2a3a' for c in top_10]

    # 1. INDEX.HTML — main map, with a narrative side panel
    # Panel numbers, all computed from the data so they can never drift from it.
    tot_events = sum(int(d['total_conflict_events']) for d in data)
    tot_fatalities = sum(int(d['fatalities']) for d in data)
    tot_schools = sum(int(d['total_schools']) for d in data)
    tot_closed = sum(int(d['closed_schools']) for d in data)
    pct_closed_all = round(tot_closed / tot_schools * 100) if tot_schools else 0
    crit_rows = sorted([d for d in data if d['risk'] == 'Critical'], key=lambda x: x['edi'], reverse=True)
    crit_pop = sum(d['population'] for d in crit_rows)

    # Group the Critical cercles into named geographic clusters, cards cover all of them.
    cluster_meta = [
        ('Gao', 'Niger River corridor (Gao)', "Along the Niger river and the border with Niger, where per-capita conflict is highest."),
        ('Tombouctou', 'Tombouctou cercle', "The region-capital cercle, carrying a heavy 2020–2024 conflict record on top of full closure."),
        ('Mopti', 'Central plateau (Mopti)', "Central Mali's conflict epicentre on the Burkina Faso border."),
    ]
    cluster_cards = ""
    for region, title, blurb in cluster_meta:
        members = [d for d in crit_rows if d['region'] == region]
        if not members:
            continue
        names = [d['cercle'] for d in members]
        closed = sum(int(d['closed_schools']) for d in members)
        schools = sum(int(d['total_schools']) for d in members)
        plural = 's' if len(members) > 1 else ''
        cluster_cards += f"""
            <div class="cluster" role="button" tabindex="0" data-cercles='{json.dumps(names)}' title="Zoom to these cercles">
                <div class="cluster-count">{len(members)} critical cercle{plural}</div>
                <div class="cluster-title">{title}</div>
                <div class="cluster-names">{', '.join(names)}</div>
                <div class="cluster-blurb">{blurb} {closed} of {schools} matched schools closed.</div>
            </div>"""

    # Headline answer, e.g. "5 of 50 cercles reach the Critical tier: 2 in Gao, 2 in Mopti, 1 in Tombouctou."
    crit_by_region = Counter(d['region'] for d in crit_rows)
    crit_split = ', '.join(f"{n} in {reg}" for reg, n in sorted(crit_by_region.items(), key=lambda x: (-x[1], x[0])))
    legend_rows = ''.join(
        f'<div class="row"><span class="swatch{" dashed" if t == "Data-Limited" else ""}" style="background:{colors[t]}"></span>'
        f'<div><b>{t}</b> <span class="n">({tier_counts.get(t, 0)})</span><div class="action">{TIER_ACTIONS[t]}</div></div></div>'
        for t in tier_order
    )

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
        .nav-btn {{ position: absolute; top: 20px; right: 20px; z-index: 1000; background: #fee08b; color: #1a2a3a; padding: 14px 22px; text-decoration: none; border-radius: 6px; font-weight: 700; font-size: 15px; letter-spacing: 0.3px; box-shadow: 0 4px 14px rgba(0,0,0,0.25), 0 0 0 3px rgba(254, 224, 139, 0.35); transition: transform 0.15s ease, box-shadow 0.15s ease; display: inline-flex; align-items: center; gap: 8px; }}
        .nav-btn:hover {{ transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0,0,0,0.3), 0 0 0 4px rgba(254, 224, 139, 0.5); }}
        .nav-btn .icon {{ font-size: 18px; line-height: 1; }}
        .story-toggle {{ position: absolute; top: 20px; left: 20px; z-index: 1100; background: #1a2a3a; color: #fff; border: none; padding: 10px 16px; border-radius: 6px; font-weight: 700; font-size: 14px; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.3); font-family: inherit; }}
        .story-toggle:hover {{ background: #2c415c; }}
        #story {{ position: absolute; top: 0; left: 0; bottom: 0; width: min(400px, 92vw); background: rgba(255,255,255,0.97); z-index: 1050; overflow-y: auto; padding: 70px 20px 20px; box-shadow: 2px 0 14px rgba(0,0,0,0.18); transform: translateX(-102%); transition: transform 0.25s ease; }}
        #story.open {{ transform: none; }}
        #story h1 {{ margin: 6px 0 6px 0; font-size: 19px; color: #1a2a3a; }}
        #story .lede {{ margin: 0 0 14px 0; font-size: 13px; color: #4a5568; line-height: 1.5; font-style: italic; }}
        #story h2 {{ font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; color: #1a2a3a; margin: 18px 0 8px 0; padding-top: 12px; border-top: 1px solid #e2e8f0; }}
        .stats-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
        .stats-row .stat {{ background: #f7fafc; border-left: 3px solid #1a2a3a; border-radius: 6px; padding: 8px 10px; }}
        .stat-num {{ font-size: 22px; font-weight: 700; color: #1a2a3a; line-height: 1; }}
        .stat-label {{ font-size: 10.5px; color: #4a5568; margin-top: 3px; line-height: 1.35; }}
        .stat-label span {{ display: block; color: #718096; font-size: 9.5px; margin-top: 1px; }}
        #story .headline {{ margin: 0 0 14px 0; font-size: 14px; color: #1a2a3a; line-height: 1.5; }}
        #story .headline b {{ color: #b30000; }}
        .cluster {{ border: 1px solid #e2e8f0; border-left: 3px solid #b30000; border-radius: 6px; padding: 9px 11px; margin-bottom: 8px; background: #fff; }}
        .cluster[role=button] {{ cursor: pointer; transition: box-shadow 0.15s ease; }}
        .cluster[role=button]:hover, .cluster[role=button]:focus {{ box-shadow: 0 2px 8px rgba(0,0,0,0.15); outline: none; }}
        .cluster.gap {{ border-left-color: #999; }}
        .cluster-count {{ font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; color: #b30000; }}
        .cluster.gap .cluster-count {{ color: #718096; }}
        .cluster-title {{ font-size: 14px; font-weight: 700; color: #1a2a3a; margin: 2px 0; }}
        .cluster-names {{ font-size: 12px; color: #2d3748; }}
        .cluster-blurb {{ font-size: 11.5px; color: #4a5568; line-height: 1.45; margin-top: 3px; }}
        .prose {{ font-size: 12.5px; color: #4a5568; line-height: 1.55; margin: 0; }}
        .prose a {{ color: #1a2a3a; font-weight: 600; }}
        .footnote {{ font-size: 11.5px; color: #718096; margin: 2px 0 0 0; line-height: 1.5; }}
        .sources {{ font-size: 11.5px; color: #4a5568; line-height: 1.5; margin: 0; padding-left: 16px; }}
        .disclaimer {{ font-size: 11.5px; color: #1a2a3a; background: #fff8e1; border-left: 3px solid #fee08b; border-radius: 4px; padding: 8px 10px; margin: 14px 0 0 0; line-height: 1.5; }}
        .legend {{ position: absolute; top: 76px; right: 20px; z-index: 1000; background: white; padding: 10px 14px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); font-size: 12px; }}
        .legend .title {{ font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; color: #1a2a3a; margin-bottom: 4px; }}
        .legend .row {{ display: flex; align-items: flex-start; margin: 5px 0; }}
        .legend .swatch {{ width: 14px; height: 14px; border-radius: 3px; margin: 1px 8px 0 0; flex-shrink: 0; }}
        .legend .dashed {{ outline: 1.5px dashed #555; outline-offset: -1.5px; }}
        .legend .n {{ color: #718096; }}
        .legend .action {{ font-size: 10.5px; color: #4a5568; }}
        .crit-label {{ background: transparent; border: none; box-shadow: none; color: #fff; font-weight: 700; font-size: 11px; text-shadow: 0 0 3px #000, 0 0 2px #000; padding: 0; }}
        .crit-label::before {{ display: none; }}
        @media (max-width: 700px) {{ .legend .action {{ display: none; }} }}
    </style>
</head>
<body>
    <a href="dashboard.html" class="nav-btn"><span class="icon">📊</span>Open Analytics Dashboard →</a>
    <button id="story-toggle" class="story-toggle">☰ Story</button>
    <aside id="story" class="open">
        <h1>Mali Education Disruption Index</h1>
        <p class="lede">Where is education access most likely to be disrupted, and where should resources be focused first?</p>
        <p class="headline"><b>{n_critical} of {n_total} cercles</b> reach the Critical tier: {crit_split}. These are where field validation should start.</p>
        <div class="stats-row">
            <div class="stat"><div class="stat-num">{tot_events:,}</div><div class="stat-label">Conflict events recorded, 2020–2024<span>ACLED</span></div></div>
            <div class="stat"><div class="stat-num">{tot_fatalities:,}</div><div class="stat-label">Conflict fatalities recorded, 2020–2024<span>ACLED</span></div></div>
            <div class="stat"><div class="stat-num">{pct_closed_all}%</div><div class="stat-label">Matched schools closed ({tot_closed:,} of {tot_schools:,})<span>OCHA Mali school registry</span></div></div>
            <div class="stat"><div class="stat-num">{n_critical}</div><div class="stat-label">Critical cercles — ~{int(round(crit_pop / 1000)):,}k people<span>this map's headline list</span></div></div>
        </div>
        <h2>Priority clusters</h2>
        {cluster_cards}
        <div class="cluster gap">
            <div class="cluster-count">The data gap</div>
            <div class="cluster-title">{n_data_limited} of {n_total} cercles</div>
            <div class="cluster-names">Data-Limited</div>
            <div class="cluster-blurb">School-data coverage too thin to score closures. Grey cercles reflect conflict signal only — field verification needed before these cercles can be ruled out.</div>
        </div>
        <p class="footnote">The cards above cover all {n_critical} Critical cercles; click one to zoom to it. {n_high} more sit in the High tier. Click any cercle on the map for the numbers driving its score.</p>
        <h2>How to read this map</h2>
        <p class="prose">Each cercle is scored on three indicators: share of matched schools closed (<b>50%</b>), ACLED conflict events per 100k people (<b>25%</b>), and fatalities per 100k (<b>25%</b>), 2020–2024, each normalised to the dataset maximum. Colour shows the tier, and Critical cercles are labelled by name. <b>Grey, dash-outlined cercles are Data-Limited</b>: scored on conflict intensity only.</p>
        <h2>A note on field knowledge</h2>
        <p class="prose">This map is a starting point for conversation, not an answer. Where it disagrees with what education teams know on the ground, the disagreement itself is the most useful finding: it points either to a data gap or to a ground condition the data cannot see. Both improve the method.</p>
        <h2>Inspect the evidence</h2>
        <p class="prose">Every figure on this page is computed from open data by the pipeline in <a href="https://github.com/MegPhapha/EduDisruption-Index/tree/main/scripts">scripts/</a>. Scoring rules and limitations in <a href="https://github.com/MegPhapha/EduDisruption-Index/blob/main/METHODOLOGY.md">METHODOLOGY.md</a>; source details in <a href="https://github.com/MegPhapha/EduDisruption-Index/blob/main/data/raw/SOURCES.md">SOURCES.md</a>. Continue to the <a href="dashboard.html">analytics dashboard</a>.</p>
        <h2>Sources</h2>
        <ul class="sources">
            <li>Conflict events and fatalities: ACLED, 2020–2024, via HDX</li>
            <li>School status: OCHA Mali school registry (2023), via HDX</li>
            <li>Population: OCHA Mali admin-2 estimates (2020), via HDX</li>
            <li>Cercle boundaries: geoBoundaries (OCHA / DNCT, CC BY 4.0)</li>
        </ul>
        <p class="disclaimer"><b>Proof of concept.</b> Tiers rank relative risk across Mali's {n_total} cercles; they are not a needs assessment. Field validation is required before any planning decision.</p>
    </aside>
    <div class="legend">
        <div class="title">Priority tier</div>
        {legend_rows}
    </div>
    <div id="map"></div>
    <script>
        var panel = document.getElementById('story');
        var toggle = document.getElementById('story-toggle');
        if (window.innerWidth < 700) panel.classList.remove('open');
        toggle.addEventListener('click', function() {{ panel.classList.toggle('open'); }});
        var map = L.map('map').setView([16.5, -4.0], 6);
        // CARTO basemaps now require an API key; Esri's light-grey canvas does not.
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ attribution: 'Tiles &copy; Esri &middot; boundaries &copy; geoBoundaries', maxZoom: 16 }}).addTo(map);
        var colors = {json.dumps(colors)};
        function baseStyle(f) {{
            var limited = f.properties.risk === 'Data-Limited';
            return {{ fillColor: colors[f.properties.risk], fillOpacity: limited ? 0.45 : 0.8, color: limited ? '#555' : '#fff', weight: 1, dashArray: limited ? '4 3' : null }};
        }}
        var layers = {{}};
        var cercles = L.geoJSON({json.dumps(boundaries, ensure_ascii=False, separators=(',', ':'))}, {{
            style: baseStyle,
            onEachFeature: function(f, layer) {{
                layers[f.properties.cercle] = layer;
                layer.bindPopup(f.properties.popup, {{ maxWidth: 300 }});
                if (f.properties.risk === 'Critical') {{
                    layer.bindTooltip(f.properties.cercle, {{ permanent: true, direction: 'center', className: 'crit-label' }});
                }} else {{
                    layer.bindTooltip(f.properties.cercle + ' · ' + f.properties.risk, {{ sticky: true }});
                }}
                layer.on('mouseover', function() {{ layer.setStyle({{ weight: 3, color: '#1a2a3a' }}); layer.bringToFront(); }});
                layer.on('mouseout', function() {{ cercles.resetStyle(layer); }});
            }}
        }}).addTo(map);
        map.fitBounds(cercles.getBounds(), {{ paddingTopLeft: [panel.classList.contains('open') ? 400 : 0, 0] }});
        document.querySelectorAll('.cluster[data-cercles]').forEach(function(card) {{
            function zoom() {{
                var group = L.featureGroup(JSON.parse(card.dataset.cercles).map(function(n) {{ return layers[n]; }}));
                var small = window.innerWidth < 700;
                if (small) panel.classList.remove('open');
                map.fitBounds(group.getBounds(), {{ paddingTopLeft: [small ? 20 : 420, 20], paddingBottomRight: [20, 20], maxZoom: 8 }});
            }}
            card.addEventListener('click', zoom);
            card.addEventListener('keydown', function(e) {{ if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); zoom(); }} }});
        }});
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
        .note {{ font-size: 12px; line-height: 1.55; color: var(--muted); margin: 0; }}
        .note b {{ color: var(--navy); }}
        .note .stat {{ display: inline-block; padding: 1px 6px; background: #edf2f7; border-radius: 3px; font-weight: 600; color: var(--navy); }}
        .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 8px; flex: 1; min-height: 0; }}
        .stat {{ display: flex; flex-direction: column; justify-content: center; padding: 8px 10px; background: #f7fafc; border-radius: 6px; border-left: 3px solid var(--navy); min-height: 0; }}
        .stat-num {{ font-size: 26px; font-weight: 700; color: var(--navy); line-height: 1; }}
        .stat-label {{ font-size: 10px; color: var(--muted); margin-top: 4px; line-height: 1.3; text-transform: none; letter-spacing: 0; font-weight: 400; }}
        .stat-label .sublabel {{ display: block; color: #718096; font-size: 9px; margin-top: 1px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Mali Education Disruption Index (EDI) Dashboard</h1>
        <div class="meta">Data Period: 2020 – 2024 <a href="index.html">View Map →</a></div>
    </div>
    <div class="container">
        <!-- Top row: Top 10 (left), Scatter (middle, landscape), Region (right) -->
        <div class="card">
            <h3>Top 10 Risk Cercles (EDI)</h3>
            <div class="chart-wrap"><canvas id="bar"></canvas></div>
        </div>
        <div class="card">
            <h3>Conflict Intensity × School Closure</h3>
            <p class="sub">Each bubble = one cercle. Size ∝ √population, color = region. <b>Hollow rings</b> mark cercles with limited or missing school-data coverage. Upper-right = both signals firing; right edge alone = conflict-only watch list.</p>
            <div class="chart-wrap"><canvas id="scatter"></canvas></div>
        </div>
        <div class="card">
            <h3>Conflict Events by Region</h3>
            <div class="chart-wrap"><canvas id="reg"></canvas></div>
        </div>

        <!-- Bottom row: Donut (left), Stats callout (middle), Methodology (right) -->
        <div class="card">
            <h3>Risk Distribution</h3>
            <div class="chart-wrap"><canvas id="donut"></canvas></div>
        </div>
        <div class="card">
            <h3>Mali at a Glance</h3>
            <div class="stats-grid">
                <div class="stat" style="border-left-color:#b30000;">
                    <div class="stat-num">{n_critical}</div>
                    <div class="stat-label">Critical cercles<span class="sublabel">immediate assessment</span></div>
                </div>
                <div class="stat">
                    <div class="stat-num">{n_data_limited}</div>
                    <div class="stat-label">Data-Limited cercles<span class="sublabel">need field verification</span></div>
                </div>
                <div class="stat">
                    <div class="stat-num">{top_edi}</div>
                    <div class="stat-label">Highest EDI<span class="sublabel">{top_cercle}</span></div>
                </div>
                <div class="stat">
                    <div class="stat-num">{top_region_events:,}</div>
                    <div class="stat-label">Most conflict events<span class="sublabel">{top_region} region (2020–2024)</span></div>
                </div>
            </div>
        </div>
        <div class="card">
            <h3>Methodology Note</h3>
            <p class="note"><b style="color:#b30000;">Critical Tier</b> = top 5 cercles with reliable school-data coverage. <span class="stat">{n_data_limited} of {n_total}</span> cercles are flagged <b>Data-Limited</b> — coverage too thin to trust the closure signal; triage falls to field-team verification.</p>
            <p class="note" style="margin-top:8px;">EDI weights: <b>50%</b> closure rate · <b>25%</b> ACLED events / 100k · <b>25%</b> fatalities / 100k (2020–2024). Each input normalised to dataset max.</p>
            <p class="note" style="margin-top:8px;"><b>Sources:</b> ACLED, OCHA Mali school registry, OCHA admin-2 population — via HDX. See <a href="https://github.com/MegPhapha/EduDisruption-Index/blob/main/METHODOLOGY.md" style="color:var(--navy); font-weight:600;">METHODOLOGY.md</a> for full detail. Spatial view on the <a href="index.html" style="color:var(--navy); font-weight:600;">map page</a>.</p>
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
            data: {{ labels: {json.dumps([x['cercle'] for x in top_10])}, datasets: [{{ label: 'EDI', data: {json.dumps([x['edi'] for x in top_10])}, backgroundColor: {json.dumps(top_10_colors)}, borderRadius: 3 }}] }},
            options: {{
                indexAxis: 'y',
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ beginAtZero: true, max: 0.7, grid: {{ color: '#edf2f7' }} }},
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
