"""
Metricon API ingestion — stub.

This module will replace ingest_mse.py when Metricon's API is live.
See data/api_notes/metricon.md for planned endpoints and example usage.

To activate:
  1. Obtain an API key and set METRICON_API_KEY in .env
  2. Uncomment and implement the functions below
  3. Update the cron schedule to call this script instead of ingest_mse.py
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

METRICON_API_KEY = os.environ.get("METRICON_API_KEY", "")


def main():
    if METRICON_API_KEY in ("", "placeholder"):
        print("Metricon API key not configured — API not yet available.")
        print("See data/api_notes/metricon.md for setup instructions.")
        sys.exit(1)

    # TODO: implement when Metricon API is live
    # import requests, websockets
    # REST: GET /stocks, GET /ohlcv/{ticker}
    # WebSocket: /live (5s tick stream → Redis → quotes table)
    raise NotImplementedError("Metricon API integration not yet implemented")


if __name__ == "__main__":
    main()
