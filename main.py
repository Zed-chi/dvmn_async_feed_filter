import asyncio

import aiohttp
import pymorphy2

from adapters.inosmi_ru import sanitize
from text_tools import calculate_jaundice_rate, split_by_words
from anyio import sleep, create_task_group, run


NEGATIVE_PATH = "./charged_dict/negative_words.txt"
POSITIVE_PATH = "./charged_dict/positive_words.txt"
TEST_ARTICLES = [
    "https://inosmi.ru/science/20210821/250351807.html",
    "https://inosmi.ru/science/20210820/250344124.html",
    "https://inosmi.ru/science/20210819/250338925.html",
    "https://inosmi.ru/science/20210817/250325101.html",
    "https://inosmi.ru/science/20210817/250323544.html",
]

async def process_article(
    session, morph, url,
    positive_words, negative_words
):
    html = await fetch(
        session, url
    )
    text = sanitize(html, True)
    words = split_by_words(morph, text)
    positive_rate = calculate_jaundice_rate(words, positive_words)
    negative_rate = calculate_jaundice_rate(words, negative_words)
    print('Address:', url)        
    print(f"\twords {len(words)}")
    print(f"\t+rate {positive_rate}")
    print(f"\t-rate {negative_rate}")        
            
def get_words_from_file(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read().split("\n")


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def main():
    morph = pymorphy2.MorphAnalyzer()
    positive_words = get_words_from_file(POSITIVE_PATH)
    negative_words = get_words_from_file(NEGATIVE_PATH)
    
    async with aiohttp.ClientSession() as session:
        async with create_task_group() as tg:        
            for url in TEST_ARTICLES:                    
                tg.start_soon(
                    process_article, session, morph,
                    url, positive_words, negative_words
                )
    


#asyncio.run(main())
run(main)

