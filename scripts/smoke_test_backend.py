from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a backend smoke test against the ad analysis API.")
    parser.add_argument("--api-base-url", default="http://127.0.0.1:8000", help="Base URL for the backend API.")
    parser.add_argument("--api-prefix", default="/v1", help="Configured API prefix.")
    parser.add_argument("--video-path", required=True, help="Path to a short test video.")
    parser.add_argument("--title", default="Smoke Test Ad")
    parser.add_argument("--brand", default="Smoke Test Brand")
    parser.add_argument("--campaign", default="smoke-test")
    parser.add_argument("--notes", default="Automated smoke test submission.")
    parser.add_argument("--dev-user-id", default="smoke-test-user")
    parser.add_argument("--auth-token", default=None)
    parser.add_argument("--runner-base-url", default=None, help="Optional TRIBE runner base URL to health check.")
    parser.add_argument("--poll-interval", type=float, default=5.0)
    parser.add_argument("--timeout-sec", type=float, default=1800.0)
    return parser.parse_args()


def _headers(args: argparse.Namespace) -> dict[str, str]:
    headers: dict[str, str] = {}
    if args.auth_token:
        headers["Authorization"] = f"Bearer {args.auth_token}"
    else:
        headers["X-Dev-User-Id"] = args.dev_user_id
    return headers


def _expect_ok(response: httpx.Response, context: str) -> dict | list:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"{context} failed: {exc.response.status_code} {exc.response.text}") from exc
    if not response.content:
        return {}
    return response.json()


def main() -> int:
    args = parse_args()
    video_path = Path(args.video_path).expanduser().resolve()
    if not video_path.exists():
        raise SystemExit(f"Video file does not exist: {video_path}")

    base_url = args.api_base_url.rstrip("/")
    api_prefix = args.api_prefix.rstrip("/")
    headers = _headers(args)

    with httpx.Client(timeout=60.0) as client:
        api_health = _expect_ok(client.get(f"{base_url}/health"), "API health")
        runner_health = None
        if args.runner_base_url:
            runner_health = _expect_ok(client.get(f"{args.runner_base_url.rstrip('/')}/health"), "Runner health")

        with video_path.open("rb") as handle:
            response = client.post(
                f"{base_url}{api_prefix}/jobs",
                headers=headers,
                data={
                    "title": args.title,
                    "brand": args.brand,
                    "campaign": args.campaign,
                    "notes": args.notes,
                },
                files={"file": (video_path.name, handle, "video/mp4")},
            )
        create_payload = _expect_ok(response, "Job creation")
        job_id = str(create_payload["job_id"])

        deadline = time.time() + args.timeout_sec
        job_payload: dict[str, object] | None = None
        while time.time() < deadline:
            job_payload = _expect_ok(
                client.get(f"{base_url}{api_prefix}/jobs/{job_id}", headers=headers),
                "Job polling",
            )
            status = str(job_payload["status"])
            if status == "completed":
                break
            if status == "failed":
                raise RuntimeError(f"Job failed: {job_payload.get('error_message')}")
            time.sleep(args.poll_interval)
        else:
            raise RuntimeError(f"Timed out waiting for job {job_id} to complete.")

        report_payload = _expect_ok(
            client.get(f"{base_url}{api_prefix}/jobs/{job_id}/report", headers=headers),
            "Report fetch",
        )
        asset_response = client.get(f"{base_url}{api_prefix}/jobs/{job_id}/assets/customer_report", headers=headers)
        asset_response.raise_for_status()

    output = {
        "api_health": api_health,
        "runner_health": runner_health,
        "job_id": job_id,
        "job_status": job_payload["status"] if job_payload else "unknown",
        "job_progress": job_payload["progress"] if job_payload else None,
        "report_summary": report_payload.get("summary"),
        "similar_ads": report_payload.get("similar_ads"),
        "customer_report_bytes": len(asset_response.content),
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}", file=sys.stderr)
        raise
