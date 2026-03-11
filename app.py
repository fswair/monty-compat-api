from cachetools import cached, TTLCache
from typing import Any

from monty_compat import get_capabilities, MontyCapabilities as Capabilities
from fastapi import Depends, FastAPI, Response
from asgi_request_duration.middleware import RequestDurationMiddleware, TimeGranularity

app = FastAPI()

app.add_middleware(
    RequestDurationMiddleware,
    header_name="x-request-duration-ms",
    time_granularity=TimeGranularity.MILLISECONDS,
    precision=0,
)


@cached(cache=TTLCache(maxsize=256, ttl=12 * 60 * 60))
def get_caps(as_dict: bool = False):
    caps = get_capabilities(cache="off")
    if as_dict:
        return caps.to_dict()
    return caps


@app.get("/")
async def home():
    return {
        "endpoints": {
            "docs": "Swagger UI API Docs"
            "nodes": "Implemented nodes by Monty.",
            "check": "Check any code to see whether code is monty compatible.",
        },
        "cache_ttl": 12 * 60 * 60,
    }


@app.get("/nodes")
async def fetch_nodes() -> dict[str, Any]:
    """
    Fetch detailed information for Python nodes supported by Monty runtime.
    """
    return get_caps(as_dict=True)


@app.get("/check")
async def check_compat(
    code: str,
    response: Response,
    caps: Capabilities = Depends(get_caps, scope="function"),
) -> dict[str, int | list[str]]:
    ok, reasons = caps.check_code(code)
    if ok:
        response.status_code = 200
    else:
        response.status_code = 505

    return {"status_code": response.status_code, "reasons": reasons}
