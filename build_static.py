#!/usr/bin/env python3
"""Build a Netlify-ready static package from Calculator Promo.xlsx.

The workbook remains the master source. Running this script regenerates data.json
and copies index.html + required files into public/.
"""
import os, shutil, json
from calculator_promo_server import load_data

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')
os.makedirs(PUBLIC_DIR, exist_ok=True)

data = load_data()
with open(os.path.join(PUBLIC_DIR, 'data.json'), 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
shutil.copy2(os.path.join(BASE_DIR, 'index.html'), os.path.join(PUBLIC_DIR, 'index.html'))
for name in ['README-NETLIFY.txt']:
    src = os.path.join(BASE_DIR, name)
    if os.path.exists(src): shutil.copy2(src, os.path.join(PUBLIC_DIR, name))
print('Static build ready:', PUBLIC_DIR)
print('Products:', sum(len(v) for v in data['catalog'].values()))
print('Card options:', len(data['card_options']))
