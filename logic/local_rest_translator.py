from googletrans import Translator


def translate_from_english_to_russian(english_text):
    translator = Translator()
    translated_text = translator.translate(english_text, src='en', dest='ru')
    return translated_text.text
