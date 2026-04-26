import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('data/raw/acled_mali_summary.xlsx', 'r') as zip_ref:
    with zip_ref.open('xl/worksheets/sheet2.xml') as f:
        tree = ET.parse(f)
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        rows = tree.findall('.//main:row', ns)
        count = 0
        for row in rows[5000:10000]: # Sample the middle
            h_val = ""
            for cell in row.findall('main:c', ns):
                if cell.get('r').startswith('H'):
                    v = cell.find('main:v', ns)
                    if v is not None: h_val = v.text
            if h_val:
                print(f"Row {row.get('r')}: H={h_val}")
                count += 1
                if count > 10: break
