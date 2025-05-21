import os
from supabase import create_client, Client
from dotenv import load_dotenv
from GetEconomicCalendar import GetEconomicCalendar
from EconomicDataAnalyzer import EconomicDataAnalyzer
import time
from datetime import datetime
import sys
def main(currency1 : str = "EUR", currency2 : str = "USD"):
    load_dotenv()
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key, )

    print("[MAIN - ECONOMIC NEWS ANALYST BOT {}{} ]".format(currency1, currency2))
    #Get the economic calendar
    url = 'https://www.forexfactory.com/calendar'
    print("[MAIN - EXTRACTING {}/{} NEWS]".format(currency1, currency2))
    calendar = GetEconomicCalendar(url, "calendar_filtered.json", currency1, currency2)
    calendar.get_data()

    #Get Grok Analysis maybe twitter
    ##grokAnalysis.txt generation

    #GPT analysis
    analyzer = EconomicDataAnalyzer(api_key=str(os.getenv("OPENAI_API_KEY")), model_name = "gpt-4.1-mini", currency1 = currency1, currency2 = currency2)
    # [('USD', (1, 0.65)), ('EUR', (0, 0.55)), ('EURUSD', (-1, 0.6))] ejemplo
    output = analyzer.get_analysis_result()
    if output is not []:
        print("[CORRECT OUTPUT]")
    else:
        return
    # Save results
    prediction_currency2, coef_currency2 = output[0][1] #CURRENCY 2
    prediction_currency1, coef_currency1 = output[1][1] #CURRENCY 1
    prediction_currency_pair, coef_currency_pair = output[2][1] ##CURRENCY1CURRENCY2
    pair_name = analyzer.get_pair_name()
    new_row = {"pair_name":pair_name, "currency_1": prediction_currency1,"currency_2": prediction_currency2, "pair":prediction_currency_pair}
    response = (
        supabase.table("EconomicCalendarResults")
        .insert(new_row)
        .execute()
    )
    print(response)


def mostrar_progreso(valor):
    print(f"\rProgreso: {valor}%", end='', flush=True)
def loop():
    #main("EUR", "USD")
    #main("GBP", "USD")
    while True:
        now = datetime.now()
        if now.minute == 0 or now.minute == 30:
            print("¡Son las 10 PM!")
            # Aquí podés hacer lo que quieras que pase a las 10 PM
            main("EUR", "USD")
            main("GBP", "USD")
            # Esperar 60 segundos para no imprimir múltiples veces
            time.sleep(60)
        else:
            # Dormir 10 segundos para no sobrecargar la CPU
            print(f"\rHora del bot: {str(now.hour)} : {str(now.minute)} : {str(now.second)}", end='', flush=True)

            time.sleep(10)
        sys.stdout.flush()
if __name__ == "__main__":
    loop()
    #main("EUR","USD")
    #main("GBP","USD")



