import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('data/raw/acled_mali_summary.xlsx', 'r') as zip_ref:
    with zip_ref.open('xl/worksheets/sheet2.xml') as f:
        tree = ET.parse(f)
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        rows = tree.findall('.//main:row', ns)
        for row in rows[1000:1010]:
            data = {}
            for cell in row.findall('main:c', ns):
                v = cell.find('main:v', ns)
                data[cell.get('r')] = v.text if v is not None else ""
            print(f"Row {row.get('r')}: {data}")
