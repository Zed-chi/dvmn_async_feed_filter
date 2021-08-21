from aiohttp import web
from main import get_articles_results

routes = web.RouteTableDef()

@routes.get('/')
async def hello(request):    
    urls_line = request.rel_url.query['urls']
    urls = urls_line.split(",")
    results = await get_articles_results(urls)
    result_dict = {
        "results":list([result_to_dict(result) for result in results])
    }
    return web.json_response(result_dict)


def result_to_dict(result):
    return {
        "address":result.address,
        "words_count":result.words_count,
        "pos_rate":result.pos_rate,
        "neg_rate":result.neg_rate,
        "status":result.status,
        "time":result.time,
    }

app = web.Application()
app.add_routes(routes)
web.run_app(app, host="127.0.0.1", port=5000)