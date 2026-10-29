"""Smoke-test a deployed Personal AI Assistant without submitting user data."""
import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def validate_base_url(value: str) -> str:
    parsed = urlparse(value.rstrip("/"))
    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Base URL must be an absolute HTTP(S) origin.")
    if parsed.username or parsed.password or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("Pass only the application origin; do not include credentials, paths, queries, or fragments.")
    if parsed.scheme != "https" and parsed.hostname not in local_hosts:
        raise ValueError("Remote smoke tests require HTTPS.")
    return value.rstrip("/")


def fetch(base_url: str, path: str):
    request = Request(base_url + path, headers={"Accept": "application/json,text/html,*/*"})
    try:
        with urlopen(request, timeout=10) as response:  # nosec B310 - base URL is allowlisted above
            body = response.read(1_000_000)
            return response.status, dict(response.headers), body
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Smoke check failed for {path}: {type(exc).__name__}") from exc


def run_checks(base_url: str, require_ai=False, require_postgres=False, require_redis=False):
    base_url = validate_base_url(base_url)
    status, _, body = fetch(base_url, "/health")
    if status != 200:
        raise RuntimeError(f"Health check returned HTTP {status}.")
    health = json.loads(body.decode("utf-8"))
    if health.get("status") != "ok":
        raise RuntimeError("Health endpoint did not report status=ok.")
    if require_ai and not health.get("ai_configured"):
        raise RuntimeError("AI provider is not configured.")
    if require_postgres and health.get("database") != "postgresql":
        raise RuntimeError("PostgreSQL was required but the service reports a different backend.")
    if require_redis and health.get("rate_limit_store") != "redis":
        raise RuntimeError("Redis-backed rate limiting was required but is not active.")

    status, headers, html = fetch(base_url, "/")
    if status != 200 or b"Personal AI Assistant" not in html:
        raise RuntimeError("The browser workspace did not load correctly.")
    csp = headers.get("Content-Security-Policy", "")
    if "script-src 'self'" not in csp or "object-src 'none'" not in csp:
        raise RuntimeError("The expected restrictive Content Security Policy is missing.")

    for asset in ("/assets/app.js", "/assets/styles.css"):
        asset_status, _, _ = fetch(base_url, asset)
        if asset_status != 200:
            raise RuntimeError(f"Static asset check failed for {asset}.")
    return health


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Application origin, e.g. https://assistant.example.com")
    parser.add_argument("--require-ai", action="store_true", help="Fail if no model provider is configured")
    parser.add_argument("--require-postgres", action="store_true", help="Fail unless PostgreSQL is active")
    parser.add_argument("--require-redis", action="store_true", help="Fail unless Redis-backed rate limiting is active")
    args = parser.parse_args()
    try:
        health = run_checks(args.url, args.require_ai, args.require_postgres, args.require_redis)
    except (ValueError, RuntimeError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc
    print(
        "Smoke checks passed: "
        f"database={health['database']}, "
        f"rate_limit_store={health['rate_limit_store']}, "
        f"ai_configured={health['ai_configured']}"
    )


if __name__ == "__main__":
    main()
