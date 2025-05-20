import os
from supabase import create_client, Client
from dotenv import load_dotenv
from GetEconomicCalendar import GetEconomicCalendar
from EconomicDataAnalyzer import EconomicDataAnalyzer
import time
from datetime import datetime

os.environ["OPENAI_API_KEY"]='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'

def main():
    load_dotenv()
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key, )

    print("[MAIN - ECONOMIC NEWS ANALYST BOT]")
    #Get the economic calendar
    url = 'https://www.forexfactory.com/calendar'
    calendar = GetEconomicCalendar(url, "calendar_filtered.json", "USD", "EUR")
    calendar.get_data()

    #Get Grok Analysis maybe twitter
    ##grokAnalysis.txt generation

    #GPT analysis
    analyzer = EconomicDataAnalyzer(api_key=str(os.getenv("OPENAI_API_KEY")), model_name = "gpt-4.5-preview")
    # [('USD', (1, 0.65)), ('EUR', (0, 0.55)), ('EURUSD', (-1, 0.6))] ejemplo
    output = analyzer.get_analysis_result()
    if output is not []:
        print("[CORRECT OUTPUT]")
    else:
        return
    # Save results
    prediction_usd, coef_usd = output[0][1] #CURRENCY 2
    prediction_eur, coef_eur = output[1][1] #CURRENCY 1
    prediction_eurusd, coef_eurusd = output[2][1] ##CURRENCY1CURRENCY2

    new_row = {"USD": prediction_usd, "USD_COEF": coef_usd, "EUR": prediction_eur, "EUR_COEF": coef_eur, "EURUSD": prediction_eurusd, "EURUSD_COEF": coef_eurusd}
    response = (
        supabase.table("EconomicCalendarResults")
        .insert(new_row)
        .execute()
    )
    print(response)

def loop():
    while True:
        now = datetime.now()
        if now.hour == 22 and now.minute == 0:
            print("¡Son las 10 PM!")
            # Aquí podés hacer lo que quieras que pase a las 10 PM
            main()
            # Esperar 60 segundos para no imprimir múltiples veces
            time.sleep(60)
        else:
            # Dormir 10 segundos para no sobrecargar la CPU
            time.sleep(10)

if __name__ == "__main__":
    main()


