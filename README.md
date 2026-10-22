# Meme Radar v0.1

Ein ausführbarer Prototyp für die Früherkennung neuer DEX-Pools auf **Solana, Base und Ethereum**. Web-Dashboard (Streamlit), regelbasierter Early-Discovery-Score und Telegram-Benachrichtigungen.

## Start

Python 3.10+ vorausgesetzt.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
streamlit run app.py
```

Dashboard im Browser unter der von Streamlit angezeigten lokalen Adresse (typisch http://localhost:8501).

## Telegram konfigurieren

1. Telegram: **@BotFather** öffnen, `/newbot` ausführen und Bot-Token kopieren.
2. Dem neuen Bot eine Nachricht senden (z. B. `/start`).
3. `https://api.telegram.org/bot<TOKEN>/getUpdates` im Browser aufrufen. In der Antwort `message.chat.id` finden. Bei Gruppen den Bot der Gruppe hinzufügen und dort eine Nachricht senden.
4. `.env` mit `TELEGRAM_BOT_TOKEN` und `TELEGRAM_CHAT_ID` befüllen.
5. Separates Terminal öffnen und den Bot-Worker starten:

```bash
python bot.py
```

Der Worker läuft nur, solange der Prozess aktiv ist. Ein Server oder Prozessmanager ist für 24/7-Betrieb erforderlich.

## Funktionsweise

Die öffentliche GeckoTerminal-API (`/api/v2/networks/{network}/new_pools`) liefert neu gelistete Pools. Die App ruft bis zu zwei Seiten je Netzwerk ab. Der Score bewertet Pool-Alter (25 Punkte), Liquidität (20), Stundenvolumen (20), Stunden-Tradeanzahl (15) und Kauf/Verkauf-Verhältnis (20). Bei einem Score >= `ALERT_MIN_SCORE` und Liquidität >= $3.000 sendet der Worker eine Nachricht. SQLite verhindert wiederholte Meldungen pro Pool-ID.

**Wichtige Einschränkungen:** Keine echte ML-Vorhersage; kein Token-Audit; keine Honeypot-, Holder-, Mint-Authority- oder LP-Lock-Prüfung. Neue Pools sind nicht zwangsläufig Meme-Coins. Die API kann Rate-Limits haben, Daten können verzögert oder manipuliert sein. Die Erkennung ist nicht garantiert vollständig oder schneller als andere Dienste. Es werden keine Trades ausgeführt.

## Sicherheit

Token niemals committen oder öffentlich teilen. `.env` privat halten. Bot nur mit den nötigen Rechten betreiben. Keine Kaufempfehlung.
