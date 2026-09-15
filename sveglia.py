from selenium import webdriver
import time

# INSERISCI QUI SOTTO IL LINK DEL TUO SITO
URL = "https://totocarnico.streamlit.app/"
options = webdriver.ChromeOptions()
options.add_argument('--headless') # Fa girare il browser in background

print("Avvio il browser invisibile...")
driver = webdriver.Chrome(options=options)
driver.get(URL)

# Aspetta 10 secondi per far caricare la grafica di Streamlit
time.sleep(10) 

# Simula uno scroll della pagina verso il basso
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
print("Pagina visitata e scorsa con successo! Il sito è sveglio.")

driver.quit()
