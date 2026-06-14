#!/usr/bin/env python3
"""
sync_from_sheets.py — fetch content from Google Sheets, write JSON files,
                       and render index.html from index.template.html.

Google Sheet must have four tabs named exactly:
  Content      — columns: key | en | es
  Services     — columns: key | label_en | label_es | title_en | title_es |
                           short_en | short_es | detail_en | detail_es
  Testimonials — columns: name | quote_en | quote_es
  Events       — columns: date | title_en | title_es | description_en |
                           description_es | location | link | link_text_en | link_text_es

Configuration: create sheets_config.json (see sheets_config.json.example).

Usage:
  python3 sync_from_sheets.py              # fetch from Sheets, write JSON + HTML
  python3 sync_from_sheets.py --render-only  # re-render HTML from existing JSON files

Cron (hourly):
  0 * * * * cd /path/to/site && python3 sync_from_sheets.py >> /var/log/sheets_sync.log 2>&1
"""

import html as _html
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, date as _date

SCRIPT_DIR     = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE    = os.environ.get('SHEETS_CONFIG', os.path.join(SCRIPT_DIR, 'sheets_config.json'))
DATA_DIR       = os.path.join(SCRIPT_DIR, 'data')
EVENTS_FILE    = os.path.join(SCRIPT_DIR, 'events', 'events.json')
TEMPLATE_FILE  = os.path.join(SCRIPT_DIR, 'index.template.html')
INDEX_FILE     = os.path.join(SCRIPT_DIR, 'index.html')


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

YOUTUBE_RE = re.compile(
    r'^(?:https?://)?(?:www\.)?'
    r'(?:youtube(?:-nocookie)?\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)'
    r'([A-Za-z0-9_-]{11})(?:[?&]\S*)?$'
)


def youtube_embed_html(video_id, size='default'):
    """Return a responsive YouTube embed. size='small' renders a narrower player
    (e.g. for testimonial cards) instead of the full-width default."""
    size_class = ' youtube-embed--small' if size == 'small' else ''
    return (
        f'<div class="youtube-embed{size_class}">'
        f'<iframe src="https://www.youtube-nocookie.com/embed/{video_id}" '
        f'title="YouTube video player" loading="lazy" '
        f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
        f'referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
        f'</div>'
    )


def text_to_html(text, embed_size='default'):
    """Convert plain text with newlines and **bold** markers to HTML paragraphs.
    A line containing only a YouTube URL is rendered as an embedded video instead."""
    if not text:
        return ''
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    html_lines = []
    for line in lines:
        m = YOUTUBE_RE.match(line)
        if m:
            html_lines.append(youtube_embed_html(m.group(1), embed_size))
            continue
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        html_lines.append(f'<p>{line}</p>')
    return '\n'.join(html_lines)


def bilingual(row, en_key, es_key, html=False, embed_size='default'):
    en = row.get(en_key, '')
    es = row.get(es_key, '')
    if html:
        en = text_to_html(en, embed_size)
        es = text_to_html(es, embed_size)
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
        quote = bilingual(row, 'quote_en', 'quote_es')
        video = {}
        for lang in ('en', 'es'):
            m = YOUTUBE_RE.match((quote.get(lang) or '').strip())
            if m:
                video[lang] = m.group(1)
                quote[lang] = None
        result.append({
            'name':  name,
            'quote': quote,
            'video': video,
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
# HTML rendering
# ---------------------------------------------------------------------------

def _esc(text):
    return _html.escape(str(text or ''), quote=True)

def _val(bilingual_dict, lang):
    d = bilingual_dict or {}
    return d.get(lang) or d.get('en' if lang == 'es' else 'es') or ''

def _build_testimonials_html(testimonials, lang):
    items = [
        t for t in testimonials
        if (t.get('quote') or {}).get(lang) or (t.get('video') or {}).get(lang)
    ]
    if not items:
        return ''
    cards = []
    for i, t in enumerate([*items, *items]):
        hidden = ' aria-hidden="true"' if i >= len(items) else ''
        name = _esc(t['name'])
        video_id = (t.get('video') or {}).get(lang)
        if video_id:
            body = youtube_embed_html(video_id, 'small')
        else:
            quote = _esc(t['quote'][lang])
            body = (
                '<span class="testimonial-quote-mark" aria-hidden="true">“</span>\n'
                f'        <p class="testimonial-text">{quote}</p>'
            )
        cards.append(
            f'      <article class="testimonial-card"{hidden}>\n'
            f'        {body}\n'
            f'        <p class="testimonial-name">{name}</p>\n'
            f'      </article>'
        )
    return '\n'.join(cards)

def _build_events_html(events):
    cards = []
    for event in events:
        d     = datetime.strptime(event['date'], '%Y-%m-%d')
        day   = d.day
        month = d.strftime('%b').upper()

        title     = event.get('title') or {}
        desc      = event.get('description') or {}
        link_text = event.get('link_text') or {}

        title_en = _esc(_val(title, 'en'))
        title_es = _esc(_val(title, 'es') or _val(title, 'en'))
        desc_en  = _esc(_val(desc, 'en'))
        desc_es  = _esc(_val(desc, 'es') or _val(desc, 'en'))
        lt_en    = _esc(_val(link_text, 'en') or 'Find out more →')
        lt_es    = _esc(_val(link_text, 'es') or 'Más información →')

        location_html = ''
        if event.get('location'):
            loc = _esc(event['location'])
            location_html = (
                '<p class="event-location">'
                '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">'
                '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>'
                '<circle cx="12" cy="10" r="3"/></svg>'
                f'{loc}</p>'
            )

        link_html = ''
        if event.get('link'):
            href = _esc(event['link'])
            link_html = (
                f'<a href="{href}" target="_blank" rel="noopener noreferrer" class="event-link">'
                f'<span class="lang-en">{lt_en}</span>'
                f'<span class="lang-es">{lt_es}</span>'
                f'</a>'
            )

        desc_html = ''
        if desc_en or desc_es:
            desc_html = f'<p class="lang-en">{desc_en}</p><p class="lang-es">{desc_es}</p>'

        cards.append(
            f'      <article class="event-card">\n'
            f'        <div class="event-date-badge" aria-label="{event["date"]}">\n'
            f'          <span class="event-date-day">{day}</span>\n'
            f'          <span class="event-date-month">{month}</span>\n'
            f'        </div>\n'
            f'        <div class="event-body">\n'
            f'          <h3><span data-en="{title_en}" data-es="{title_es}">{title_en}</span></h3>\n'
            f'          {desc_html}\n'
            f'          {location_html}\n'
            f'          {link_html}\n'
            f'        </div>\n'
            f'      </article>'
        )
    return '\n'.join(cards)

def _filter_upcoming(events):
    today = _date.today()
    upcoming = []
    for e in events:
        if not e.get('date'):
            continue
        try:
            if datetime.strptime(e['date'], '%Y-%m-%d').date() >= today:
                upcoming.append(e)
        except ValueError:
            pass
    return sorted(upcoming, key=lambda e: e['date'])

def _build_tokens(content, services, testimonials, events):
    tokens = {}
    html_content_keys = {'about_bio'}

    for key, val in content.items():
        en = (val or {}).get('en') or ''
        es = (val or {}).get('es') or en
        if key in html_content_keys:
            tokens[f'{key}_en'] = en
            tokens[f'{key}_es'] = es
        else:
            tokens[f'{key}_en'] = _esc(en)
            tokens[f'{key}_es'] = _esc(es)

    hero_title = content.get('hero_title') or {}
    hero_title_en = hero_title.get('en') or ''
    hero_title_es = hero_title.get('es') or hero_title_en
    for suffix, text in (('en', hero_title_en), ('es', hero_title_es)):
        words = text.split()
        move  = words[0]      if words else ''
        being = words[-1]     if len(words) > 1 else ''
        mid   = ' '.join(words[1:-1]) if len(words) > 2 else ''
        tokens[f'hero_title_move_{suffix}']  = _esc(move)
        tokens[f'hero_title_mid_{suffix}']   = _esc(mid)
        tokens[f'hero_title_being_{suffix}'] = _esc(being)

    html_service_fields = {'detail'}
    for svc in services:
        k = svc['key']
        for field in ('label', 'title', 'short'):
            tokens[f'{k}_{field}_en'] = _esc(_val(svc.get(field), 'en'))
            tokens[f'{k}_{field}_es'] = _esc(_val(svc.get(field), 'es'))
        for field in html_service_fields:
            tokens[f'{k}_{field}_en'] = _val(svc.get(field), 'en')
            tokens[f'{k}_{field}_es'] = _val(svc.get(field), 'es')

    tokens['testimonials_en_html'] = _build_testimonials_html(testimonials, 'en')
    tokens['testimonials_es_html'] = _build_testimonials_html(testimonials, 'es')

    upcoming = _filter_upcoming(events)
    if upcoming:
        tokens['events_section_style'] = ''
        tokens['events_list_html']     = _build_events_html(upcoming)
    else:
        tokens['events_section_style'] = 'style="display:none"'
        tokens['events_list_html']     = ''

    return tokens

def render_html(content, services, testimonials, events):
    if not os.path.exists(TEMPLATE_FILE):
        print(f'  WARN: {TEMPLATE_FILE} not found — skipping HTML render')
        return
    with open(TEMPLATE_FILE, encoding='utf-8') as f:
        html = f.read()
    tokens = _build_tokens(content, services, testimonials, events)
    for key, val in tokens.items():
        html = html.replace('{{' + key + '}}', val)
    # Clear any tokens that had no data (missing keys in JSON)
    html = re.sub(r'\{\{[^}]+\}\}', '', html)
    tmp = INDEX_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(html)
    os.replace(tmp, INDEX_FILE)
    print(f'  wrote {os.path.relpath(INDEX_FILE, SCRIPT_DIR)}')


# ---------------------------------------------------------------------------
# File writing
# ---------------------------------------------------------------------------

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)  # atomic on POSIX — readers never see a partial file
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

    render_html(outputs['Content'], outputs['Services'], outputs['Testimonials'], outputs['Events'])

    print('done.')


def _load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


if __name__ == '__main__':
    if '--render-only' in sys.argv:
        print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] rendering HTML from existing JSON...')
        render_html(
            _load_json(os.path.join(DATA_DIR, 'content.json')),
            _load_json(os.path.join(DATA_DIR, 'services.json')),
            _load_json(os.path.join(DATA_DIR, 'testimonials.json')),
            _load_json(EVENTS_FILE),
        )
        print('done.')
    else:
        main()
