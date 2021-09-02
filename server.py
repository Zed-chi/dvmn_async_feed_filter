from typing import List

import pymorphy2
from aiohttp import web
from article_analyzer import Result, get_articles_results
from config import DEFAULT_TIMEOUT, NEGATIVE_WORDS_PATH, POSITIVE_WORDS_PATH
from text_tools import load_words_from_file

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
            {"error": "too many urls in request, should be 10 or less"},
        )

    results: List[Result] = await get_articles_results(
        MORPH, POSITIVE_WORDS, NEGATIVE_WORDS, urls, DEFAULT_TIMEOUT,
    )
    result_dict = {
        "results": [result.__dict__ for result in results],
    }
    return web.json_response(result_dict)


app = web.Application()
app.add_routes(routes)
web.run_app(app, host="127.0.0.1", port=9000)
