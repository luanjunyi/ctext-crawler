'''
This crawler is for ctext.org, which is a website that hosts Chinese classics.

黄帝内经 - 素问

python crawl.py --url="https://ctext.org/huangdi-neijing/suwen/zhs" \
    --title="黄帝内经 - 素问" \
    --chapter-filter-regex="huangdi-neijing/.+/zhs" \
    --chapter-index-start=0


黄帝内经 - 灵枢

python crawl.py --url="https://ctext.org/huangdi-neijing/ling-shu-jing/zhs" \
    --title="黄帝内经 - 灵枢" \
    --chapter-filter-regex="huangdi-neijing/.+/zhs" \
    --chapter-index-start=81


史记全书(canon)
python crawl.py --url="https://ctext.org/shiji/zhs" \
    --title="史记" \
    --chapter-filter-regex="shiji/.+/zhs" \
    --book_urls "https://ctext.org/shiji/ben-ji/zhs" "https://ctext.org/shiji/biao/zhs" "https://ctext.org/shiji/shu/zhs" "https://ctext.org/shiji/shi-jia/zhs" https://ctext.org/shiji/lie-zhuan/zhs
'''

from dataclasses import dataclass, asdict
import requests
import time
import re
import json
import argparse
from urllib.parse import urljoin
from typing import Callable

from bs4 import BeautifulSoup

from postprocessing import postprocess

CTEXT_ROOT_URL = 'https://ctext.org'


@dataclass
class Chapter:
    title: str
    texts: list[str]
    loc: int


@dataclass
class Section:
    title: str
    chapter_range: tuple[int, int]  # chapter range, 0 based index, inclusive


@dataclass
class Book:
    name: str
    chapters: list[Chapter]
    sections: list[Section] = None


class BookCrawler:
    @staticmethod
    def fetch_html(url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'
        }

        print(f"Opening {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        time.sleep(1)
        return response.text

    def __init__(self, url, title, chapter_href_filter: Callable[[str], bool], max_chapters=None, chapter_index_start=0):
        self.root_url = url
        self.title = title
        self.chapter_href_filter = chapter_href_filter
        self.max_chapters = max_chapters
        self.chapter_index_start = chapter_index_start

    def crawl_canon(self, book_urls: list[str]) -> Book:
        books = []
        for book_url in book_urls:
            self.root_url = book_url
            books.append(self.crawl_book())

        canon = Book(name=self.title, chapters=[], sections=[])
        for book in books:
            base = 0 if len(
                canon.chapters) == 0 else canon.chapters[-1].loc + 1
            for chapter in book.chapters:
                chapter.loc = base + chapter.loc
            section = Section(title=book.name,
                              chapter_range=(book.chapters[0].loc, book.chapters[-1].loc))
            canon.chapters.extend(book.chapters)
            canon.sections.append(section)

        self.book = canon
        return canon

    def crawl_book(self) -> Book:
        print(f"crawling book at {self.root_url}")

        root_html = BookCrawler.fetch_html(self.root_url)
        if root_html is None:
            return "Failed to fetch root page."

        soup = BeautifulSoup(root_html, 'html.parser')
        title = soup.find('h2').text.strip()
        chapters: list[Chapter] = []

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
        self.book = Book(name=title, chapters=chapters)
        return self.book

    def crawl_chapter(self, chapter_index, url, title="") -> Chapter:
        chapter_html = BookCrawler.fetch_html(url)
        assert chapter_html is not None, f"Failed to fetch chapter page from {url}"

        s = BeautifulSoup(chapter_html, 'html.parser')
        if not title:
            title = s.find('h2').text.strip()
        sections = [postprocess(t.text)
                    for t in s.select("td[class='ctext']")]
        # import pdb
        # pdb.set_trace()

        return Chapter(title=title, texts='\n'.join(sections), loc=chapter_index)

    def export_to_json(self, json_path=""):
        book_path = f"{self.title}.json"
        ch = [asdict(c) for c in self.book.chapters]

        with open(book_path, 'w', encoding='utf-8') as f:
            json.dump(ch, f)

        if self.book.sections:
            sec = [asdict(s) for s in self.book.sections]
            section_path = f"{self.title}_sections.json"
            with open(section_path, 'w', encoding='utf-8') as f:
                json.dump(sec, f)


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
    arg.add_argument('--book_urls', nargs='*', type=str, default=None)
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
    if config.book_urls:
        crawler.crawl_canon(config.book_urls)
    else:
        crawler.crawl_book()
    crawler.export_to_json()
