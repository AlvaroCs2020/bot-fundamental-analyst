import os
from supabase import create_client, Client
from dotenv import load_dotenv
from EconomicDataAnalyzer import EconomicDataAnalyzer
from CalendarUpdatesCheck import CalendarUpdatesCheck
import time
from datetime import datetime
import sys
def call_analyst_and_save_to_db(currency1 : str = "EUR", currency2 : str = "USD"):
    load_dotenv()
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key, )

    print("[MAIN - ECONOMIC NEWS ANALYST BOT {}{} ]".format(currency1, currency2))
    #Get the economic calendar
    print("[MAIN - EXTRACTING {}/{} NEWS]".format(currency1, currency2))


    #GPT analysis
    analyzer = EconomicDataAnalyzer(api_key=str(os.getenv("OPENAI_API_KEY")), model_name = "gpt-4.1", currency1 = currency1, currency2 = currency2)
    # [('USD', (1, 0.65)), ('EUR', (0, 0.55)), ('EURUSD', (-1, 0.6))] ejemplo
    output = analyzer.get_analysis_result()
    if output is not []:
        print("[MAIN - CORRECT OUTPUT]")
    else:
        print("[MAIN - INCORRECT OUTPUT]")
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
def main_loop():
    list_of_pairs = [("GBP", "USD"), ("EUR", "USD")]
    url = "https://www.forexfactory.com/calendar"
    calendar_updates_checker = CalendarUpdatesCheck(list_of_pairs, url=url)
    a = calendar_updates_checker.process() #Traemos todas las noticias y creamos los json

    for (currency1, currency2) in a: #Creamos todos los analisis y cargamos la db
        call_analyst_and_save_to_db(currency1, currency2)

    while True:
        now = datetime.now()
        if now.minute % 5 == 0: #cada 5 min reviso investing y comparo contra las ultimas noticias que me traje
            print("[MAIN - check news]")
            currencies_to_analyze = []
            currencies_to_analyze = calendar_updates_checker.process()

            for (currency1, currency2) in currencies_to_analyze: ##Multiple threading
                call_analyst_and_save_to_db(currency1, currency2)

            time.sleep(30)
        else:
            # Dormir 10 segundos para no sobrecargar la CPU
            print(f"\r[MAIN - Hora del bot: {str(now.hour)} : {str(now.minute)} : {str(now.second)}]", end='', flush=True)

            time.sleep(1)

        sys.stdout.flush()

if __name__ == "__main__":
    main_loop()




