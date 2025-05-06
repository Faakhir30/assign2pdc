import time
import matplotlib.pyplot as plt
import seaborn as sns
from sequential_crawler import SequentialCrawler
from parallel_crawler import ParallelCrawler

seed_url = "https://example.com/"
max_pages = 20
worker_counts = [1, 2, 4, 8]

# Sequential benchmark
print("Running sequential crawler...")
seq_crawler = SequentialCrawler(seed_url, max_pages)
start = time.time()
seq_crawler.crawl()
seq_time = time.time() - start
print(f"Sequential: {seq_time:.2f}s for {len(seq_crawler.results)} pages")

# Parallel benchmarks
par_times = []
speedups = []
utilizations = []
for n_workers in worker_counts:
    print(f"Running parallel crawler with {n_workers} workers...")
    par_crawler = ParallelCrawler(seed_url, max_pages, num_workers=n_workers)
    par_crawler.crawl()
    metrics = par_crawler.get_metrics()
    par_times.append(metrics["duration"])
    speedups.append(seq_time / metrics["duration"])
    utilizations.append(sum(metrics["worker_utilization"]) / n_workers)
    print(
        f'  Time: {metrics["duration"]:.2f}s, Speedup: {seq_time / metrics["duration"]:.2f}, Utilization: {utilizations[-1]:.2f}'
    )

# Plotting
plt.figure(figsize=(10, 5))
sns.lineplot(x=worker_counts, y=speedups, marker="o")
plt.title("Speedup vs Number of Workers")
plt.xlabel("Number of Workers")
plt.ylabel("Speedup")
plt.savefig("speedup.png")
plt.close()

plt.figure(figsize=(10, 5))
sns.lineplot(x=worker_counts, y=utilizations, marker="o")
plt.title("Average Worker Utilization")
plt.xlabel("Number of Workers")
plt.ylabel("Utilization")
plt.savefig("utilization.png")
plt.close()

print("Plots saved as speedup.png and utilization.png")
