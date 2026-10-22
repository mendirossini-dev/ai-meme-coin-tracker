import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from tracker import scan, notify_new

load_dotenv()
st.set_page_config(page_title='Meme Radar', page_icon='📡', layout='wide')
st.title('📡 Meme Radar — Early Discovery')
st.caption('Solana · Base · Ethereum | Neue DEX-Pools, kein vollständiger Markt- oder Sicherheitscheck')
with st.sidebar:
    st.header('Filter')
    chains = st.multiselect('Blockchains', ['Solana','Base','Ethereum'], default=['Solana','Base','Ethereum'])
    min_score = st.slider('Mindest-Score', 0, 100, 50)
    min_liq = st.number_input('Min. Liquidität (USD)', min_value=0, value=3000, step=1000)
    pages = st.slider('API-Seiten je Chain', 1, 3, 2)
    refresh = st.button('🔄 Jetzt aktualisieren')
    st.caption('Für regelmäßige Aktualisierung Seite neu laden oder den Bot-Worker starten.')

@st.cache_data(ttl=75, show_spinner='Scanne neue Pools …')
def cached_scan(pages): return scan(pages)
if refresh: cached_scan.clear()
rows, errors = cached_scan(pages)
for e in errors: st.warning('API-Fehler: '+e)
filtered = [r for r in rows if r['chain'].capitalize() in chains and r['score'] >= min_score and r['liquidity'] >= min_liq]
a,b,c = st.columns(3)
a.metric('Pools gefunden',len(rows))
b.metric('Gefilterte Kandidaten',len(filtered))
c.metric('Score ≥ 75',sum(r['score'] >= 75 for r in filtered))
if filtered:
    df = pd.DataFrame(filtered)
    st.dataframe(df[['chain','name','score','age_h','liquidity','volume_h1','buys_h1','sells_h1','risk','url']],
        column_config={'url':st.column_config.LinkColumn('Chart'),'score':st.column_config.ProgressColumn('Score',min_value=0,max_value=100),
                       'liquidity':st.column_config.NumberColumn('Liquidität $',format='$%.0f'),
                       'volume_h1':st.column_config.NumberColumn('Volumen 1h $',format='$%.0f')},
        hide_index=True, use_container_width=True)
else: st.info('Keine Pools für diese Filter. Filter lockern oder später erneut scannen.')
st.divider()
st.subheader('Telegram-Test')
if st.button('Neue Treffer jetzt an Telegram senden'):
    try:
        n = notify_new(rows, int(os.getenv('ALERT_MIN_SCORE','75')))
        st.success(f'{n} neue Meldungen gesendet (bereits gemeldete Pools werden übersprungen).')
    except Exception as e: st.error(str(e))
st.info('Der Score ist eine Heuristik, keine trainierte KI oder Gewinnprognose. Contract-, Holder-, Honeypot- und LP-Lock-Prüfungen sind noch NICHT integriert.')
