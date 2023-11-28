'''
This crawler is for ctext.org, which is a website that hosts Chinese classics.
'''

from dataclasses import dataclass, asdict
import requests
import time
import re
import json
import argparse
from urllib.parse import urljoin
from typing import Callable, List


from bs4 import BeautifulSoup

CTEXT_ROOT_URL = 'https://ctext.org'


@dataclass
class Chapter:
    title: str
    texts: List[str]
    loc: int


@dataclass
class Book:
    name: str
    chapters: List[Chapter]


class BookCrawler:
    @staticmethod
    def fetch_html(url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'
        }
        try:
            print(f"Opening {url}")
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            time.sleep(1)
            return response.text
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def __init__(self, url, title, chapter_href_filter: Callable[[str], bool], max_chapters=None, chapter_index_start=0):
        self.root_url = url
        self.title = title
        self.chapter_href_filter = chapter_href_filter
        self.max_chapters = max_chapters
        self.chapter_index_start = chapter_index_start

    def crawl_book(self) -> Book:
        root_html = BookCrawler.fetch_html(self.root_url)
        if root_html is None:
            return "Failed to fetch root page."

        soup = BeautifulSoup(root_html, 'html.parser')
        chapters: List[Chapter] = []

        chapter_idx = self.chapter_index_start
        for link in soup.find('div', id="content3").find_all('a'):
            href = link.get('href')
            # Modify this if needed for better filtering
            if href and self.chapter_href_filter(href):
                chapter_url = urljoin(CTEXT_ROOT_URL, href)
                link_text = link.text.strip()
                print(
                    f"[Crawling chapter {chapter_idx}]: {link_text}, {chapter_url}")
                chapter = self.crawl_chapter(
                    chapter_index=chapter_idx,
                    url=chapter_url, title=link_text)
                chapters.append(chapter)
                chapter_idx += 1
            else:
                print(f"Skipping {link.text.strip()},  {href}")

            if self.max_chapters and chapter_idx >= self.max_chapters:
                break
        self.book = Book(name=self.title, chapters=chapters)
        return self.book

    def crawl_chapter(self, chapter_index, url, title="") -> Chapter:
        chapter_html = BookCrawler.fetch_html(url)
        assert chapter_html is not None, f"Failed to fetch chapter page from {url}"

        s = BeautifulSoup(chapter_html, 'html.parser')
        if not title:
            title = s.find('h2').text.strip()
        sections = [t.text.strip() for t in s.select("td[class='ctext']")]
        # import pdb
        # pdb.set_trace()

        return Chapter(title=title, texts='\n'.join(sections), loc=chapter_index)

    def export_to_json(self, json_path=""):
        if not json_path:
            json_path = f"{self.title}.json"

        d = [asdict(c) for c in self.book.chapters]
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(d, f)


if __name__ == "__main__":
    arg = argparse.ArgumentParser(description='''Crawl a book from ctext.org. Example:
        python crawl.py --url="https://ctext.org/huangdi-neijing/ling-shu-jing/zhs" 
          --title="黄帝内经 - 灵枢经" 
          --chapter-filter-regex="huangdi-neijing/.+/zhs"
    ''')
    arg.add_argument('--url', required=True,
                     help="The root url of the book, for example, https://ctext.org/huangdi-neijing/suwen/zhs")
    arg.add_argument(
        '--title', required=True, help="The title of the book, also the name of the output json file")
    arg.add_argument('--chapter-filter-regex', type=str, required=True,
                     help="A regex string to filter out chapter urls, for example, 'huangdi-neijing/.+/zhs'")
    arg.add_argument('--max-chapters', type=int, default=None,
                     help="The max number of chapters to crawl, useful for testing")
    arg.add_argument('--chapter-index-start', type=int, default=0,
                     help="The index of the first chapter, useful for concatenating multiple crawls")
    config = arg.parse_args()

    crawler = BookCrawler(config.url,
                          title=config.title,
                          chapter_href_filter=lambda x: re.match(
                              config.chapter_filter_regex, x) is not None,
                          max_chapters=config.max_chapters,
                          chapter_index_start=config.chapter_index_start)

    crawler.crawl_book()
    crawler.export_to_json()
