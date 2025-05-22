import os
import json
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

class CalendarUpdatesCheck:
    def __init__(self, list_of_pairs, url):
        self.list_of_pairs = list_of_pairs
        self.data_dict = {"weeklyevents": {"event": []}}
        self.url = str(url)
        self.analysis_required: bool = False
        self.base_path = os.path.dirname(os.path.abspath(__file__))  # Ruta base del script

    def __get_full_calendar_html(self):
        try:
            self.data_dict = {"weeklyevents": {"event": []}}

            options = Options()
            options.add_argument("--headless")
            options.add_argument("user-agent=Mozilla/5.0 ... Chrome/120.0.0.0 Safari/537.36")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            driver = webdriver.Chrome(options=options)
            print("Navegador iniciado, accediendo a la URL...")
            driver.get(self.url)
            time.sleep(5)
            html = driver.page_source
            driver.quit()

            # Guardar HTML
            file_path = os.path.join(self.base_path, "data", "calendar.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html)
            print("HTML guardado en calendar.html")

            soup = BeautifulSoup(html, 'html.parser')
            return soup
        except Exception as e:
            print(f"Error al obtener el HTML: {e}")
            return None

    def __extract_all_events_from_html(self):
        file_path = os.path.join(self.base_path, "data", "calendar.html")
        with open(file_path, "r", encoding="utf-8") as f:
            html = f.read()

        pattern = r'window\.calendarComponentStates\[1\]\s*=\s*({.*?});\s*\n'
        match = re.search(pattern, html, re.DOTALL)
        data_block = re.findall(r'\{.*?\}', match.group(1), re.DOTALL)

        events = []
        for bloque in data_block:
            try:
                data = json.loads(bloque)
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
                continue

        print(f"[ CALENDAR UPDATE CHECKER - Se obtuvieron: {len(events)} noticias ]")
        self.data_dict['weeklyevents']['event'] = events
        return self.data_dict

    def filter_events_to_dict(self, currency1, currency2):
        events = self.data_dict.get("weeklyevents", {}).get("event", [])
        if not isinstance(events, list):
            events = [events]
        filtered = [event for event in events if event.get('country') in (currency1, currency2)]
        return {"weeklyevents": {"event": filtered}}

    def save_events_per_pair_to_json(self, save_as_old: bool = False):
        for (currency1, currency2) in self.list_of_pairs:
            name_of_pair = f"{currency1}{currency2}"
            data_dict = self.filter_events_to_dict(currency1, currency2)
            data_json = json.dumps(data_dict, indent=2)

            file_new = os.path.join(self.base_path, "data", f"filtered_events_{name_of_pair}.json")
            file_old = os.path.join(self.base_path, "data", f"filtered_events_{name_of_pair}_old.json")

            if save_as_old:
                with open(file_old, "w", encoding="utf-8") as f:
                    f.write(data_json)
            else:
                with open(file_new, "w", encoding="utf-8") as f:
                    f.write(data_json)
                if not os.path.exists(file_old):
                    with open(file_old, "w", encoding="utf-8") as f:
                        f.write(data_json)

    def check_new_events_or_update(self):
        currencies_that_need_new_analysis = []

        for (currency1, currency2) in self.list_of_pairs:
            self.analysis_required = False
            name_of_pair = f"{currency1}{currency2}"

            file_old = os.path.join(self.base_path, "data", f"filtered_events_{name_of_pair}_old.json")
            file_new = os.path.join(self.base_path, "data", f"filtered_events_{name_of_pair}.json")

            with open(file_old, 'r', encoding='utf-8') as f_old:
                dict_old = json.load(f_old)

            with open(file_new, 'r', encoding='utf-8') as f_new:
                dict_new = json.load(f_new)

            events_old = dict_old.get("weeklyevents", {}).get("event", [])
            events_new = dict_new.get("weeklyevents", {}).get("event", [])

            if not events_old or not events_new:
                print("No hay archivos json para comparar")
                return False

            for event in events_new:
                title = event.get("title")
                country = event.get("country")
                match_old = [e for e in events_old if e.get("title") == title and e.get("country") == country]

                if not match_old:
                    self.analysis_required = True
                    continue

                old = match_old[0]
                if not (str(event.get("forecast")) == str(old.get("forecast")) and
                        str(event.get("previous")) == str(old.get("previous")) and
                        str(event.get("actual")) == str(old.get("actual"))):
                    self.analysis_required = True
                    print(f"LLEGO UNA UPDATE PARA EL PAR {name_of_pair} {title} {country} actual {event.get('actual')} viejo: {old.get('actual')}")

            if self.analysis_required:
                currencies_that_need_new_analysis.append((currency1, currency2))

        return currencies_that_need_new_analysis

    def process(self):
        self.__get_full_calendar_html()
        self.__extract_all_events_from_html()
        self.save_events_per_pair_to_json()
        currencies_that_need_new_analysis = self.check_new_events_or_update()
        self.save_events_per_pair_to_json(save_as_old=True)
        return currencies_that_need_new_analysis

def main():
    list_of_pairs = [("GBP", "USD"), ("EUR", "USD")]
    url = "https://www.forexfactory.com/calendar"
    checker = CalendarUpdatesCheck(list_of_pairs, url=url)
    checker.process()

if __name__ == "__main__":
    main()