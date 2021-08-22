import pytest


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
