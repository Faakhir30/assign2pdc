import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time


class SequentialCrawler:
    def __init__(self, seed_url, max_pages=50):
        self.seed_url = seed_url
        self.max_pages = max_pages
        self.visited = set()
        self.results = []

    def crawl(self):
        queue = deque([self.seed_url])
        while queue and len(self.visited) < self.max_pages:
            url = queue.popleft()
            if url in self.visited:
                continue
            try:
                resp = requests.get(url, timeout=5)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                title = soup.title.string.strip() if soup.title else ""
                self.results.append({"url": url, "title": title})
                self.visited.add(url)
                for link in soup.find_all("a", href=True):
                    abs_url = urljoin(url, link["href"])
                    if self._is_valid_url(abs_url) and abs_url not in self.visited:
                        queue.append(abs_url)
            except Exception as e:
                print(f"Error fetching {url}: {e}")

    def _is_valid_url(self, url):
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https")


if __name__ == "__main__":
    seed = "https://example.com/"
    crawler = SequentialCrawler(seed_url=seed, max_pages=20)
    start = time.time()
    crawler.crawl()
    end = time.time()
    print(f"Crawled {len(crawler.results)} pages in {end-start:.2f} seconds.")
    for r in crawler.results:
        print(r)
