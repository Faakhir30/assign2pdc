import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import threading
import time
from collections import deque


class ParallelCrawler:
    def __init__(self, seed_url, max_pages=50, num_workers=8):
        self.seed_url = seed_url
        self.max_pages = max_pages
        self.num_workers = num_workers
        self.visited = set()
        self.results = []
        self.lock = threading.Lock()
        self.url_queue = Queue()
        self.url_queue.put(seed_url)
        self.pages_crawled = 0
        self.start_time = None
        self.worker_activity = [0] * num_workers
        self.active_workers = 0
        self.worker_lock = threading.Lock()

    def _is_valid_url(self, url):
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https")

    def worker(self, worker_id):
        with self.worker_lock:
            self.active_workers += 1

        try:
            while True:
                # Check if we've reached max pages
                with self.lock:
                    if self.pages_crawled >= self.max_pages:
                        break

                try:
                    # Get URL with a shorter timeout
                    url = self.url_queue.get(timeout=0.1)
                except:
                    # If queue is empty and no other workers are active, we're done
                    with self.worker_lock:
                        if self.active_workers <= 1:
                            break
                    continue

                with self.lock:
                    if url in self.visited:
                        self.url_queue.task_done()
                        continue
                    self.visited.add(url)
                    self.pages_crawled += 1
                    self.worker_activity[worker_id] += 1

                try:
                    resp = requests.get(url, timeout=5)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "html.parser")
                    title = soup.title.string.strip() if soup.title else ""

                    with self.lock:
                        self.results.append({"url": url, "title": title})

                    # Extract and add new URLs
                    new_urls = []
                    for link in soup.find_all("a", href=True):
                        abs_url = urljoin(url, link["href"])
                        if self._is_valid_url(abs_url):
                            new_urls.append(abs_url)

                    # Add new URLs to queue
                    with self.lock:
                        for new_url in new_urls:
                            if new_url not in self.visited:
                                self.url_queue.put(new_url)

                except Exception as e:
                    print(f"Error fetching {url}: {e}")
                finally:
                    self.url_queue.task_done()

        finally:
            with self.worker_lock:
                self.active_workers -= 1

    def crawl(self):
        self.start_time = time.time()
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Submit initial worker tasks
            futures = [executor.submit(self.worker, i) for i in range(self.num_workers)]
            # Wait for all tasks to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Worker error: {e}")
        self.end_time = time.time()

    def get_metrics(self):
        duration = self.end_time - self.start_time
        pages_per_sec = self.pages_crawled / duration if duration > 0 else 0
        utilization = [a / self.pages_crawled for a in self.worker_activity]
        return {
            "pages_crawled": self.pages_crawled,
            "duration": duration,
            "pages_per_sec": pages_per_sec,
            "worker_utilization": utilization,
        }


if __name__ == "__main__":
    seed = "https://example.com/"
    crawler = ParallelCrawler(seed_url=seed, max_pages=20, num_workers=4)
    crawler.crawl()
    metrics = crawler.get_metrics()
    print(
        f"Crawled {metrics['pages_crawled']} pages in {metrics['duration']:.2f} seconds."
    )
    print(f"Pages per second: {metrics['pages_per_sec']:.2f}")
    print(f"Worker utilization: {metrics['worker_utilization']}")
    for r in crawler.results:
        print(r)
