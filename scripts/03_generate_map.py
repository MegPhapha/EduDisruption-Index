import csv
import json
import os

def generate_map():
    data = []
    with open('data/clean/mali_map_data.csv', mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in ['lat', 'lng', 'edi', 'total_schools', 'closed_schools', 'pct_closed', 'total_conflict_events', 'events_per_100k', 'population']:
                row[key] = float(row[key])
            data.append(row)

    top_5 = sorted(data, key=lambda x: x['edi'], reverse=True)[:5]

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
                <h3 style='margin:0 0 5px 0; color:#2c3e50;'>{r['cercle']}</h3>
                <span style='color: white; background: {color}; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; font-weight: bold;'>{r['risk']} RISK</span>
                <hr style='border: 0; border-top: 1px solid #eee; margin: 10px 0;'>
                <table style='width: 100%; font-size: 0.9em;'>
                    <tr><td><b>Region:</b></td><td align='right'>{r['region']}</td></tr>
                    <tr><td><b>EDI Score:</b></td><td align='right'>{r['edi']}</td></tr>
                    <tr><td><b>Schools:</b></td><td align='right'>{int(r['total_schools'])}</td></tr>
                    <tr><td><b>Closed:</b></td><td align='right' style='color:red;'>{int(r['closed_schools'])}</td></tr>
                    <tr><td><b>Events:</b></td><td align='right'>{int(r['total_conflict_events'])}</td></tr>
                </table>
            </div>
        """
        markers_js += f"""
        L.circleMarker([{r['lat']}, {r['lng']}], {{
            radius: {max(6, r['edi'] * 25)},
            fillColor: "{color}",
            color: "#fff",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.85
        }}).addTo(map).bindPopup(`{popup}`);
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mali EDI Map</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; }}
            #map {{ flex-grow: 1; }}
            .header {{ background: #1a2a3a; color: white; padding: 20px 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); z-index: 1000; }}
            .header h1 {{ margin: 0; font-size: 24px; letter-spacing: -0.5px; }}
            .header p {{ margin: 5px 0 0 0; opacity: 0.8; font-size: 14px; }}
            .legend {{ background: white; padding: 15px; line-height: 1.5em; border-radius: 8px; box-shadow: 0 1px 5px rgba(0,0,0,0.1); border: none; }}
            .legend i {{ width: 18px; height: 18px; float: left; margin-right: 10px; border-radius: 50%; }}
            .info-panel {{
                position: absolute; top: 100px; left: 20px; width: 250px;
                background: white; padding: 20px; border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1); z-index: 1000;
            }}
            .info-panel h2 {{ margin: 0 0 15px 0; font-size: 16px; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 5px; }}
            .top-item {{ display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 13px; }}
            .top-name {{ font-weight: bold; }}
            .top-score {{ color: #e34a33; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Mali Education Disruption Index (EDI)</h1>
            <p>Geospatial analysis of conflict impact and school accessibility (2020-2024)</p>
        </div>
        <div class="info-panel">
            <h2>Highest Risk Areas</h2>
            {''.join([f'<div class="top-item"><span class="top-name">{x["cercle"]}</span><span class="top-score">{x["edi"]}</span></div>' for x in top_5])}
        </div>
        <div id="map"></div>
        <script>
            var map = L.map('map', {{ zoomControl: false }}).setView([17.5, -4.0], 6);
            L.control.zoom({{ position: 'topright' }}).addTo(map);

            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 20
            }}).addTo(map);

            // BOLD BORDER FOR MALI
            fetch('https://raw.githubusercontent.com/datasets/geo-boundaries-world-110m/master/countries/MLI.geojson')
                .then(response => response.json())
                .then(data => {{
                    L.geoJSON(data, {{
                        style: {{
                            color: "#2c3e50",
                            weight: 4,
                            fillOpacity: 0.05,
                            dashArray: '5, 10'
                        }}
                    }}).addTo(map);
                }});

            {markers_js}

            var legend = L.control({{position: 'bottomright'}});
            legend.onAdd = function (map) {{
                var div = L.DomUtil.create('div', 'legend'),
                    grades = ["Critical", "High", "Medium", "Low"],
                    labels = {json.dumps(colors)};
                div.innerHTML = '<b style="margin-bottom:10px; display:block;">Risk Level</b>';
                for (var i = 0; i < grades.length; i++) {{
                    div.innerHTML +=
                        '<i style="background:' + labels[grades[i]] + '"></i> ' +
                        grades[i] + '<br>';
                }}
                return div;
            }};
            legend.addTo(map);
        </script>
    </body>
    </html>
    """

    os.makedirs('outputs', exist_ok=True)
    with open('outputs/mali_edi_map.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Map generated: outputs/mali_edi_map.html")

if __name__ == "__main__":
    generate_map()
