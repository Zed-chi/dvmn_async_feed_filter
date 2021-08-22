import asyncio
from enum import Enum
from time import monotonic

import aiohttp
import pymorphy2
from aiohttp.client_exceptions import ClientConnectorError, ClientResponseError
from anyio import create_task_group, run
from async_timeout import timeout

from adapters import ArticleNotFound
from adapters.inosmi_ru import sanitize
from text_tools import calculate_jaundice_rate, split_by_words
from dataclasses import dataclass




DEFAULT_PROCESS_TIME = 3
NEGATIVE_WORDS_PATH = "./charged_dict/negative_words.txt"
POSITIVE_WORDS_PATH = "./charged_dict/positive_words.txt"
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


@dataclass
class Result:
    address:str
    words_count:int
    pos_rate:float
    neg_rate:float
    status:str
    time:float = 0.0


async def process_article(
    session,
    morph,
    url,
    positive_words,
    negative_words,
    results_container,
    process_timeout=DEFAULT_PROCESS_TIME,
):
    word_count = 0
    positive_rate = None
    negative_rate = None
    status = None
    process_time = 0
    try:
        async with timeout(process_timeout):
            start_time = monotonic()
            html = await fetch(session, url)
            text = sanitize(html, True)
            words = split_by_words(morph, text)
            positive_rate = calculate_jaundice_rate(words, positive_words)
            negative_rate = calculate_jaundice_rate(words, negative_words)
            word_count = len(words)
            status = ProcessingStatus.OK.value
            end_time = monotonic()
            process_time = round((end_time - start_time), 2)
    except (ClientResponseError, ClientConnectorError):
        status = ProcessingStatus.FETCH_ERROR.value
    except ArticleNotFound:
        status = ProcessingStatus.PARSING_ERROR.value
    except asyncio.TimeoutError:
        status = ProcessingStatus.TIMEOUT.value
    finally:
        result = Result(
            url,
            word_count,
            positive_rate,
            negative_rate,
            status,
            process_time,
        )
        results_container.append(result)


def get_words_from_file(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read().split("\n")


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def main(urls=None):
    morph = pymorphy2.MorphAnalyzer()
    positive_words = get_words_from_file(POSITIVE_WORDS_PATH)
    negative_words = get_words_from_file(NEGATIVE_WORDS_PATH)

    results = []

    async with aiohttp.ClientSession() as session:
        async with create_task_group() as tg:
            for url in urls:
                tg.start_soon(
                    process_article,
                    session,
                    morph,
                    url,
                    positive_words,
                    negative_words,
                    results,
                )

    for result in results:
        print(f"Address {result.address}")
        print(f"\tstatus {result.status}")
        print(f"\twords count {result.words_count}")
        print(f"\t+rate {result.pos_rate}")
        print(f"\t-rate {result.neg_rate}")
        print(f"\ttime {result.time}")


async def get_articles_results(urls=None, process_timeout=DEFAULT_PROCESS_TIME):
    morph = pymorphy2.MorphAnalyzer()
    positive_words = get_words_from_file(POSITIVE_WORDS_PATH)
    negative_words = get_words_from_file(NEGATIVE_WORDS_PATH)

    results = []

    async with aiohttp.ClientSession() as session:
        async with create_task_group() as tg:
            for url in urls:
                tg.start_soon(
                    process_article,
                    session,
                    morph,
                    url,
                    positive_words,
                    negative_words,
                    results,
                    process_timeout,
                )
    return results


if __name__ == "__main__":
    run(main, TEST_ARTICLES)
