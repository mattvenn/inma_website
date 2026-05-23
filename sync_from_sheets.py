#!/usr/bin/env python3
"""
sync_from_sheets.py — fetch content from Google Sheets and write JSON files.

Google Sheet must have four tabs named exactly:
  Content      — columns: key | en | es
  Services     — columns: key | label_en | label_es | title_en | title_es |
                           short_en | short_es | detail_en | detail_es
  Testimonials — columns: name | quote_en | quote_es
  Events       — columns: date | title_en | title_es | description_en |
                           description_es | location | link | link_text_en | link_text_es

Configuration: create sheets_config.json (see sheets_config.json.example).

Usage:
  python3 sync_from_sheets.py

Cron (hourly):
  0 * * * * cd /path/to/site && python3 sync_from_sheets.py >> /var/log/sheets_sync.log 2>&1
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE  = os.path.join(SCRIPT_DIR, 'sheets_config.json')
DATA_DIR     = os.path.join(SCRIPT_DIR, 'data')
EVENTS_FILE  = os.path.join(SCRIPT_DIR, 'events', 'events.json')


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f'ERROR: {CONFIG_FILE} not found. Copy sheets_config.json.example and fill it in.')
        sys.exit(1)
    with open(CONFIG_FILE) as f:
        cfg = json.load(f)
    sheet_id = cfg.get('sheet_id') or os.environ.get('SHEETS_ID')
    api_key  = cfg.get('api_key')  or os.environ.get('SHEETS_API_KEY')
    if not sheet_id or not api_key:
        print('ERROR: sheet_id and api_key must be set in sheets_config.json or environment.')
        sys.exit(1)
    return sheet_id, api_key


# ---------------------------------------------------------------------------
# Google Sheets API
# ---------------------------------------------------------------------------

def fetch_tab(sheet_id, api_key, tab_name):
    """Return list-of-rows for one sheet tab (first row = headers)."""
    range_enc = urllib.parse.quote(f'{tab_name}!A:Z') if hasattr(urllib, 'parse') else tab_name + '!A:Z'
    url = (
        f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}'
        f'/values/{urllib.request.quote(tab_name + "!A:Z")}'
        f'?key={api_key}'
    )
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f'ERROR fetching tab "{tab_name}": HTTP {e.code} — {e.read().decode()}')
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f'ERROR fetching tab "{tab_name}": {e.reason}')
        sys.exit(1)
    return data.get('values', [])


def rows_to_dicts(rows):
    """Convert [[header...], [row...], ...] to [{'header': value, ...}, ...]."""
    if not rows:
        return []
    headers = [h.strip() for h in rows[0]]
    result = []
    for row in rows[1:]:
        if not any(cell.strip() for cell in row):
            continue  # skip blank rows
        d = {}
        for i, header in enumerate(headers):
            d[header] = row[i].strip() if i < len(row) else ''
        result.append(d)
    return result


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def text_to_html(text):
    """Convert plain text with newlines and **bold** markers to HTML paragraphs."""
    if not text:
        return ''
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    html_lines = []
    for line in lines:
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        html_lines.append(f'<p>{line}</p>')
    return '\n'.join(html_lines)


def bilingual(row, en_key, es_key, html=False):
    en = row.get(en_key, '')
    es = row.get(es_key, '')
    if html:
        en = text_to_html(en)
        es = text_to_html(es)
    return {'en': en or None, 'es': es or None}


# ---------------------------------------------------------------------------
# Tab processors
# ---------------------------------------------------------------------------

def process_content(rows):
    dicts = rows_to_dicts(rows)
    result = {}
    for row in dicts:
        key = row.get('key', '').strip()
        if not key:
            continue
        en = row.get('en', '')
        es = row.get('es', '')
        # Multi-paragraph fields get HTML wrapping; single-line fields stay as plain text
        html_keys = {'about_bio'}
        if key in html_keys:
            result[key] = {'en': text_to_html(en), 'es': text_to_html(es)}
        else:
            result[key] = {'en': en or None, 'es': es or None}
    return result


def process_services(rows):
    dicts = rows_to_dicts(rows)
    result = []
    for row in dicts:
        key = row.get('key', '').strip()
        if not key:
            continue
        result.append({
            'key':    key,
            'label':  bilingual(row, 'label_en', 'label_es'),
            'title':  bilingual(row, 'title_en', 'title_es'),
            'short':  bilingual(row, 'short_en', 'short_es'),
            'detail': bilingual(row, 'detail_en', 'detail_es', html=True),
        })
    return result


def process_testimonials(rows):
    dicts = rows_to_dicts(rows)
    result = []
    for row in dicts:
        name = row.get('name', '').strip()
        if not name:
            continue
        result.append({
            'name':  name,
            'quote': bilingual(row, 'quote_en', 'quote_es'),
        })
    return result


def process_events(rows):
    dicts = rows_to_dicts(rows)
    result = []
    for row in dicts:
        date = row.get('date', '').strip()
        if not date:
            continue
        result.append({
            'date':        date,
            'title':       bilingual(row, 'title_en', 'title_es'),
            'description': bilingual(row, 'description_en', 'description_es'),
            'location':    row.get('location', '') or None,
            'link':        row.get('link', '') or None,
            'link_text':   bilingual(row, 'link_text_en', 'link_text_es'),
        })
    return result


# ---------------------------------------------------------------------------
# File writing
# ---------------------------------------------------------------------------

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'  wrote {os.path.relpath(path, SCRIPT_DIR)}')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# urllib.request.quote lives here in Python 3
import urllib.parse
urllib.request.quote = urllib.parse.quote


def main():
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] syncing from Google Sheets...')

    sheet_id, api_key = load_config()

    tabs = {
        'Content':      process_content,
        'Services':     process_services,
        'Testimonials': process_testimonials,
        'Events':       process_events,
    }

    outputs = {}
    for tab_name, processor in tabs.items():
        rows = fetch_tab(sheet_id, api_key, tab_name)
        outputs[tab_name] = processor(rows)

    write_json(os.path.join(DATA_DIR, 'content.json'),      outputs['Content'])
    write_json(os.path.join(DATA_DIR, 'services.json'),     outputs['Services'])
    write_json(os.path.join(DATA_DIR, 'testimonials.json'), outputs['Testimonials'])
    write_json(EVENTS_FILE,                                  outputs['Events'])

    print('done.')


if __name__ == '__main__':
    main()
