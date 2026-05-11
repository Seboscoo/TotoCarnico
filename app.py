import streamlit as st
import requests
import pandas as pd
from io import StringIO
import random
import os
from datetime import datetime
from zoneinfo import ZoneInfo
# Definiamo il percorso del logo (quello che hai messo nella cartella)
FILE_LOGO = "logo.webp"

# Creiamo tre colonne. Quella centrale ospiterà il logo, 
# quelle laterali (vuote) servono per centrarlo.
col1, col2, col3 = st.columns([1, 2, 1]) 

# Se il file del logo esiste, lo mostriamo nella colonna centrale
if os.path.exists(FILE_LOGO):
    with col2:
        # width=400 è un buon compromesso per pc e mobile, aggiustalo se serve
        st.image(FILE_LOGO, width=400) 
else:
    # Se per qualche motivo il logo manca, mostriamo un avviso
    # (solo sul tuo pc, i tuoi amici vedranno il logo online)
    st.info("⚠️ Logo 'logo.png' non trovato nella cartella. Ma online funzionerà se l'hai caricato su GitHub.")
st.title("Totocalcio Carnico ")
st.write("Inserisci i tuoi pronostici.")

# --- 1. FUNZIONE DI ESTRAZIONE DAL SITO ---
@st.cache_data 
def estrai_partite(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        risposta = requests.get(url, headers=headers)
        tabelle = pd.read_html(StringIO(risposta.text))
        
        tabella_giusta = None
        nome_colonna_partita = None
        
        for tab in tabelle:
            for colonna in tab.columns:
                if 'partita' in str(colonna).lower():
                    tabella_giusta = tab
                    nome_colonna_partita = colonna
                    break
            if tabella_giusta is not None:
                break
                
        if tabella_giusta is not None:
            partite_grezze = tabella_giusta[nome_colonna_partita].dropna().tolist()
            partite_pulite = [str(p).split('(')[0].strip() for p in partite_grezze]
            return partite_pulite
        else:
            return []
    except Exception as e:
        st.error(f"Errore nello scaricare {url}: {e}")
        return []

# --- 2. GESTIONE DELLA SCHEDINA SETTIMANALE ---
FILE_SCHEDINA = "schedina_settimana.csv"

URL_PRIMA = "https://www.carnico.it/calendario/prima-categoria/?giornata=seconda-giornata-prima-categoria"
URL_SECONDA = "https://www.carnico.it/calendario/seconda-categoria/?giornata=seconda-giornata-seconda-categoria"
URL_TERZA = "https://www.carnico.it/calendario/terza-categoria/?giornata=seconda-giornata-terza-categoria"

if not os.path.exists(FILE_SCHEDINA):
    st.info("Sto generando la nuova schedina della settimana...")
    
    partite_prima = estrai_partite(URL_PRIMA)
    partite_seconda = estrai_partite(URL_SECONDA)
    partite_terza = estrai_partite(URL_TERZA)
    
    if len(partite_prima) >= 6 and len(partite_seconda) >= 4 and len(partite_terza) >= 3:
        scelte_prima = random.sample(partite_prima, 6)
        scelte_seconda = random.sample(partite_seconda, 4)
        scelte_terza = random.sample(partite_terza, 3)
        
        # NUOVA LOGICA: Creiamo una colonna per le categorie
        tutte_le_partite = scelte_prima + scelte_seconda + scelte_terza
        categorie = ["Prima Categoria"] * 6 + ["Seconda Categoria"] * 4 + ["Terza Categoria"] * 3
        
        df_partite = pd.DataFrame({"Categoria": categorie, "Partite": tutte_le_partite})
        df_partite.to_csv(FILE_SCHEDINA, index=False)
        st.rerun() 
    else:
        st.error("Non sono riuscito a trovare abbastanza partite sul sito. Controlla i link!")
        st.stop()
else:
    df_partite = pd.read_csv(FILE_SCHEDINA)

# --- 3. IL FORM PER I PRONOSTICI ---
# --- 3. IL FORM PER I PRONOSTICI CON SCADENZA AUTOMATICA ---
st.header("La Schedina della Settimana Seconda Giornata")
st.caption("Made By Esseba")
st.caption("LUCIO MERDA")

# --- IMPOSTA QUI LA DATA DI SCADENZA ---
# Esempio: 10 Maggio 2026 alle ore 14:30
scadenza = datetime(2026, 5, 15, 20, 30, tzinfo=ZoneInfo("Europe/Rome"))
adesso = datetime.now(ZoneInfo("Europe/Rome"))

# CONTROLLO ORARIO
if adesso < scadenza:
    # Se siamo in tempo, mostriamo il modulo
    with st.form("form_totocalcio"):
        nome_giocatore = st.text_input("Inserisci il tuo Nome")
        st.write("Seleziona 1, X, o 2 per ogni partita, Puoi non Rispondere se ti chiami Andrea Monai")
        
        pronostici_fatti = []
        
        # Dividiamo visivamente le categorie
        for cat in ["Prima Categoria", "Seconda Categoria", "Terza Categoria"]:
            st.subheader(f" {cat}")
            
            # Filtriamo solo le partite di questa categoria
            partite_categoria = df_partite[df_partite["Categoria"] == cat]["Partite"]
            
            for partita in partite_categoria:
                # Aggiungiamo index=None per far sì che nessun pallino sia già selezionato
                scelta = st.radio(partita, ["1", "X", "2"], horizontal=True, key=partita, index=None)
                
                # Se non seleziona nulla, Streamlit restituisce 'None'. 
                # Noi lo trasformiamo in uno spazio vuoto per inviarlo a Google.
                if scelta is None:
                    pronostici_fatti.append("")
                else:
                    pronostici_fatti.append(scelta)
                
            st.markdown("---")
            
        pulsante_invio = st.form_submit_button("Invia Giocata Definitiva")
      
        # --- SEZIONE 4: INVIO DATI (dentro il form) ---
        if pulsante_invio:
            if nome_giocatore.strip() == "":
                st.warning("Ma sei scemo? devi inserire il nome COGLIONE")
            else:
                url_form = "https://docs.google.com/forms/d/e/1FAIpQLSe4qwxFjLYQ-nxenG7cEIcRd4fSukdeUbtmZXL6laQ6VN4iKQ/formResponse"
                
                form_data = {
                    "entry.209404488": nome_giocatore,
                    "entry.1501733804": pronostici_fatti[0],
                    "entry.2143684766": pronostici_fatti[1],
                    "entry.328672958": pronostici_fatti[2],
                    "entry.1212089018": pronostici_fatti[3],
                    "entry.1836274014": pronostici_fatti[4],
                    "entry.805664275": pronostici_fatti[5],
                    "entry.1475285346": pronostici_fatti[6],
                    "entry.1518268040": pronostici_fatti[7],
                    "entry.510699695": pronostici_fatti[8],
                    "entry.497013538": pronostici_fatti[9],
                    "entry.186611401": pronostici_fatti[10],
                    "entry.158458027": pronostici_fatti[11],
                    "entry.1445830973": pronostici_fatti[12],
                }
                
                try:
                    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                    risposta = requests.post(url_form, data=form_data, headers=headers)
                    
                    if risposta.status_code == 200:
                        st.success(f"Grazie Mille {nome_giocatore}, pronostici inviati!")
                        
                        # --- INIZIO SCONTRINO VIRTUALE ---
                        st.markdown("### 🧾 La Tua Giocata")
                        st.info("Fai uno screenshot di questa schermata e non rompere il cazzo")
                        
                        # Creiamo una tabella elegante unendo le partite ai pronostici scelti
                        df_riepilogo = pd.DataFrame({
                            "Partita": df_partite["Partite"],
                            "Il tuo Pronostico": pronostici_fatti
                        })
                        
                        # st.table mostra una tabella fissa, perfetta per gli screenshot
                        st.table(df_riepilogo)
                        # --- FINE SCONTRINO VIRTUALE ---
                        
                    else:
                        st.error(f"Errore tecnico (Codice {risposta.status_code}).")
                        
                except Exception as e:
                    st.error(f"Errore di connessione: {e}")

else:
    # --- COSA SUCCEDE SE IL TEMPO È SCADUTO ---
    st.error(" LE GIOCATE SONO CHIUSE!")
    st.info(f"Il termine per l'invio era il {scadenza.strftime('%d/%m/%Y alle %H:%M')}.")
    st.write("Per questa giornata hai perso 2€ AHAHAHAHAHAHA")