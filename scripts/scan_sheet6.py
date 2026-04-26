import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('data/raw/acled_mali_summary.xlsx', 'r') as zip_ref:
    with zip_ref.open('xl/worksheets/sheet6.xml') as f:
        tree = ET.parse(f)
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        for row in tree.findall('.//main:row', ns)[:20]:
            row_data = {}
            for cell in row.findall('main:c', ns):
                col = ''.join(filter(str.isalpha, cell.get('r')))
                v = cell.find('main:v', ns)
                is_node = cell.find('main:is/main:t', ns)
                val = v.text if v is not None else ""
                if is_node is not None: val = is_node.text
                row_data[col] = val
            print(f"Row {row.get('r')}: {row_data}")
