import asyncio
import string


def load_words_from_file(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        return file.read().splitlines()


async def _clean_word(word):
    chars_to_clean = [
        "«","»", ".",",",
        " - ","!","?","(",
        ")","[","]",'"',"'",
        ":",";","...",
    ]
    for char in chars_to_clean:
        word = word.replace(char, "")
        await asyncio.sleep(0)
    word = word.strip(string.punctuation)
    return word


async def split_by_words(morph, text):
    """Учитывает знаки пунктуации, регистр и словоформы, выкидывает предлоги."""
    words = []
    for word in text.split():
        cleaned_word = await _clean_word(word)
        normalized_word = morph.parse(cleaned_word)[0].normal_form
        if len(normalized_word) > 2 or normalized_word == "не":
            words.append(normalized_word)
        await asyncio.sleep(0)
    return words


async def calculate_jaundice_rate(article_words, charged_words):
    """Расчитывает желтушность текста, принимает список "заряженных" слов и ищет их внутри article_words."""

    if not article_words:
        return 0.0

    found_charged_words = 0
    for word in article_words:
        if word in set(charged_words):
            found_charged_words += 1
        await asyncio.sleep(0)

    score = found_charged_words / len(article_words) * 100

    return round(score, 2)
