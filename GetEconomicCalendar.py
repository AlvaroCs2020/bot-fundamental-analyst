import requests
import xmltodict
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re
class GetEconomicCalendar:
    def __init__(self, url, path, currency1, currency2):
        self.url = url
        self.raw_xml = None
        self.data_dict = {"weeklyevents":{"events":[]}}
        self.data_path = path
        self.events = []
        self.currency1 = currency1
        self.currency2 = currency2
    def fetch_html(self):
        try:
            # Configurar opciones de Chrome
            options = Options()
            options.add_argument("--headless")  # Ejecutar sin interfaz gráfica
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            options.add_argument("--disable-blink-features=AutomationControlled")  # Evitar detección de bot
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            # Iniciar el navegador
            driver = webdriver.Chrome(options=options)
            print("Navegador iniciado, accediendo a la URL...")

            # Acceder a la página
            driver.get(self.url)
            time.sleep(5)  # Esperar a que el contenido dinámico se cargue

            # Obtener el HTML
            html = driver.page_source
            driver.quit()

            # Guardar el HTML para depuración
            with open("./data/calendar.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("HTML guardado en calendar.html")

            # Parsear el HTML con BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            return soup

        except Exception as e:
            print(f"Error al obtener el HTML: {e}")
            return None

    def extract_events_from_html(self):

        with open("calendar.html", "r", encoding="utf-8") as f:
            html = f.read()

        # Buscar el objeto JS window.calendarComponentStates[1] = {...};
        pattern = r'window\.calendarComponentStates\[1\]\s*=\s*({.*?});\s*\n'

        match = re.search(pattern, html, re.DOTALL)
        # print(match.group(1))
        # Buscar todos los posibles bloques {...}
        posibles_bloques = re.findall(r'\{.*?\}', match.group(1), re.DOTALL)

        events = []
        for bloque in posibles_bloques:
            try:
                data = json.loads(bloque)
                # eventos.append(data)
                if all(k in data for k in ["id", "name", "dateline", "currency", "impactName", "timeLabel"]):
                    base = {
                        "title":    data["name"],
                        "country":  data["currency"],
                        "date":     data["date"],
                        "time":     data["timeLabel"],
                        "impact":   data["impactName"],
                        "forecast": data["forecast"],
                        "previous": data["previous"],
                        "actual":   data["actual"],
                        "url":      data["soloUrl"]
                    }
                    events.append(base)
            except json.JSONDecodeError:
                continue  # ignoramos los que no son JSON válidos
        print("Se obtuvieron: " + str(len(events)) + " noticias ")
        self.events = events
        self.data_dict['weeklyevents']['event'] = events
        return self.events

    def generate_json(self, events):
        result = {"weeklyevents": {"event": events}}
        return json.dumps(result, indent=2)

    def fetch_xml(self):
        response = requests.get(self.url)
        response.raise_for_status()
        self.raw_xml = response.content

    def parse_xml(self):
        if self.raw_xml is None:
            raise ValueError("No XML content fetched. Call fetch_xml() first.")
        self.data_dict = xmltodict.parse(self.raw_xml)

    def filter_events(self, exclude_countries=None):
        if self.data_dict is None:
            raise ValueError("No parsed XML data. Call parse_xml() first.")

        events = self.data_dict.get("weeklyevents",{}).get("event",{})

        if not isinstance(events, list):
            events = [events]  # in case there's only one event

        filtered = [event for event in events if (event.get('country') in (self.currency1, self.currency2)) and event.get('previous') is not None ]

        self.data_dict['weeklyevents']['event'] = filtered

        return self.data_dict

    def to_json(self, indent=2):
        if self.data_dict is None:
            raise ValueError("No parsed data to convert. Call parse_xml() first.")
        return json.dumps(self.data_dict, indent=indent)

    def save_to_file(self, filepath, json_data):
        print("Luego del filtrado por divisa, se analizaran: "+ str(len(self.data_dict['weeklyevents']['event'])) + " noticias ")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json_data)

    def get_data(self):
        self.fetch_html()
        events = self.extract_events_from_html()
        json_data = self.filter_events()
        json_data = self.generate_json(json_data.get("weeklyevents").get("event"))
        self.save_to_file(self.data_path, json_data)



            ###self.__filter_events(exclude_countries=["USD", "EUR"])
            #self.__save_to_file(self.data_path
if __name__ == "__main__":
    url = 'https://www.forexfactory.com/calendar'
    calendar = GetEconomicCalendar(url,"calendar_filtered.json", "GBP", "USD")
    calendar.get_data()
    print("Filtered calendar saved as calendar_filtered.json")
