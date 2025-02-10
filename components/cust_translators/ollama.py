import requests
import cutlet
import regex as re
import unicodedata




pattern = re.compile(r'([\p{IsHan}\p{IsBopo}\p{IsHira}\p{IsKatakana}]+)', re.UNICODE)
katsu = cutlet.Cutlet()

class OllamaTranslator:
    def __init__(self, model="deepseek-r1:1.5b", api_url="http://localhost:11434/api/generate"):
        self.model = model
        self.api_url = api_url
        self.system_prompt = f"""You are a professional translation expert. 
        Rules of translation:
        1. Your answer must include exactly one XML element <translation> that contains only the translated text.
        2. Inside the <translation> tag, do not include any extra words, annotations, or formatting—only the pure translation.
        3. Additional explanations or notes outside the XML element are allowed if they help clarify the translation.
        4. Do not use markdown or any other formatting inside the <translation> tag.
        5. Prioritize natural localization over a literal word-for-word translation.
        6. Preserve specialized terms and proper names without adaptation (think twice about it to be sure). Do not expand abbreviation
        8. Your anwser should always ends with <translation> tag.
        9. If you can translate text, translate it. Do not transcribe it if its not a name or a term of some kind. When doing so, stick to the Polivanov system.
        10. Keep in mind, you are translating pages from manga. So try to keep style and personality of the original text. 
        11. If you see a wierd word that have no meaning or no translation, think step by step and figure out the best way to translate it. It may include errors on OCR stage. 
        12. Make sure that translated text is following the rules of the language you are translating to.
        13. While writing something, write it in the same language you are translating into. Explanations, comments, etc. should be written in the same language as the translation."""

    def translate_text(self, text,  full_text, target_lang):
        """
        Translates the given text to the target language using the Ollama model.
        """
        # Construct the prompt for translation
        if pattern.match(text):
            text = katsu.romaji(text)
        prompt = f"""
        There is full unordered ocr text, but do not translate it. Its only for context. Do not include it or translation of it into <translation> tag.: 
        '
        {full_text}
        ' 

        Your task is to translate only the following text from its detected source language into {target_lang}. Your response may include additional commentary or context outside the XML element if it enhances clarity, but the XML element must contain exclusively the translation. Try to find connectionss in the provided full text and adapt them as you translating - to translate punctuation, lettercase and names. Translate the following text:
        '
        {text}
        '"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "system": self.system_prompt,
        }

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()  # Raise an exception for HTTP errors
            result = response.json()
            output = result.get("response", "").strip()

            matches = re.findall(r"<translation>(.*?)</translation>", output, re.DOTALL)
            clean_text = matches[-1].strip() if matches else output  
            clean_text = self.normalize_wide_letters(clean_text)

            print(f'\n-"{output}"')
            return type('TranslationResult', (object,), {'text': clean_text})()
        except requests.RequestException as e:
            print(f"Error communicating with Ollama: {e}")
            return type('TranslationResult', (object,), {'text': ""})()
        
    def normalize_wide_letters(self, text):
        result = []
        for char in text:
            if 'Ｆ' <= char <= 'Ｚ' or 'Ａ' <= char <= 'Ｚ':
                normalized_char = unicodedata.normalize('NFKC', char)
                result.append(normalized_char)
            else:
                result.append(char)
        return ''.join(result)