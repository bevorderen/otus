import argparse
import asyncio
import logging
import os
import sys
import uuid
from asyncio import Task
from typing import Union, Tuple

import aiofiles
import aiohttp
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup

FETCH_TIMEOUT = 5
MAIN_PAGE_URL = "https://news.ycombinator.com"
COMMENTS_TEMPLATE = "https://news.ycombinator.com/item?id={id}"


async def fetch_page(url: str, need_bytes: bool) -> Union[str, bytes]:
    try:
        async with ClientSession(
                timeout=ClientTimeout(FETCH_TIMEOUT),
                connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.get(url=url) as response:
                if need_bytes:
                    return await response.read()
                else:
                    return await response.text()

    except aiohttp.ClientError as error:
        logging.debug(f"Catch error when fetch page {url=}. {error.__str__()}")
    except asyncio.TimeoutError as error:
        logging.debug(f"Can't download page {url=}. {error.__str__()}")


async def save_page(save_dir: str, filename: str, content: Union[str, bytes]) -> None:
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    try:
        async with aiofiles.open(save_dir + "/" + filename + ".html", mode="wb") as fw:
            await fw.write(content)
            await fw.close()
    except OSError as error:
        logging.error(f"Error when saving file {filename=}. {error.__str__()}")


async def fetch_and_save(uid: str, url: str, save_dir: str) -> None:
    content = await fetch_page(url=url, need_bytes=True)
    if not content:
        return
    await save_page(filename=uid, save_dir=save_dir, content=content)


def parse_top_news(html, fetch_limit: int) -> Tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    for tr in soup.find_all(name="tr", class_="athing", limit=fetch_limit):
        uid = tr.attrs.get("id")
        if not uid:
            continue
        else:
            a = tr.select_one("a.titlelink")
            if not a:
                continue
            url = a.attrs.get("href")
            if not url:
                continue
            yield uid, url


def parse_comments(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for span in soup.find_all(name="span", class_="commtext"):
        for a in span.find_all("a"):
            url = a.attrs.get("href")
            if not url:
                continue
            yield url


class YCrawler:
    def __init__(self, save_dir: str, top_posts_limit: int = 30, download_interval: int = 60):
        self.saved_posts = set()
        self.need_save = set()
        self.save_dir = save_dir
        self.top_posts_limit = top_posts_limit
        self.download_interval = download_interval

    async def monitor_page(self, uid: str, url: str, save_dir: str) -> Tuple[str, str]:
        logging.debug(f"Download page {url=}")
        await fetch_and_save(uid=uid, url=url, save_dir=save_dir)

        logging.debug(f"Save comments for {url=}")
        comment_page = await fetch_page(url=COMMENTS_TEMPLATE.format(id=uid), need_bytes=False)
        if comment_page:
            comment_urls = parse_comments(comment_page)
            if comment_urls:
                comment_tasks = []
                for comment_url in comment_urls:
                    comment_save_path = os.path.join(save_dir, "links")
                    comment_uid = uuid.uuid4().hex
                    task = asyncio.create_task(
                        fetch_and_save(
                            uid=comment_uid,
                            url=comment_url,
                            save_dir=comment_save_path
                        )
                    )
                    comment_tasks.append(task)
                await asyncio.gather(*comment_tasks, return_exceptions=False)
        return "success", uid

    async def monitor_main_page(self):
        content = await fetch_page(url=MAIN_PAGE_URL, need_bytes=False)
        if not content:
            logging.debug(f"Can't received main page")
            return

        top_news = parse_top_news(html=content, fetch_limit=self.top_posts_limit)
        tasks = []
        for uid, url in top_news:
            if uid in self.saved_posts or uid in self.need_save:
                continue
            save_dir = os.path.join(self.save_dir, uid)
            task = asyncio.create_task(self.monitor_page(uid=uid, url=url, save_dir=save_dir))
            self.need_save.add(uid)
            tasks.append(task)

        if not tasks:
            return

        return await asyncio.gather(*tasks, return_exceptions=False)

    def mark_saved(self, task: Task) -> None:
        results = task.result()
        if not results:
            return

        for result in results:
            if isinstance(result, tuple) and result[0] == "success":
                self.saved_posts.add(result[1])
                self.need_save.remove(result[1])

    async def run(self):
        while True:
            task = asyncio.create_task(self.monitor_main_page())
            task.add_done_callback(self.mark_saved)
            await asyncio.sleep(self.download_interval)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--download_interval", default=10, type=int)
    arg_parser.add_argument("--save_dir", default="results", type=str)
    arg_parser.add_argument("--top_posts_limit", default=30, type=int)
    arg_parser.add_argument("--dry_run", default=True, type=bool)
    arg_parser.add_argument('--log', default=None, type=str)
    args = arg_parser.parse_args()
    logging.basicConfig(filename=args.log, level=logging.INFO if not args.dry_run else logging.DEBUG,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    try:
        ycrawler = YCrawler(
            download_interval=args.download_interval,
            save_dir=args.save_dir,
            top_posts_limit=args.top_posts_limit,
        )
        asyncio.run(ycrawler.run())
    except KeyboardInterrupt:
        sys.exit(1)
