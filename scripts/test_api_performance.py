
import time
import json
import statistics
import urllib.request
import urllib.error
import threading
import concurrent.futures

BASE_URL = "http://127.0.0.1:8000"
TOTAL_REQUESTS = 50

def send_request(index):
    body = json.dumps({
        "command": "what is the weather in Delhi"
    }).encode("utf-8")

    request = urllib.request.Request(
        f"{BASE_URL}/parse",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    start = time.perf_counter()

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            response.read()
            elapsed = (time.perf_counter() - start) * 1000
            return elapsed, response.status
    except Exception as error:
        elapsed = (time.perf_counter() - start) * 1000
        print(f"Request {index} failed: {error}")
        return elapsed, 0


if __name__ == "__main__":
    print(f"Running {TOTAL_REQUESTS} sequential requests...")

    results = [
        send_request(i + 1)
        for i in range(TOTAL_REQUESTS)
    ]

    successful = [r[0] for r in results if r[1] == 200]
    failed = TOTAL_REQUESTS - len(successful)

    if successful:
        print("\n--- API Performance Results ---")
        print("Total requests:", TOTAL_REQUESTS)
        print("Successful:", len(successful))
        print("Failed:", failed)
        print("Average latency (ms):", round(statistics.mean(successful), 2))
        print("P50 latency (ms):", round(statistics.median(successful), 2))
        print(
            "P95 latency (ms):",
            round(sorted(successful)[int(0.95 * (len(successful) - 1))], 2)
        )
        print("Total time (seconds):", round(sum(r[0] for r in results) / 1000, 2))
    else:
        print("All requests failed.")
