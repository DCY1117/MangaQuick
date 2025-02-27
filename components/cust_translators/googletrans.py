import requests
from googletrans import Translator
import asyncio

class GoogleTrans:
    def __init__(self):
        pass
    
    def translate_text(self, text, target_lang):
        target_lang = target_lang.split('-')[0].lower()
        return asyncio.run(self.async_translate_text(text, target_lang))
        

    async def async_translate_text(self, text, target_lang):
        """
        Translates the given text to the target language using googletrans.
        """

        async with Translator() as translator:
            result = await  translator.translate(text, dest=target_lang)
            print(result.text)
        return type('TranslationResult', (object,), {'text': result.text})()
