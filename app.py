import streamlit as st
import requests
import pandas as pd
from io import StringIO
import random
import os

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

URL_PRIMA = "https://www.carnico.it/calendario/prima-categoria/?giornata=terza-giornata-prima-categoria"
URL_SECONDA = "https://www.carnico.it/calendario/seconda-categoria/?giornata=terza-giornata-seconda-categoria"
URL_TERZA = "https://www.carnico.it/calendario/terza-categoria/?giornata=terza-giornata-terza-categoria"

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
st.header("La Schedina della Settimana")

with st.form("form_totocalcio"):
    nome_giocatore = st.text_input("Inserisci il tuo Nome")
    st.write("Seleziona 1, X, o 2 per ogni partita")
    
    pronostici_fatti = []
    
    # NUOVA LOGICA: Dividiamo visivamente le categorie
    for cat in ["Prima Categoria", "Seconda Categoria", "Terza Categoria"]:
        st.subheader(f" {cat}")
        
        # Filtriamo solo le partite di questa categoria
        partite_categoria = df_partite[df_partite["Categoria"] == cat]["Partite"]
        
        for partita in partite_categoria:
            scelta = st.radio(partita, ["1", "X", "2"], horizontal=True)
            pronostici_fatti.append(scelta)
            
        st.markdown("---") # Aggiunge una linea di separazione elegante
        
    pulsante_invio = st.form_submit_button("Invia Giocata Definitiva")
    
    # --- 4. SALVATAGGIO DEI DATI ---
    if pulsante_invio:
        if nome_giocatore.strip() == "":
            st.warning("Devi inserire il tuo nome per partecipare stupido.")
        else:
            risultato_utente = {"Giocatore": nome_giocatore}
            
            # Ricostruiamo la lista di tutte le partite nell'ordine giusto
            tutte_le_partite_ordinate = df_partite["Partite"].tolist()
            for i, p in enumerate(tutte_le_partite_ordinate):
                risultato_utente[p] = pronostici_fatti[i]
            
            df_risultato = pd.DataFrame([risultato_utente])
            FILE_RISULTATI = "giocate_segrete.csv"
            
            if not os.path.exists(FILE_RISULTATI):
                df_risultato.to_csv(FILE_RISULTATI, index=False)
            else:
                df_risultato.to_csv(FILE_RISULTATI, mode='a', header=False, index=False)
                
            st.success(f"Grazie Mille {nome_giocatore},  ")