from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        print("Opening Streamlit app...")

        page.goto(
            "https://totocarnico.streamlit.app/",
            wait_until="networkidle"
        )

        # Aspetta che il runtime Streamlit si stabilizzi
        page.wait_for_timeout(8000)

        # Simula attività utente minima (molto importante)
        page.mouse.move(200, 200)
        page.mouse.click(200, 200)

        print("App fully loaded. Keeping session alive...")

        # Mantieni sessione abbastanza a lungo
        time.sleep(25)

        print("Closing session.")
        browser.close()

if __name__ == "__main__":
    run()
