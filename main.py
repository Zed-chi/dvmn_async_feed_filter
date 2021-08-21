import asyncio
import logging
from datetime import datetime
from enum import Enum

import aiohttp
import pymorphy2
from anyio import create_task_group, run, sleep
from async_timeout import timeout

from adapters import ArticleNotFound
from adapters.inosmi_ru import sanitize
from text_tools import calculate_jaundice_rate, split_by_words


logging.basicConfig(level=logging.INFO)
PROCESS_TIME = 3
NEGATIVE_PATH = "./charged_dict/negative_words.txt"
POSITIVE_PATH = "./charged_dict/positive_words.txt"
TEST_ARTICLES = [
    "https://inosmi.ru/science/20210821/250351807.html",
    "https://inosmi.ru/science/20210820/250344124.html",
    "https://inosmi.ru/science/20210819/250338925.html",
    "https://inosmi.ru/science/20210817/250325101.html",
    "https://inosmi.ru/science/20210817/250323544.html",
]


class ProcessingStatus(Enum):
    OK = "OK"
    FETCH_ERROR = "FETCH_ERROR"
    PARSING_ERROR = "PARSING_ERROR"
    TIMEOUT = "TIMEOUT"


class Result:
    def __init__(self, address, words_count, pos_rate, neg_rate, status, time=0):
        self.address = address
        self.words_count = words_count
        self.pos_rate = pos_rate
        self.neg_rate = neg_rate
        self.status = status
        self.time = time


async def process_article(
    session, morph, url, positive_words, negative_words, results_container
):
    address = "Not Loaded"
    word_count = 0
    positive_rate = None
    negative_rate = None
    status = None
    time = 0
    try:
        async with timeout(PROCESS_TIME):
            start = datetime.now()
            html = await fetch(session, url)
            text = sanitize(html, True)
            words = split_by_words(morph, text)
            positive_rate = calculate_jaundice_rate(words, positive_words)
            negative_rate = calculate_jaundice_rate(words, negative_words)
            address = url
            word_count = len(words)
            status = ProcessingStatus.OK.value
            time = datetime.now() - start            
    except aiohttp.client_exceptions.ClientResponseError:
        status = ProcessingStatus.FETCH_ERROR.value
    except ArticleNotFound:
        status = ProcessingStatus.PARSING_ERROR.value
    except asyncio.TimeoutError:
        status = ProcessingStatus.TIMEOUT.value
    finally:
        result = Result(
            address, word_count, positive_rate, negative_rate, status, time
        )
        results_container.append(result)


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

    results = []

    async with aiohttp.ClientSession() as session:
        async with create_task_group() as tg:
            for url in TEST_ARTICLES:
                tg.start_soon(
                    process_article,
                    session,
                    morph,
                    url,
                    positive_words,
                    negative_words,
                    results,
                )

    for i in results:
        print(f"Address {i.address}")
        print(f"\tstatus {i.status}")
        print(f"\twords count {i.words_count}")
        print(f"\t+rate {i.pos_rate}")
        print(f"\t-rate {i.neg_rate}")
        print(f"\ttime {i.time}")


if __name__ == "__main__":
    run(main)
