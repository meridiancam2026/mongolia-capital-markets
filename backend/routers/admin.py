import os

import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter()

_GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
_GITHUB_REPO = "meridiancam2026/mongolia-capital-markets"
_ALLOWED = {"ingest_mse", "ingest_cbonds"}


@router.post("/trigger/{workflow}")
async def trigger_workflow(workflow: str):
    if workflow not in _ALLOWED:
        raise HTTPException(status_code=400, detail=f"Unknown workflow: {workflow!r}")
    if not _GITHUB_TOKEN:
        raise HTTPException(status_code=503, detail="GITHUB_TOKEN not configured on server")

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"https://api.github.com/repos/{_GITHUB_REPO}/actions/workflows/{workflow}.yml/dispatches",
            json={"ref": "main"},
            headers={
                "Authorization": f"Bearer {_GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

    if resp.status_code == 204:
        return {"status": "triggered"}
    raise HTTPException(status_code=resp.status_code, detail=resp.text)
