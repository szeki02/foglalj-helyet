# -*- coding: utf-8 -*-
# Python 3 - the workshops as a PDF (2026-10-15, user: "Extract the thumbnails from separate workshops with titles
# and create a pdf (in hungarian)").
#
#   python -I scripts/workshop_pdf.py serve     waits on http://localhost:8619 for the website (running in a browser
#                                               on localhost) to post each workshop's picture and words, then builds
#   python -I scripts/workshop_pdf.py build     builds from what is already in docs/workshop_pdf/
#
# The pictures are the gallery's thumbnails, drawn at print size by the page's own stageImage(i, w, h): each workshop
# as at its stop, from its own view. In the browser, with the page in Hungarian:
#
#   const a = window.__au6, out = [];
#   for (const [i, p] of a.phases.entries()) if (p.zone) out.push({ i, no: a.workshopNo(i), title: p.title,
#     when: p.when, areas: [a.zones[p.zone].areas.map(x => x.rect.label)], img: a.stageImage(i, 1600, 1200, 0.9) });
#   for (const o of out) await fetch('http://localhost:8619/', { method: 'POST', body: JSON.stringify(o) });
#   await fetch('http://localhost:8619/done', { method: 'POST', body: '{}' });
#
# The PDF is laid out as HTML (docs/workshop_pdf/workshops.html) and printed by Microsoft Edge headless: one A3
# landscape sheet with all the workshops in a 4 x 2 grid, numbered in the site's one accent colour (user, 2026-10-15:
# "use one accent colour for all workshops, put them on a single A3").
import base64
import html
import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs', 'workshop_pdf')
PDF = os.path.join(ROOT, 'docs', 'Alfoldi6_workshopok_A3.pdf')
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'


class Receiver(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Private-Network', 'true')

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])) or b'{}')
        if self.path.startswith('/done'):
            self.server.done = True
        else:
            name = 'w%d.jpg' % body['no']
            with open(os.path.join(OUT, name), 'wb') as f:
                f.write(base64.b64decode(body.pop('img').split(',', 1)[1]))
            body['file'] = name
            self.server.items.append(body)
            print('got', name, flush=True)
        self.send_response(200)
        self._cors()
        self.end_headers()
        self.wfile.write(b'ok')

    def log_message(self, *a):
        pass


def serve():
    os.makedirs(OUT, exist_ok=True)
    srv = HTTPServer(('127.0.0.1', 8619), Receiver)
    srv.items, srv.done = [], False
    print('waiting on http://localhost:8619')
    while not srv.done:
        srv.handle_request()
    with open(os.path.join(OUT, 'workshops.json'), 'w', encoding='utf-8') as f:
        json.dump(sorted(srv.items, key=lambda o: o['no']), f, ensure_ascii=False, indent=1)


ACCENT = '#2d5a74'                                   # the site's --accent (pavilion steel, blue-grey)
PAGE_CSS = '''
@page { size: A3 landscape; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; background: #f4f3ee; color: #1d211f; font-family: "Atkinson Hyperlegible Next", "Segoe UI", sans-serif; }
.sheet { width: 420mm; height: 297mm; padding: 14mm 16mm 12mm; display: grid; grid-template-rows: auto 1fr auto; gap: 8mm; overflow: hidden; }
.eyebrow { font: 500 8.5pt/1.25 "Atkinson Hyperlegible Mono", Consolas, monospace; color: #5f665f; }
.top { display: grid; grid-template-columns: 1fr auto; align-items: end; gap: 10mm; border-bottom: 0.5mm solid #1d211f; padding-bottom: 5mm; }
h1 { margin: 2mm 0 0; font: 800 34pt/1.05 "Atkinson Hyperlegible Next", "Segoe UI", sans-serif; }
.sub { font-size: 13pt; margin: 0; max-width: 120mm; text-align: right; }
.grid { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 11mm 8mm; align-content: center; }
.card { display: grid; gap: 2.5mm; align-content: start; break-inside: avoid; }
.card header { display: grid; grid-template-columns: auto 1fr; gap: 3mm; align-items: end; }
.num { font: 800 26pt/0.85 "Atkinson Hyperlegible Next", "Segoe UI", sans-serif; color: %s; }
h2 { margin: 0; font: 800 13pt/1.15 "Atkinson Hyperlegible Next", "Segoe UI", sans-serif; }
.card img { width: 100%%; aspect-ratio: 4 / 3; object-fit: cover; display: block; border: 0.3mm solid #c9c8bf; }
.card .eyebrow { font-size: 7.5pt; }
.foot { display: flex; justify-content: space-between; }
''' % ACCENT


def build():
    items = json.load(open(os.path.join(OUT, 'workshops.json'), encoding='utf-8'))
    proj = json.load(open(os.path.join(ROOT, 'web', 'phases.hu.json'), encoding='utf-8'))['project']
    e = html.escape
    def areas(o):                                     # the areas only when they say more than the title
        a = ' + '.join(o['areas'][0])
        return '' if a.lower() == o['title'].lower() else '<div class="eyebrow">%s</div>' % e(a)
    cards = ''.join('''
      <li class="card"><header><div class="num">%d</div><h2>%s</h2></header>
        <img src="%s" alt="">%s</li>''' % (o['no'], e(o['title']), o['file'], areas(o)) for o in items)
    body = '''<section class="sheet">
      <header class="top"><div><div class="eyebrow">Budapest VIII · Alföldi utca 6</div><h1>%s</h1></div>
        <p class="sub">%s</p></header>
      <ol class="grid">%s</ol>
      <footer class="foot eyebrow"><span>%s</span><span>%s</span></footer></section>''' % (
        e(proj['title']), e(proj['subtitle']), cards, e(proj['status']), '%d workshop' % len(items))
    doc = '''<!doctype html><html lang="hu"><head><meta charset="utf-8"><title>%s · workshopok</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible+Next:wght@400;700;800&family=Atkinson+Hyperlegible+Mono:wght@500&display=block">
<style>%s</style></head><body>%s</body></html>''' % (e(proj['title']), PAGE_CSS, body)
    page = os.path.join(OUT, 'workshops.html')
    with open(page, 'w', encoding='utf-8') as f:
        f.write(doc)
    # its own profile, so a running Edge doesn't take the job over (and silently not print)
    profile = os.path.join(os.environ.get('TEMP', OUT), 'au6_edge_pdf')
    before = os.path.getmtime(PDF) if os.path.exists(PDF) else 0
    subprocess.run([EDGE, '--headless', '--disable-gpu', '--no-pdf-header-footer', '--virtual-time-budget=8000',
                    '--user-data-dir=' + profile, '--print-to-pdf=' + PDF, 'file:///' + page.replace('\\', '/')],
                   check=True, timeout=180)
    if not os.path.exists(PDF) or os.path.getmtime(PDF) <= before:
        sys.exit('Edge did not write the PDF')
    print('wrote', PDF, os.path.getsize(PDF), 'bytes')


if __name__ == '__main__':
    if sys.argv[1:] == ['serve']:
        serve()
        build()
    else:
        build()
