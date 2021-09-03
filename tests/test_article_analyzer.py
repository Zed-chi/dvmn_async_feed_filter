import pymorphy2
import pytest
from article_analyzer import process_article
from config import NEGATIVE_WORDS_PATH, POSITIVE_WORDS_PATH
from text_tools import load_words_from_file


@pytest.mark.asyncio
async def test_processing_timeout():
    morph = pymorphy2.MorphAnalyzer()
    positive_words = load_words_from_file(POSITIVE_WORDS_PATH)
    negative_words = load_words_from_file(NEGATIVE_WORDS_PATH)
    with open("./tests/bigfile.txt", "r", encoding="utf-8") as file:
        text = file.read()

    result = await process_article(
        morph, positive_words, negative_words, 1, text=text
    )
    assert result.status == "TIMEOUT"
