import asyncio
import aiohttp
import argparse
import time
import ssl
import certifi
from concurrent.futures import ThreadPoolExecutor

# Create a custom SSL context using certifi's certificates
ssl_context = ssl.create_default_context(cafile=certifi.where())

class HerokuLoadTester:
    def __init__(self, target_url, num_workers=10, duration=60):
        self.target_url = target_url
        self.num_workers = num_workers
        self.duration = duration
        self.results = []
        self.start_time = None

    async def make_request(self, session):
        try:
            start = time.time()
            async with session.post(self.target_url, json={"n": 30_000}, ssl=ssl_context) as response:
                await response.text()
                end = time.time()
                return {
                    'status': response.status,
                    'latency': end - start
                }
        except Exception as e:
            print(f"Error making request: {e}")
            return {
                'status': 'error',
                'latency': 0,
                'error': str(e)
            }

    async def worker(self, worker_id, session):
        while time.time() - self.start_time < self.duration:
            result = await self.make_request(session)
            result['worker_id'] = worker_id
            result['timestamp'] = time.time()
            self.results.append(result)
            # Small delay to prevent overwhelming the system
            # await asyncio.sleep(0.1)

    async def run_load_test(self):
        self.start_time = time.time()
        async with aiohttp.ClientSession() as session:
            workers = [self.worker(i, session) for i in range(self.num_workers)]
            await asyncio.gather(*workers)

    def analyze_results(self):
        successful_requests = [r for r in self.results if r['status'] == 200]
        failed_requests = [r for r in self.results if r['status'] != 200]

        if not self.results:
            return "No results collected"

        total_requests = len(self.results)
        avg_latency = sum(r['latency'] for r in successful_requests) / len(successful_requests) if successful_requests else 0

        return {
            'total_requests': total_requests,
            'successful_requests': len(successful_requests),
            'failed_requests': len(failed_requests),
            'failed_request_statuses': [r['status'] for r in failed_requests],
            'requests_per_second': total_requests / self.duration,
            'average_latency': avg_latency,
            'error_rate': len(failed_requests) / total_requests if total_requests > 0 else 0
        }

async def main():
    parser = argparse.ArgumentParser(description='Load test a Heroku dyno')
    parser.add_argument('url', help='Target URL to test')
    parser.add_argument('--workers', type=int, default=10, help='Number of concurrent workers')
    parser.add_argument('--duration', type=int, default=60, help='Test duration in seconds')
    args = parser.parse_args()

    tester = HerokuLoadTester(args.url, args.workers, args.duration)
    print(f"Starting load test against {args.url}")
    print(f"Workers: {args.workers}, Duration: {args.duration}s")

    await tester.run_load_test()
    results = tester.analyze_results()

    print("\nTest Results:")
    print(f"Total Requests: {results['total_requests']}")
    print(f"Requests/second: {results['requests_per_second']:.2f}")
    print(f"Average Latency: {results['average_latency']:.3f}s")
    print(f"Error Rate: {results['error_rate']*100:.2f}%")
    print(f"Failed request statuses: {results['failed_request_statuses']}")

if __name__ == "__main__":
    asyncio.run(main())
