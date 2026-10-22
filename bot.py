import os
import time
import logging
from dotenv import load_dotenv
from tracker import scan, notify_new

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
interval = max(60, int(os.getenv('POLL_SECONDS','90')))
threshold = int(os.getenv('ALERT_MIN_SCORE','75'))
logging.info('Telegram Worker startet: %ss Intervall, Score >= %s',interval,threshold)
while True:
    try:
        rows, errors = scan(pages=2)
        for e in errors: logging.warning(e)
        n = notify_new(rows, threshold)
        logging.info('%d Pools geprüft; %d Meldungen versendet',len(rows),n)
    except Exception: logging.exception('Scan/Telegram fehlgeschlagen')
    time.sleep(interval)
