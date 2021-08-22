from time import monotonic

import pymorphy2
from anyio import run

from article_analyzer import get_articles_results, load_words_from_file
from config import (DEFAULT_TIMEOUT, NEGATIVE_WORDS_PATH, POSITIVE_WORDS_PATH,
                    TEST_ARTICLES)


async def main(urls=None):
    start_time = monotonic()
    morph = pymorphy2.MorphAnalyzer()
    positive_words = load_words_from_file(POSITIVE_WORDS_PATH)
    negative_words = load_words_from_file(NEGATIVE_WORDS_PATH)

    results = await get_articles_results(
        morph, positive_words, negative_words, TEST_ARTICLES, DEFAULT_TIMEOUT
    )

    end_time = monotonic()
    for result in results:
        print(f"Address {result.address}")
        print(f"\tstatus {result.status}")
        print(f"\twords count {result.words_count}")
        print(f"\t+rate {result.pos_rate}")
        print(f"\t-rate {result.neg_rate}")
        print(f"\ttime {result.time}")
    print(f"{round(end_time-start_time, 2)} sec")


if __name__ == "__main__":
    run(main, TEST_ARTICLES)
