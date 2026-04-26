def normalize(s):
    if s is None:
        return ''
    s = str(s).strip().lower()
    replacements = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a',
        'ô': 'o', 'ö': 'o',
        'î': 'i', 'ï': 'i',
        'û': 'u', 'ü': 'u', 'ù': 'u',
        'ç': 'c'
    }
    for accented, plain in replacements.items():
        s = s.replace(accented, plain)
    return s
