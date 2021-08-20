import aiohttp
import asyncio
from adapters.inosmi_ru import sanitize
from text_tools import calculate_jaundice_rate, split_by_words
import pymorphy2

async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def main():
    async with aiohttp.ClientSession() as session:
        morph = pymorphy2.MorphAnalyzer()
        
        html = await fetch(session, 'https://inosmi.ru/politic/20210820/250347187.html')
        text = sanitize(html, True)
        words = split_by_words(morph, text)

        rate = calculate_jaundice_rate(words, ['все', 'аутсайдер', 'побег'])
        print(rate)


asyncio.run(main())
