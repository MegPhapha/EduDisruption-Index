import zipfile
import xml.etree.ElementTree as ET
import csv
import os
from utils import normalize

def read_xlsx_stateful(file_path, sheet_idx, col_map, row_start):
    results = []
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        strings = []
        try:
            with zip_ref.open('xl/sharedStrings.xml') as f:
                tree = ET.parse(f)
                for el in tree.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                    strings.append(el.text if el.text else "")
        except: pass
        
        sheet_files = sorted([f for f in zip_ref.namelist() if 'worksheets/sheet' in f])
        with zip_ref.open(sheet_files[sheet_idx]) as f:
            tree = ET.parse(f)
            ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            
            # State for backfilling
            current_state = {v: None for v in col_map.values()}
            
            for row in tree.findall('.//main:row', ns):
                if int(row.get('r')) < row_start: continue
                
                row_data = {}
                for cell in row.findall('main:c', ns):
                    col = ''.join(filter(str.isalpha, cell.get('r')))
                    if col in col_map:
                        v = cell.find('main:v', ns)
                        is_node = cell.find('main:is/main:t', ns)
                        val = None
                        if v is not None:
                            val = v.text
                            if cell.get('t') == 's': val = strings[int(val)]
                        elif is_node is not None:
                            val = is_node.text
                        
                        if val:
                            current_state[col_map[col]] = val
                
                # Copy current state into results
                if any(current_state.values()):
                    results.append(current_state.copy())
    return results

# Schools: K=Cercle, X=Statut, AE=Lat, AF=Lon
s_map = {'K': 'cercle', 'X': 'statut', 'AE': 'lat', 'AF': 'lon'}
schools = read_xlsx_stateful('data/raw/mali_schools_2023.xlsx', 2, s_map, 4)

schools_stats = {}
for r in schools:
    c_raw = r.get('cercle')
    if c_raw and r.get('lat') and r.get('lon'):
        c_key = normalize(c_raw)
        if c_key not in schools_stats: schools_stats[c_key] = {'total': 0, 'closed': 0}
        schools_stats[c_key]['total'] += 1
        if normalize(r.get('statut')) in ['non', 'ferme']:
            schools_stats[c_key]['closed'] += 1

# ACLED: C=Cercle, G=Year, H=Events, I=Fatalities
# Based on headers: C=Admin2, G=Month, H=Year, I=Events, J=Fatalities
a_map = {'C': 'cercle', 'H': 'year', 'I': 'events', 'J': 'fatalities'}
acled = read_xlsx_stateful('data/raw/acled_mali_summary.xlsx', 1, a_map, 2)

conflict_stats = {}
for r in acled:
    c_raw = r.get('cercle')
    year = r.get('year')
    if c_raw and year and str(year).isdigit():
        y_int = int(year)
        if 2020 <= y_int <= 2024:
            c_key = normalize(c_raw)
            if c_key not in conflict_stats: conflict_stats[c_key] = {'events': 0, 'fatalities': 0}
            events = r.get('events', '0')
            fatalities = r.get('fatalities', '0')
            conflict_stats[c_key]['events'] += int(events if events else 0)
            conflict_stats[c_key]['fatalities'] += int(fatalities if fatalities else 0)

# Population
pop_lookup = {}
with open('data/raw/mali_population_admin2_2020.csv', mode='r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for r in reader:
        c_orig = r['admin2Name_fr']
        c_key = normalize(c_orig)
        pop_lookup[c_key] = {'display_name': c_orig, 'region': r['admin1Name_fr'], 'pop': int(r['T_TL'])}

# Combine
final = []
for c_key, p in pop_lookup.items():
    s = schools_stats.get(c_key, {'total': 0, 'closed': 0})
    c = conflict_stats.get(c_key, {'events': 0, 'fatalities': 0})
    
    pct_closed = (s['closed'] / s['total'] * 100) if s['total'] > 0 else 0
    events_100k = (c['events'] / p['pop'] * 100000) if p['pop'] > 0 else 0
    
    final.append({
        'cercle': p['display_name'], 'region': p['region'], 'total_schools': s['total'],
        'closed_schools': s['closed'], 'pct_closed': pct_closed,
        'total_conflict_events': c['events'], 'population': p['pop'], 'events_per_100k': events_100k
    })

max_pct = max([r['pct_closed'] for r in final]) if final else 1
max_events = max([r['events_per_100k'] for r in final]) if final else 1

tier_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
for row in final:
    n_c = row['pct_closed'] / max_pct if max_pct > 0 else 0
    n_e = row['events_per_100k'] / max_events if max_events > 0 else 0
    edi = round((n_c * 0.6) + (n_e * 0.4), 3)
    row['EDI_score'] = edi
    if edi >= 0.7: row['risk_tier'] = "Critical"
    elif edi >= 0.4: row['risk_tier'] = "High"
    elif edi >= 0.2: row['risk_tier'] = "Medium"
    else: row['risk_tier'] = "Low"
    tier_counts[row['risk_tier']] += 1

final.sort(key=lambda x: x['EDI_score'], reverse=True)
os.makedirs('data/clean', exist_ok=True)
with open('data/clean/mali_disruption_summary.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=final[0].keys())
    writer.writeheader()
    writer.writerows(final)

print("\nTOP 15 CERLCES BY EDI SCORE:")
header = f"{'Cercle':<15} | {'Region':<12} | {'Schools':<7} | {'Closed':<6} | {'Events':<6} | {'Pop':<9} | {'EDI':<6} | {'Tier'}"
print(header)
print("-" * len(header))
for r in final[:15]:
    print(f"{r['cercle']:<15} | {r['region']:<12} | {r['total_schools']:<7} | {r['closed_schools']:<6} | {r['total_conflict_events']:<6} | {r['population']:<9} | {r['EDI_score']:<6} | {r['risk_tier']}")

print(f"\nMATCHING SUMMARY:\n  - Cercles in Pop: {len(pop_lookup)}\n  - Cercles with Schools: {len(schools_stats)}\n  - Cercles with Conflict: {len(conflict_stats)}")
print("\nRISK TIER COUNTS:")
for t, count in tier_counts.items(): print(f"  - {t}: {count}")
