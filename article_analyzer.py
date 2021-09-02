import asyncio
from dataclasses import dataclass
from enum import Enum
from time import monotonic
from typing import List, Union

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
    words_count: int
    pos_rate: float
    neg_rate: float
    status: str
    time: float = 0.0
    address: str = "Noname article"


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(
    morph,
    positive_words,
    negative_words,
    process_timeout,
    results_container=None,
    session=None,
    url=None,
    text=None,
) -> Union[Result, List[Result]]:
    words_count = 0
    positive_rate = None
    negative_rate = None
    status = None
    process_time = 0
    try:
        async with timeout(process_timeout):
            start_time = monotonic()

            if text is None:
                html = await fetch(session, url)
                text = sanitize(html, True)

            words = await split_by_words(morph, text)
            positive_rate = await calculate_jaundice_rate(
                words, positive_words,
            )
            negative_rate = await calculate_jaundice_rate(
                words, negative_words,
            )
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
            words_count,
            positive_rate,
            negative_rate,
            status,
            process_time,
            url,
        )
        if results_container is None:
            return result
        else:
            results_container.append(result)


async def get_articles_results(
    morph, positive_words, negative_words, urls, process_timeout,
):
    results: List[Result] = []

    async with aiohttp.ClientSession() as session:
        async with create_task_group() as tg:
            for url in urls:
                tg.start_soon(
                    process_article,
                    morph,
                    positive_words,
                    negative_words,
                    process_timeout,
                    results,
                    session,
                    url,
                )
    return results
