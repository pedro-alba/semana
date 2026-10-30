"""Load test (SC-007). Not collected by pytest.

uv run python tests/load.py --url http://127.0.0.1:8000 --users 1000 --minutes 5
"""
import argparse
import asyncio
import statistics
import sys
import time
import uuid

import httpx

times: dict[str, list[float]] = {"GET /api/week": [], "POST /api/ops": []}


async def measure(route, call):
    start = time.perf_counter()
    r = await call
    times[route].append(time.perf_counter() - start)
    r.raise_for_status()
    return r


async def user(url, n, end):
    async with httpx.AsyncClient(base_url=url, timeout=30) as c:
        r = await c.post("/api/account", json={
            "email": f"load-{uuid.uuid4().hex[:12]}-{n}@example.com",
            "password": "load-password", "timezone": "America/Sao_Paulo"})
        r.raise_for_status()
        account_id = r.json()["account"]["id"]
        start = (await c.get("/api/start")).json()
        project, monday = start["projects"][0]["id"], start["current_week"]
        task = str(uuid.uuid4())
        await c.post("/api/ops", json={"account_id": account_id, "ops": [
            {"op": "task.create", "id": task, "project_id": project, "week": monday}]})
        rev = 0
        while time.monotonic() < end:
            await measure("GET /api/week",
                          c.get("/api/week", params={"project": project, "week": monday}))
            r = await measure("POST /api/ops", c.post("/api/ops", json={
                "account_id": account_id,
                "ops": [{"op": "task.title", "id": task, "value": f"title {rev}",
                         "base_rev": rev}]}))
            rev = r.json()["results"][0].get("rev", rev)
            await asyncio.sleep(3)


def p95(xs):
    return statistics.quantiles(xs, n=20)[-1] if len(xs) > 1 else (xs[0] if xs else 0)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--users", type=int, default=100)
    ap.add_argument("--minutes", type=float, default=1)
    a = ap.parse_args()
    end = time.monotonic() + a.minutes * 60
    await asyncio.gather(*(user(a.url, n, end) for n in range(a.users)))
    limits = {"GET /api/week": 0.5, "POST /api/ops": 1.0}
    failed = False
    for route, xs in times.items():
        v = p95(xs)
        print(f"{route}: {len(xs)} calls, p95 {v * 1000:.0f} ms (limit {limits[route] * 1000:.0f})")
        failed |= v > limits[route]
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    asyncio.run(main())
