from typing import List

import pymorphy2
import pytest
from aiohttp import web

from article_analyzer import Result, get_articles_results, load_words_from_file
from config import DEFAULT_TIMEOUT, NEGATIVE_WORDS_PATH, POSITIVE_WORDS_PATH

routes = web.RouteTableDef()
MORPH = pymorphy2.MorphAnalyzer()
POSITIVE_WORDS = load_words_from_file(POSITIVE_WORDS_PATH)
NEGATIVE_WORDS = load_words_from_file(NEGATIVE_WORDS_PATH)


@routes.get("/")
async def process_articles(request):
    urls_parameter = request.rel_url.query.get("urls", None)
    if not urls_parameter:
        return web.json_response({"error": "Empty url parameter"})

    urls = urls_parameter.split(",")
    if len(urls) > 10:
        return web.json_response(
            {"error": "too many urls in request, should be 10 or less"}
        )

    results: List[Result] = await get_articles_results(
        MORPH, POSITIVE_WORDS, NEGATIVE_WORDS, urls, DEFAULT_TIMEOUT
    )
    result_dict = {
        "results": [result.__dict__ for result in results],
    }
    return web.json_response(result_dict)


@pytest.fixture
def cli(loop, aiohttp_client):
    app = web.Application()
    app.router.add_get("/", process_articles)
    return loop.run_until_complete(aiohttp_client(app))


async def test_empty_url(cli):
    resp = await cli.get("/")
    assert resp.status == 200
    result = await resp.json()
    assert result == {"error": "Empty url parameter"}


async def test_invalid_url(cli):
    """Testing invalid url and fetch error"""
    resp = await cli.get("/?urls=https://inosmi.ru/sc6ience/20210821/250351807.html")
    assert resp.status == 200
    result = await resp.json()
    assert result["results"][0]["status"] == "FETCH_ERROR"


async def test_parse_error(cli):
    resp = await cli.get("/?urls=https://ria.ru/20210821/arenda-1746671283.html")
    assert resp.status == 200
    result = await resp.json()
    assert result["results"][0]["status"] == "PARSING_ERROR"


async def test_timing_error(cli):
    global DEFAULT_TIMEOUT
    DEFAULT_TIMEOUT = 0.3
    resp = await cli.get("/?urls=https://inosmi.ru/science/20210821/250351807.html")
    assert resp.status == 200
    result = await resp.json()
    assert result["results"][0]["status"] == "TIMEOUT"


app = web.Application()
app.add_routes(routes)
web.run_app(app, host="127.0.0.1", port=9000)
