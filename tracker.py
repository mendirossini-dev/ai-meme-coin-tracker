import os
import time
import sqlite3
import requests
from datetime import datetime, timezone
from pathlib import Path

BASE = 'https://api.geckoterminal.com/api/v2'
CHAINS = {'Solana':'solana', 'Base':'base', 'Ethereum':'eth'}
DB = Path(os.getenv('TRACKER_DB', 'tracker.db'))


def fetch_new_pools(chain, pages=2):
    output = []
    session = requests.Session()
    session.headers.update({'accept':'application/json', 'User-Agent':'MemeTracker/0.1'})
    for page in range(1, pages+1):
        url = f'{BASE}/networks/{chain}/new_pools'
        for attempt in range(3):
            try:
                r = session.get(url, params={'page':page}, timeout=20)
                if r.status_code == 429:
                    time.sleep(2**attempt * 3)
                    continue
                r.raise_for_status()
                output.extend(r.json().get('data', []))
                break
            except requests.RequestException:
                if attempt == 2: raise
                time.sleep(2**attempt)
    return output


def num(x):
    try: return float(x or 0)
    except (ValueError, TypeError): return 0.0


def score_pool(pool, chain):
    a = pool.get('attributes') or {}
    tx = (a.get('transactions') or {}).get('h1') or {}
    buys, sells = int(num(tx.get('buys'))), int(num(tx.get('sells')))
    liquidity = num(a.get('reserve_in_usd'))
    volume = num((a.get('volume_usd') or {}).get('h1'))
    created = a.get('pool_created_at')
    try:
        dt = datetime.fromisoformat(created.replace('Z','+00:00'))
        age_h = max(0, (datetime.now(timezone.utc)-dt).total_seconds()/3600)
    except (TypeError, ValueError, AttributeError):
        age_h = 99999
    score = 0
    score += 25 if age_h <= 1 else 20 if age_h <= 6 else 12 if age_h <= 24 else 0
    score += 20 if liquidity >= 25000 else 12 if liquidity >= 10000 else 5 if liquidity >= 3000 else 0
    score += 20 if volume >= 50000 else 14 if volume >= 10000 else 7 if volume >= 2000 else 0
    trades = buys+sells
    score += 15 if trades >= 100 else 10 if trades >= 30 else 5 if trades >= 10 else 0
    ratio = buys / trades if trades else 0
    score += 20 if trades >= 10 and .55 <= ratio <= .85 else 10 if trades >= 10 and ratio > .5 else 0
    flags = []
    if liquidity < 3000: flags.append('Sehr geringe Liquidität')
    if trades < 10: flags.append('Wenige Trades')
    if trades >= 10 and ratio > .9: flags.append('Extrem einseitiger Kaufdruck')
    if age_h > 24: flags.append('Älter als 24 Stunden')
    if liquidity and volume > liquidity*20: flags.append('Sehr hohes Volumen relativ zur Liquidität')
    pid = pool.get('id','')
    address = a.get('address') or pid.split('_',1)[-1]
    return {'id':pid, 'chain':chain, 'name':a.get('name') or 'Unbekannt',
            'address':address, 'score':score, 'age_h':round(age_h,2),
            'liquidity':liquidity, 'volume_h1':volume, 'buys_h1':buys,
            'sells_h1':sells, 'risk':'; '.join(flags) or 'Keine Basiswarnung',
            'url':f'https://www.geckoterminal.com/{chain}/pools/{address}'}


def scan(pages=2):
    rows, errors = [], []
    for label, chain in CHAINS.items():
        try:
            rows.extend(score_pool(p, chain) for p in fetch_new_pools(chain, pages))
        except (requests.RequestException, ValueError) as e:
            errors.append(f'{label}: {e}')
    return sorted(rows, key=lambda x:x['score'], reverse=True), errors


def db_connection():
    conn = sqlite3.connect(DB)
    conn.execute('CREATE TABLE IF NOT EXISTS alerted (pool_id TEXT PRIMARY KEY, alerted_at TEXT NOT NULL)')
    return conn


def send_telegram(text):
    token, chat = os.getenv('TELEGRAM_BOT_TOKEN'), os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat: raise RuntimeError('TELEGRAM_BOT_TOKEN und TELEGRAM_CHAT_ID fehlen')
    r = requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
                      json={'chat_id':chat,'text':text,'disable_web_page_preview':True}, timeout=20)
    r.raise_for_status()
    result = r.json()
    if not result.get('ok'): raise RuntimeError(str(result))


def notify_new(rows, threshold=75):
    sent = 0
    with db_connection() as conn:
        for p in rows:
            if p['score'] < threshold or p['liquidity'] < 3000: continue
            if conn.execute('SELECT 1 FROM alerted WHERE pool_id=?', (p['id'],)).fetchone(): continue
            msg = (f"🚨 Neuer Pool: {p['name']}\nChain: {p['chain']} | Score: {p['score']}/100\n"
                   f"Alter: {p['age_h']}h | Liquidität: ${p['liquidity']:,.0f}\n"
                   f"Volumen 1h: ${p['volume_h1']:,.0f} | Käufe/Verkäufe: {p['buys_h1']}/{p['sells_h1']}\n"
                   f"Risiken: {p['risk']}\n{p['url']}\nKeine Kaufempfehlung.")
            send_telegram(msg)
            conn.execute('INSERT INTO alerted VALUES (?,?)', (p['id'], datetime.now(timezone.utc).isoformat()))
            conn.commit()
            sent += 1
    return sent
