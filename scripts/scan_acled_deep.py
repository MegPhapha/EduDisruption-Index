import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('data/raw/acled_mali_summary.xlsx', 'r') as zip_ref:
    with zip_ref.open('xl/worksheets/sheet2.xml') as f:
        tree = ET.parse(f)
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        count = 0
        for row in tree.findall('.//main:row', ns):
            row_data = {}
            for cell in row.findall('main:c', ns):
                col = ''.join(filter(str.isalpha, cell.get('r')))
                v = cell.find('main:v', ns)
                val = v.text if v is not None else ""
                row_data[col] = val
            if row_data.get('H') == '2024':
                print(f"Row {row.get('r')}: {row_data}")
                count += 1
                if count > 3: break
