import importlib
try:
    m = importlib.import_module('fitz')
    print('pymupdf: OK')
except Exception as e:
    print('pymupdf: MISSING', type(e).__name__, e)
