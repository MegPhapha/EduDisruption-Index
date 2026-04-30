import zipfile
import xml.etree.ElementTree as ET
import csv
import os
from utils import normalize

# 1. Load official cercles and population
pop_lookup = {}
with open('data/raw/mali_population_admin2_2020.csv', mode='r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        orig = row['admin2Name_fr']
        pop_lookup[normalize(orig)] = {'display_name': orig, 'region': row['admin1Name_fr'], 'pop': int(row['T_TL'])}

official_cercles_norm = sorted(list(pop_lookup.keys()), key=len, reverse=True)

# Verified Coordinates for Mali Cercles
CAPITAL_COORDS = {
    'abeibara': (19.0, 2.0), 'ansongo': (15.67, 0.50), 'bamako': (12.65, -8.00),
    'banamba': (13.55, -7.45), 'bandiagara': (14.35, -3.61), 'bankass': (14.08, -3.52),
    'bafoulabe': (13.81, -10.83), 'baraoueli': (13.37, -6.90), 'bla': (13.48, -5.77), 'bougouni': (11.42, -7.48),
    'bourem': (18.97, 0.36), 'diema': (14.53, -9.18), 'dire': (16.27, -3.40),
    'dioila': (12.70, -6.80), 'djenne': (13.91, -4.56), 'douentza': (15.00, -2.95),
    'gao': (16.27, -0.04), 'goundam': (16.41, -3.67), 'gourma-rharous': (16.88, -1.93),
    'kadiolo': (10.57, -5.70), 'kangaba': (11.93, -8.42), 'kati': (12.75, -8.07),
    'kayes': (14.45, -11.44), 'kenieba': (12.83, -11.23), 'kidal': (18.44, 1.41),
    'kita': (13.03, -9.49), 'kolokani': (13.55, -8.03), 'kolondieba': (11.08, -6.88),
    'koro': (14.08, -3.08), 'koulikoro': (12.86, -7.56), 'koutiala': (12.39, -5.47),
    'macina': (14.11, -5.35), 'menaka': (15.92, 2.40), 'mopti': (14.49, -4.19),
    'nara': (15.17, -7.28), 'niafunke': (15.93, -3.98), 'nioro': (15.23, -9.58),
    'niono': (14.25, -5.98), 'san': (13.30, -4.90), 'segou': (13.45, -6.27),
    'sikasso': (11.33, -5.67), 'tenenkou': (14.52, -4.92), 'tessalit': (20.20, 0.98),
    'tin-essako': (19.47, 2.47), 'tombouctou': (16.77, -3.00), 'tominian': (13.28, -4.58),
    'yanfolila': (11.18, -8.15), 'yelimane': (15.13, -10.57), 'yorosso': (12.37, -4.78),
    'youwarou': (15.25, -4.18)
}

def get_cell_val(cell, strings, ns):
    v = cell.find('main:v', ns)
    if v is not None:
        if cell.get('t') == 's': return strings[int(v.text)]
        return v.text
    is_node = cell.find('main:is/main:t', ns)
    if is_node is not None: return is_node.text
    return ""

def classify_coverage(n):
    if n >= 10: return 'Full'
    if n >= 3: return 'Partial'
    if n >= 1: return 'Limited'
    return 'Conflict-only'

# Schools status doesn't depend on the conflict-events year window, so process once.
print("Processing Schools...")
schools_stats = {c: {'total': 0, 'closed': 0} for c in official_cercles_norm}
with zipfile.ZipFile('data/raw/mali_schools_2023.xlsx', 'r') as zip_ref:
    with zip_ref.open('xl/sharedStrings.xml') as f:
        tree = ET.parse(f)
        strings = [el.text if el.text else "" for el in tree.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')]
    with zip_ref.open(sorted([f for f in zip_ref.namelist() if 'worksheets/sheet' in f])[2]) as f:
        tree = ET.parse(f)
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        for row in tree.findall('.//main:row', ns):
            if int(row.get('r')) < 4: continue
            row_vals = [get_cell_val(c, strings, ns) for c in row.findall('main:c', ns)]
            cercle = None
            for v in row_vals:
                nv = normalize(v)
                for c in official_cercles_norm:
                    if c in nv:
                        cercle = c
                        break
                if cercle: break
            if not cercle: continue
            is_closed = any(normalize(v) in ['non', 'ferme', 'fermé'] for v in row_vals)
            schools_stats[cercle]['total'] += 1
            if is_closed: schools_stats[cercle]['closed'] += 1


def aggregate_acled(year_start, year_end):
    stats = {c: {'events': 0, 'fatalities': 0} for c in official_cercles_norm}
    with zipfile.ZipFile('data/raw/acled_mali_summary.xlsx', 'r') as zip_ref:
        with zip_ref.open('xl/worksheets/sheet2.xml') as f:
            tree = ET.parse(f)
            ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            cur_c, cur_y = None, None
            for row in tree.findall('.//main:row', ns):
                if int(row.get('r')) < 2: continue
                row_data = {c.get('r').rstrip('0123456789'): get_cell_val(c, [], ns) for c in row.findall('main:c', ns)}
                if row_data.get('C'):
                    nv = normalize(row_data['C'])
                    for c in official_cercles_norm:
                        if c in nv:
                            cur_c = c
                            break
                if row_data.get('H'): cur_y = row_data['H']
                if cur_c and cur_y and cur_y.isdigit() and year_start <= int(cur_y) <= year_end:
                    try:
                        stats[cur_c]['events'] += int(float(row_data.get('I', 0) or 0))
                        stats[cur_c]['fatalities'] += int(float(row_data.get('J', 0) or 0))
                    except: pass
    return stats


def build_edi(year_start=2020, year_end=2024, suffix=''):
    print(f"Building EDI for {year_start}-{year_end}{' (sensitivity)' if suffix else ''}...")
    conflict_stats = aggregate_acled(year_start, year_end)

    final = []
    for k, p in pop_lookup.items():
        s, c = schools_stats[k], conflict_stats[k]
        p_cl = (s['closed']/s['total']*100) if s['total']>0 else 0
        e_100k = (c['events']/p['pop']*100000) if p['pop']>0 else 0
        f_100k = (c['fatalities']/p['pop']*100000) if p['pop']>0 else 0
        l, ln = CAPITAL_COORDS.get(k, (0,0))
        final.append({
            'cercle': p['display_name'], 'region': p['region'],
            'lat': l, 'lng': ln,
            'total_schools': s['total'], 'closed_schools': s['closed'],
            'pct_closed': round(p_cl, 2),
            'total_conflict_events': c['events'], 'fatalities': c['fatalities'],
            'population': p['pop'],
            'events_per_100k': round(e_100k, 2),
            'fatalities_per_100k': round(f_100k, 2),
            'data_coverage': classify_coverage(s['total'])
        })

    m_pc = max([r['pct_closed'] for r in final]) or 1
    m_ev = max([r['events_per_100k'] for r in final]) or 1
    m_fat = max([r['fatalities_per_100k'] for r in final]) or 1

    # EDI = 50% closure rate + 25% events/100k + 25% fatalities/100k. Each input normalised to dataset max.
    for r in final:
        edi = round(
            (r['pct_closed']/m_pc) * 0.5
            + (r['events_per_100k']/m_ev) * 0.25
            + (r['fatalities_per_100k']/m_fat) * 0.25,
            3
        )
        r['EDI_score'] = edi
        # Data-Limited gate: weak coverage + modest conflict → flagged Data-Limited rather than mixed into tiers.
        # Cercles with weak coverage but severe conflict (events/100k ≥ 100) keep their conflict-driven tier.
        if r['data_coverage'] in ('Limited', 'Conflict-only') and r['events_per_100k'] < 100:
            r['risk_tier'] = 'Data-Limited'
        else:
            r['risk_tier'] = ("High" if edi>=0.4 else "Medium" if edi>=0.2 else "Low")

    final.sort(key=lambda x: x['EDI_score'], reverse=True)

    # Critical tier: top 5 cercles with reliable coverage (Full or Partial). Hard-coded count, not a score threshold.
    reliable = [r for r in final if r['data_coverage'] in ('Full', 'Partial')]
    critical_set = {r['cercle'] for r in reliable[:5]}
    for r in final:
        if r['cercle'] in critical_set:
            r['risk_tier'] = 'Critical'

    os.makedirs('data/clean', exist_ok=True)
    summary_path = f'data/clean/mali_disruption_summary{suffix}.csv'
    map_path = f'data/clean/mali_map_data{suffix}.csv'

    with open(summary_path, 'w', newline='', encoding='utf-8') as f:
        dw = csv.DictWriter(f, fieldnames=[
            'cercle','region','total_schools','closed_schools','pct_closed',
            'total_conflict_events','fatalities','population',
            'events_per_100k','fatalities_per_100k','EDI_score','risk_tier','data_coverage'
        ])
        dw.writeheader()
        for r in final:
            dw.writerow({k:v for k,v in r.items() if k not in ['lat','lng']})

    with open(map_path, 'w', newline='', encoding='utf-8') as f:
        dw = csv.DictWriter(f, fieldnames=[
            'cercle','region','lat','lng','edi','risk','coverage',
            'total_schools','closed_schools','pct_closed',
            'total_conflict_events','events_per_100k',
            'fatalities','fatalities_per_100k','population'
        ])
        dw.writeheader()
        for r in final:
            dw.writerow({
                'cercle':r['cercle'],'region':r['region'],'lat':r['lat'],'lng':r['lng'],
                'edi':r['EDI_score'],'risk':r['risk_tier'],'coverage':r['data_coverage'],
                'total_schools':r['total_schools'],'closed_schools':r['closed_schools'],
                'pct_closed':r['pct_closed'],'total_conflict_events':r['total_conflict_events'],
                'events_per_100k':r['events_per_100k'],
                'fatalities':r['fatalities'],'fatalities_per_100k':r['fatalities_per_100k'],
                'population':r['population']
            })

    return final


if __name__ == '__main__':
    # Default window 2020-2024 (used by dashboard)
    build_edi(2020, 2024, '')
    # Sensitivity check: recent half (2022-2024)
    build_edi(2022, 2024, '_2022_2024')
