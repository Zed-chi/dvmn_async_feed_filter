import asyncio
from dataclasses import dataclass
from enum import Enum
from time import monotonic
from typing import List

import aiohttp
from aiohttp.client_exceptions import ClientConnectorError, ClientResponseError
from anyio import create_task_group
from async_timeout import timeout

from adapters import ArticleNotFound
from adapters.inosmi_ru import sanitize
from text_tools import calculate_jaundice_rate, split_by_words


class ProcessingStatus(Enum):
    OK = "OK"
    FETCH_ERROR = "FETCH_ERROR"
    PARSING_ERROR = "PARSING_ERROR"
    TIMEOUT = "TIMEOUT"


@dataclass
class Result:
    address: str
    words_count: int
    pos_rate: float
    neg_rate: float
    status: str
    time: float = 0.0


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(
    session,
    morph,
    url,
    positive_words,
    negative_words,
    results_container,
    process_timeout,
):
    words_count = 0
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
            words_count = len(words)
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
            words_count,
            positive_rate,
            negative_rate,
            status,
            process_time,
        )
        results_container.append(result)


async def get_articles_results(
    morph, positive_words, negative_words, urls, process_timeout
):
    results: List[Result] = []

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
