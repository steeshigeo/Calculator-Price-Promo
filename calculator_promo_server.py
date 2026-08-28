#!/usr/bin/env python3
import json, os, re, socket, sys, zipfile
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
XLSX_PATH = os.path.join(BASE_DIR, 'Calculator Promo.xlsx')
HTML_PATH = os.path.join(BASE_DIR, 'index.html')
HOST = '0.0.0.0'
PORT = 8765
CACHE = {'mtime': None, 'data': None}

NS_MAIN = {'a': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
NS_REL = {'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}


def col_letter_to_num(col):
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch.upper()) - 64)
    return n


def excel_date(value):
    return value


def read_xlsx_sheets(path):
    with zipfile.ZipFile(path, 'r') as z:
        names = set(z.namelist())
        shared = []
        if 'xl/sharedStrings.xml' in names:
            root = ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in root.findall('a:si', NS_MAIN):
                txt = ''.join(t.text or '' for t in si.iter('{%s}t' % NS_MAIN['a']))
                shared.append(txt)

        wb_root = ET.fromstring(z.read('xl/workbook.xml'))
        rels_root = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        rel_map = {}
        for rel in rels_root:
            rid = rel.attrib.get('Id')
            target = rel.attrib.get('Target', '')
            if target.startswith('/'):
                target = target[1:]
            elif not target.startswith('xl/'):
                target = 'xl/' + target
            rel_map[rid] = target

        sheets = []
        for s in wb_root.find('a:sheets', NS_MAIN):
            name = s.attrib.get('name')
            rid = s.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            target = rel_map.get(rid)
            if target and target in names:
                sheets.append((name, target))

        out = {}
        for name, target in sheets:
            root = ET.fromstring(z.read(target))
            sheet = []
            max_col = 0
            for row in root.findall('.//a:sheetData/a:row', NS_MAIN):
                row_values = {}
                max_c_row = 0
                for c in row.findall('a:c', NS_MAIN):
                    ref = c.attrib.get('r', '')
                    m = re.match(r'([A-Z]+)(\d+)', ref)
                    if not m:
                        continue
                    cidx = col_letter_to_num(m.group(1))
                    max_c_row = max(max_c_row, cidx)
                    typ = c.attrib.get('t')
                    v = c.find('a:v', NS_MAIN)
                    value = None
                    if typ == 'inlineStr':
                        isel = c.find('a:is', NS_MAIN)
                        if isel is not None:
                            value = ''.join(t.text or '' for t in isel.iter('{%s}t' % NS_MAIN['a']))
                    elif v is not None:
                        raw = v.text or ''
                        if typ == 's':
                            try:
                                value = shared[int(raw)]
                            except Exception:
                                value = raw
                        elif typ == 'b':
                            value = raw == '1'
                        else:
                            try:
                                num = float(raw)
                                value = int(num) if num.is_integer() else num
                            except Exception:
                                value = raw
                    if value not in (None, ''):
                        row_values[cidx] = value
                if row_values:
                    max_col = max(max_col, max_c_row)
                    row_arr = [None] * max_col
                    # Re-expand existing earlier rows as needed below.
                    sheet.append(row_values)
            # normalize rows to max column count
            normalized = []
            for row_map in sheet:
                normalized.append([row_map.get(i) for i in range(1, max_col + 1)])
            out[name] = normalized
        return out


def text(v):
    return '' if v is None else str(v).strip()


def num(v):
    if v in (None, ''):
        return 0
    if isinstance(v, (int, float)):
        return v
    s = re.sub(r'[^0-9.-]', '', str(v))
    try:
        return float(s) if '.' in s else int(s)
    except Exception:
        return 0


def parse_price_list(rows):
    products = []
    current_model = None
    for i, r in enumerate(rows, start=1):
        r = r + [None] * max(0, 8 - len(r))
        a,b,c,d,e,f,g,h = r[:8]
        # section headers are generally a title in column A and no SAP description
        if text(a) and not text(b) and not text(c) and not text(d) and not text(e) and not text(f):
            if i >= 6:
                current_model = text(a)
        if text(a) and text(b) and text(c):
            category = text(c)
            if category.startswith('Apple Device - '):
                products.append({
                    'article': text(a),
                    'description': text(b),
                    'category': category,
                    'group': current_model or text(b),
                    'normal_price': num(e),
                    'promo_price': num(f) if num(f) else num(e),
                    'change': num(g),
                    'remarks': text(h),
                })
    return products


def parse_bnpl(rows):
    out=[]
    for r in rows[1:]:
        r = r + [None]*5
        if text(r[0]):
            tenors=[]
            for v in r[1:4]:
                if v not in (None,''):
                    try: tenors.append(int(float(v)))
                    except: pass
            out.append({'name':text(r[0]),'tenors':tenors,'interest':text(r[4])})
    return out


def parse_catalog(rows):
    out=[]
    for r in rows[1:]:
        r = r + [None]*8
        if text(r[0]):
            out.append({
                'brand':text(r[0]),
                'article':text(r[1]),
                'description':text(r[3]),
                'reference':num(r[5]),
                'current':num(r[6]),
                'repricing':num(r[7]),
            })
    return out


def parse_trade_in(rows):
    # Trade in sheet: BRAND | MODEL NAME | GRADE S | GRADE A | GRADE B | GRADE C | GRADE D
    out=[]
    if not rows: return out
    for r in rows[2:]:
        r = r + [None]*7
        brand, model = text(r[0]), text(r[1])
        if not brand or not model:
            continue
        grades={}
        for key, idx in [('S',2),('A',3),('B',4),('C',5),('D',6)]:
            if r[idx] not in (None,''):
                grades[key]=num(r[idx])
        if grades:
            out.append({'brand':brand,'brand_key':brand.lower(),'model':model,'model_key':model.lower(),'grades':grades})
    return out

def parse_promo_rows(rows):
    notes=[]
    for r in rows:
        r = r + [None]*4
        vals=[text(x) for x in r[:4] if text(x)]
        if vals:
            notes.append({'row': len(notes)+1, 'text': '\n'.join(vals)})
    return notes


def unique_preserve(items):
    seen=set(); out=[]
    for x in items:
        if x not in seen:
            seen.add(x); out.append(x)
    return out


def normalize(data, file_mtime=None):
    products = parse_price_list(data.get('Price List', []))
    bnpl = parse_bnpl(data.get('BNPL', []))
    providers = parse_catalog(data.get('Provider', []))
    qoala = parse_catalog(data.get('Qoala Protection', []))
    promo_notes = parse_promo_rows(data.get('Promo Berjalan', []))
    trade_in = parse_trade_in(data.get('Trade in', []))

    # Split four user-facing product tabs.
    catalog = {'iPhone': [], 'iPad': [], 'Apple Watch': [], 'Mac': []}
    for p in products:
        desc = p['description'].upper()
        if p['category'] == 'Apple Device - iPhone':
            tab = 'iPhone'
        elif p['category'] == 'Apple Device - iPad':
            tab = 'iPad'
        elif 'APPLE WATCH' in desc or p['group'].lower().startswith('apple watch'):
            tab = 'Apple Watch'
        else:
            tab = 'Mac'
        p2 = dict(p)
        # Keep model group from spreadsheet, but clean whitespace.
        p2['group'] = re.sub(r'\s+', ' ', p2['group']).strip()
        catalog[tab].append(p2)

    # Qoala maximum cover is encoded in description as "Max 25.000.000" etc.
    for q in qoala:
        m = re.search(r'Max\s*([0-9.]+)', q['description'], re.I)
        q['max_device'] = int(m.group(1).replace('.','')) if m else 0
        mm = re.search(r'(\d+)\s*bulan', q['description'], re.I)
        q['qoala_tenor'] = int(mm.group(1)) if mm else None
    # More reliable group/tenor extraction from article too
    for q in qoala:
        if not q.get('qoala_tenor'):
            m = re.search(r'\((\d+)-', q['article'])
            q['qoala_tenor'] = int(m.group(1)) if m else None

    # Card installment matrix is shown as an image embedded in Promo Berjalan.
    # Current workbook image1.jpg was transcribed into this structured matrix so
    # the web calculator can present the available 0% tenors.
    # Muamalat is debit-card-only in the image and Mayapada has no available tenor,
    # so neither is offered as a credit-card choice.
    card_matrix = [
        ('BCA', [3,6,12,18,24]),
        ('BRI', [3,6,12,18,24]),
        ('BNI', [3,6,12,18,24]),
        ('CIMB', [3,6,12,24]),
        ('Bank BSI', [3,6,12,24]),
        ('Panin', [3,6,12]),
        ('Mandiri', [3,6,12,18,24]),
        ('Permata', [3,6,12,18,24]),
        ('DBS', [3,6,12,18,24]),
        ('HSBC', [3,6,12,18,24]),
        ('Danamon', [3,6,12,18,24]),
        ('UOB', [3,6,12,18,24]),
        ('Maybank', [3,6,12,24]),
        ('Jenius (BTPN)', [3,6,12]),
        ('KB Bukopin', [3,6,12,18,24]),
        ('OCBC', [3,6,12]),
    ]
    card_options=[{'name':name,'tenors':tenors,'promo_note':'Cicilan 0% berdasarkan tabel kartu kredit pada gambar di sheet Promo Berjalan.'} for name,tenors in card_matrix]

    return {
        'updated_at': datetime.fromtimestamp(file_mtime or os.path.getmtime(XLSX_PATH)).isoformat(timespec='seconds'),
        'source_file': os.path.basename(XLSX_PATH),
        'catalog': catalog,
        'bnpl': bnpl,
        'providers': providers,
        'qoala': qoala,
        'promo_notes': promo_notes,
        'trade_in': trade_in,
        'card_options': card_options,
    }


def load_data():
    try:
        mtime = os.path.getmtime(XLSX_PATH)
    except FileNotFoundError:
        raise RuntimeError(f'File tidak ditemukan: {XLSX_PATH}')
    if CACHE['mtime'] != mtime:
        raw = read_xlsx_sheets(XLSX_PATH)
        CACHE['data'] = normalize(raw, mtime)
        CACHE['mtime'] = mtime
    return CACHE['data']


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, content, content_type='text/html; charset=utf-8'):
        if isinstance(content, str): content = content.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store, max-age=0')
        self.end_headers(); self.wfile.write(content)

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == '/':
                with open(HTML_PATH, 'rb') as f: content=f.read()
                return self._send(200, content, 'text/html; charset=utf-8')
            if path == '/api/data':
                return self._send(200, json.dumps(load_data(), ensure_ascii=False), 'application/json; charset=utf-8')
            if path == '/api/health':
                return self._send(200, json.dumps({'ok':True,'file':os.path.basename(XLSX_PATH)}, ensure_ascii=False), 'application/json; charset=utf-8')
            return self._send(404, 'Not Found', 'text/plain; charset=utf-8')
        except Exception as e:
            return self._send(500, json.dumps({'ok':False,'error':str(e)}, ensure_ascii=False), 'application/json; charset=utf-8')

    def log_message(self, fmt, *args):
        sys.stdout.write('[%s] %s\n' % (datetime.now().strftime('%H:%M:%S'), fmt % args))


def lan_ip():
    try:
        s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); ip=s.getsockname()[0]; s.close(); return ip
    except Exception:
        try: return socket.gethostbyname(socket.gethostname())
        except: return '127.0.0.1'


def main():
    # Validate the workbook before opening server.
    d = load_data()
    print(f"Loaded {sum(len(v) for v in d['catalog'].values())} Apple device price rows")
    server=ThreadingHTTPServer((HOST,PORT), Handler)
    print('\nKALKULATOR PROMO siap.')
    print(f'Komputer ini : http://127.0.0.1:{PORT}')
    print(f'HP via Wi-Fi : http://{lan_ip()}:{PORT}')
    print('Edit & simpan "Calculator Promo.xlsx" untuk memperbarui master data.')
    print('Tekan Ctrl+C untuk berhenti.\n')
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__=='__main__': main()
