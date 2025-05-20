# Import required libraries
import os  
from dotenv import load_dotenv  
from operator import itemgetter
from langchain_openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough
import json
from pathlib import Path
from pprint import pprint
from langchain_openai import OpenAIEmbeddings
from datetime import datetime
from langchain.schema import HumanMessage, SystemMessage
from IPython.display import Markdown, display
from langchain.schema import AIMessage
import re
class EconomicDataAnalyzer:
    def __init__(self, api_key: str, model_name: str = "gpt-4-turbo", temperature: float = 0.0, use_grok_analysis : bool = False):
        os.environ["OPENAI_API_KEY"] = api_key
        self.model = ChatOpenAI(temperature=temperature, model_name=model_name)
        self.context = ""
        self.use_grok_analysis = use_grok_analysis
    def __save_json(self, path: str, text: str) -> bool:
        # Buscar el bloque JSON
        match = re.search(r'(\{\s*"weeklyevents"\s*:\s*\{[\s\S]+?\}\s*\})', text)

        if match:
            json_str = match.group(1)
            try:
                data = json.loads(json_str)
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                print(f"JSON guardado en: {path}")
                return True
            except json.JSONDecodeError as e:
                print("Error al parsear JSON:", e)
        else:
            print("No se encontró el bloque JSON en el texto.")

        return False

    def __save_text_to_file(self, path: str, content: str) -> None:
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)

    def __extract_overall_signals(self, text):
        # Mapas de sentimiento a valor numérico
        sentiment_map = {
            "bullish": 1,
            "bearish": -1,
            "neutral": 0
        }

        # Regex para encontrar las líneas OVERALL
        pattern = r"OVERALL:\s+([A-Z]+)\s+(BULLISH|BEARISH|NEUTRAL)\s+([0-9.]+)"
        matches = re.findall(pattern, text, flags=re.IGNORECASE)

        result = []
        for currency, sentiment, value in matches:
            sentiment_val = sentiment_map[sentiment.lower()]
            result.append((currency.upper(), (sentiment_val, float(value))))

        return result
    def __load_inputs(self, json_path: str, system_prompt_path: str, complementary_path: str):
        """Load and prepare full context from input files."""
        with open(json_path, "r", encoding="utf-8") as f_json:
            economic_json = json.dumps(json.load(f_json), indent=2)

        with open(system_prompt_path, "r", encoding="utf-8") as f_sys:
            system_prompt = f_sys.read()

        self.context = f"""
        System Message:
        {system_prompt}

        Economic News JSON:
        {economic_json}
        """

    def __analyze(self, query: str = "Please, analyze the data") -> str:
        """Run the analysis using the loaded context and return the response content."""
        if not self.context:
            raise ValueError("Context is empty. Call load_inputs() first.")

        messages = [
            SystemMessage(content=self.context),
            HumanMessage(content=query)
        ]
        print("[API CALL - INIT]")
        response = self.model.invoke(messages)
        print("[API CALL - DONE]")
        return response.content
    def get_analysis_result(self):
        system_prompt_path = "systemMessage.txt"
        self.__load_inputs(
                json_path="calendar_filtered.json",
                system_prompt_path=system_prompt_path,
                complementary_path=""
                )
        analysis = self.__analyze()
        output = self.__extract_overall_signals(analysis)
        self.__save_text_to_file(path= "AnalysisResult.txt",content = str(analysis))
        return output
