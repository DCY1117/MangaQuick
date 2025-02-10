import requests
import cutlet
import regex as re

pattern = re.compile(r'([\p{IsHan}\p{IsBopo}\p{IsHira}\p{IsKatakana}]+)', re.UNICODE)
katsu = cutlet.Cutlet()

class OllamaTranslator:
    def __init__(self, model="deepseek-r1:1.5b", api_url="http://localhost:11434/api/generate"):
        self.model = model
        self.api_url = api_url

    def translate_text(self, text, target_lang):
        """
        Translates the given text to the target language using the Ollama model.
        """
        # Construct the prompt for translation
        if pattern.match(text):
            text = katsu.romaji(text)
        prompt = f"""You are a professional translation expert. 
        Rules of translation:
        1. Your answer must include exactly one XML element <translation> that contains only the translated text.
        2. Inside the <translation> tag, do not include any extra words, annotations, or formatting—only the pure translation.
        3. Additional explanations or notes outside the XML element are allowed if they help clarify the translation.
        4. Do not use markdown or any other formatting inside the <translation> tag.
        5. Prioritize natural localization over a literal word-for-word translation.
        6. Preserve specialized terms and proper names as they are.
        7. Translate only the portion of the text written in the source language.
        8. Your anwser should always ends with <translation> tag.
        9. If you can translate text, translate it. Do not transcribe it if its not a name or a term of some kind.
        Your task is to translate the following text from its detected source language into {target_lang}. Your response may include additional commentary or context outside the XML element if it enhances clarity, but the XML element must contain exclusively the translation. Translate the following text:
        '{text}'"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()  # Raise an exception for HTTP errors
            result = response.json()
            output = result.get("response", "").strip()

            matches = re.findall(r"<translation>(.*?)</translation>", output, re.DOTALL)
            clean_text = matches[-1].strip() if matches else output  

            print(output)
            return type('TranslationResult', (object,), {'text': clean_text})()
        except requests.RequestException as e:
            print(f"Error communicating with Ollama: {e}")
            return type('TranslationResult', (object,), {'text': ""})()