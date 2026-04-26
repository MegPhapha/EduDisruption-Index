import csv
import json
import os

def generate_map():
    data = []
    with open('data/clean/mali_map_data.csv', mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            for key in ['lat', 'lng', 'edi', 'total_schools', 'closed_schools', 'pct_closed', 'total_conflict_events', 'events_per_100k', 'population']:
                row[key] = float(row[key])
            data.append(row)

    # Color function for risk tiers
    colors = {
        "Critical": "#d73027", # Red
        "High": "#f46d43",     # Orange-Red
        "Medium": "#fee08b",   # Yellow
        "Low": "#1a9850"       # Green
    }

    # Build markers JS
    markers_js = ""
    for r in data:
        color = colors.get(r['risk'], "#999999")
        popup = f"""
            <b>Cercle: {r['cercle']}</b><br>
            Region: {r['region']}<br>
            Risk Tier: {r['risk']}<br>
            EDI Score: {r['edi']}<br><br>
            Schools: {int(r['total_schools'])} ({int(r['closed_schools'])} closed)<br>
            % Closed: {r['pct_closed']}%<br>
            Conflict Events: {int(r['total_conflict_events'])}<br>
            Events per 100k: {r['events_per_100k']}
        """
        markers_js += f"""
        L.circleMarker([{r['lat']}, {r['lng']}], {{
            radius: {max(5, r['edi'] * 20)},
            fillColor: "{color}",
            color: "#000",
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
        }}).addTo(map).bindPopup(`{popup}`);
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mali Education Disruption Index Map</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            #map {{ height: 800px; width: 100%; }}
            body {{ font-family: sans-serif; margin: 0; }}
            .legend {{
                background: white;
                padding: 10px;
                line-height: 1.5em;
                border: 1px solid gray;
                border-radius: 5px;
            }}
            .legend i {{
                width: 18px;
                height: 18px;
                float: left;
                margin-right: 8px;
                opacity: 0.7;
            }}
        </style>
    </head>
    <body>
        <div style="padding: 15px; background: #2c3e50; color: white;">
            <h1>Mali Education Disruption Index (EDI)</h1>
            <p>Risk prioritization based on School Closures and Conflict Intensity (2020-2024)</p>
        </div>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([17.57, -3.99], 6);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);

            {markers_js}

            var legend = L.control({{position: 'bottomright'}});
            legend.onAdd = function (map) {{
                var div = L.DomUtil.create('div', 'legend'),
                    grades = ["Critical", "High", "Medium", "Low"],
                    labels = {json.dumps(colors)};
                div.innerHTML = '<b>Risk Tiers</b><br>';
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
