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
# INCOLLA QUI IL LINK CSV DEL TUO FOGLIO GOOGLE
LINK_CSV_FOGLIO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTMNpU0j7ZM0EACZxO2-SfHpPKnXxe7rXSsa0D4pptqecMvW-2LBW771Cov0XUib0ZDc2D1k_IEc0tk/pub?gid=1209485560&single=true&output=csv"
def recupera_vecchia_giocata(nome_cercato):
    try:
        # skiprows=4 fa partire la lettura dalla riga 5
        df_risposte = pd.read_csv(LINK_CSV_FOGLIO, skiprows=4)
        
        # Trasforma i nomi in minuscolo
        df_risposte.columns = df_risposte.columns.astype(str).str.strip().str.lower()
        
        # 1. CONTROLLO COLONNA NOME
        if 'nome' not in df_risposte.columns:
            st.error(f"🕵️ ERRORE FOGLIO: Non trovo la colonna 'nome'. Python sta leggendo queste colonne: {list(df_risposte.columns)}")
            return None
            
        df_risposte['nome'] = df_risposte['nome'].astype(str).str.strip().lower()
        
        # Filtriamo le righe corrispondenti al giocatore
        giocate_trovate = df_risposte[df_risposte['nome'] == nome_cercato.strip().lower()]
        
        # Se non ci sono giocate, restituisce None tranquillamente
        if giocate_trovate.empty:
            return None
            
        # Prende l'ultima giocata inserita da quella persona
        giocata_utente = giocate_trovate.iloc[-1]
        
        vecchi_segni = []
        for i in range(1, 14):
            nome_colonna = f'partita {i}'
            
            # 2. CONTROLLO COLONNE PARTITE
            if nome_colonna not in df_risposte.columns:
                st.error(f"🕵️ ERRORE FOGLIO: Mi sono bloccato perché manca o è scritta male la colonna '{nome_colonna}' nel foglio Excel!")
                return None
                
            segno = str(giocata_utente[nome_colonna])
            if segno.lower() == 'nan':
                segno = ""
                
            vecchi_segni.append(segno)
            
        return vecchi_segni
        
    except Exception as e:
        # 3. CONTROLLO ERRORI TECNICI GENERARLI
        st.error(f"🕵️ ERRORE DI SISTEMA: {e}")
        return None

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
# CAMBIA QUESTO NUMERO OGNI SETTIMANA
NUMERO_GIORNATA = 2 

# Fissiamo il "Seme": questo garantisce che l'estrazione casuale 
# sia IDENTICA ogni volta che il sito si riaccende per questa giornata.
random.seed(NUMERO_GIORNATA)
URL_PRIMA = "https://www.carnico.it/calendario/prima-categoria/?giornata=seconda-giornata-prima-categoria"
URL_SECONDA = "https://www.carnico.it/calendario/seconda-categoria/?giornata=seconda-giornata-seconda-categoria"
URL_TERZA = "https://www.carnico.it/calendario/terza-categoria/?giornata=seconda-giornata-terza-categoria"
st.info(f"Schedina della {NUMERO_GIORNATA}ª Giornata")

# Ora eseguiamo l'estrazione (che sarà sempre la stessa per il numero 2)
partite_prima = estrai_partite(URL_PRIMA)
partite_seconda = estrai_partite(URL_SECONDA)
partite_terza = estrai_partite(URL_TERZA)

if len(partite_prima) >= 6 and len(partite_seconda) >= 4 and len(partite_terza) >= 3:
    # Dato che abbiamo usato random.seed(2), queste scelte saranno 
    # casuali ma "congelate" per tutta la settimana!
    scelte_prima = random.sample(partite_prima, 6)
    scelte_seconda = random.sample(partite_seconda, 4)
    scelte_terza = random.sample(partite_terza, 3)
    
    tutte_le_partite = scelte_prima + scelte_seconda + scelte_terza
    categorie = ["Prima Categoria"] * 6 + ["Seconda Categoria"] * 4 + ["Terza Categoria"] * 3
    
    df_partite = pd.DataFrame({"Categoria": categorie, "Partite": tutte_le_partite})
else:
    st.error("Errore nel recupero partite. Verifica i link!")
    st.stop()

# --- 3. IL FORM PER I PRONOSTICI CON SCADENZA AUTOMATICA ---
st.header("La Schedina della Settimana")
st.caption("Made By Esseba")
st.caption("LUCIO MERDA")

# --- IMPOSTA QUI LA DATA DI SCADENZA ---
scadenza = datetime(2026, 5, 15, 20, 30, tzinfo=ZoneInfo("Europe/Rome"))
adesso = datetime.now(ZoneInfo("Europe/Rome"))

# CONTROLLO ORARIO
if adesso < scadenza:
    # --- PARTE INPUT NOME E CARICAMENTO ---
    nome_giocatore = st.text_input("Inserisci il tuo Nome")

    vecchi_pronostici = None
    if nome_giocatore:
        if st.button("Carica la mia ultima giocata"):
            st.info("Sto cercando nel database...")
            vecchi_pronostici = recupera_vecchia_giocata(nome_giocatore)
            if vecchi_pronostici:
                st.success("Giocata trovata, se vuoi modificarla puoi farlo ma stai attento che ti vedo.")
            else:
                st.warning("Non ho trovato giocate precedenti per questo nome")

    # --- INIZIO DEL MODULO VERO E PROPRIO ---
    with st.form("form_totocalcio"):
        st.write("Seleziona 1, X, o 2 per ogni partita. Puoi non Rispondere se ti chiami Andrea Monai")
        
        pronostici_fatti = []
        indice_globale = 0 
        
        for cat in ["Prima Categoria", "Seconda Categoria", "Terza Categoria"]:
            st.subheader(f" {cat}")
            partite_categoria = df_partite[df_partite["Categoria"] == cat]["Partite"]
            
            for partita in partite_categoria:
                indice_predefinito = None
                if vecchi_pronostici and len(vecchi_pronostici) > indice_globale:
                    segno = vecchi_pronostici[indice_globale]
                    if segno == "1": indice_predefinito = 0
                    elif segno == "X": indice_predefinito = 1
                    elif segno == "2": indice_predefinito = 2
                
                scelta = st.radio(partita, ["1", "X", "2"], horizontal=True, key=partita, index=indice_predefinito)
                
                if scelta is None:
                    pronostici_fatti.append("")
                else:
                    pronostici_fatti.append(scelta)
                
                indice_globale += 1
            st.markdown("---")
            
        pulsante_invio = st.form_submit_button("Invia Giocata")

    # --- SEZIONE 4: INVIO DATI (Deve essere sotto il form ma dentro il controllo scadenza) ---
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
                    st.markdown("### La Tua Giocata")
                    st.info("Fai uno screenshot di questa schermata e non rompere il cazzo")
                    
                    df_riepilogo = pd.DataFrame({
                        "Partita": df_partite["Partite"],
                        "Il tuo Pronostico": pronostici_fatti
                    })
                    st.table(df_riepilogo)
                else:
                    st.error(f"Errore tecnico (Codice {risposta.status_code}).")
            except Exception as e:
                st.error(f"Errore di connessione: {e}")

else:
    # --- COSA SUCCEDE SE IL TEMPO È SCADUTO ---
    st.error("LE GIOCATE SONO CHIUSE!")
    st.info(f"Il termine per l'invio era il {scadenza.strftime('%d/%m/%Y alle %H:%M')}.")
    st.write("Per questa giornata hai perso 2€ AHAHAHAHAHAHA")