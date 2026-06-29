"""
Seed the securities table with company names, sectors, and descriptions.

Run after migrations, before or after quote ingestion. Safe to re-run — uses
ON CONFLICT DO UPDATE, so existing rows are updated rather than duplicated.

Usage:
    python scripts/seed_securities.py
    python scripts/seed_securities.py --dry-run
"""
import argparse
import logging
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# fmt: off
SECURITIES = [
    # ticker  name                                          sector               description
    ("APU",   "APU JSC",                                   "Consumer Staples",  "Mongolia's largest brewery and distillery group. Produces Chinggis Beer, APU vodka, and Bolor mineral water. One of the most actively traded stocks on the MSE."),
    ("TDB",   "Trade and Development Bank of Mongolia",    "Banking",           "Mongolia's largest commercial bank by total assets. Provides corporate banking, trade finance, and retail services. Majority state-owned."),
    ("KHAN",  "Khan Bank",                                 "Banking",           "Mongolia's largest bank by branch network and retail customer base, with over 500 branches. Formerly the Agricultural Bank of Mongolia."),
    ("XAC",   "XacBank",                                   "Banking",           "Commercial bank specializing in SME lending, microfinance, and green finance. One of Mongolia's oldest private banks."),
    ("SUU",   "Suu JSC",                                   "Consumer Staples",  "Mongolia's leading dairy and food products manufacturer. Produces milk, yogurt, butter, and juice under the Suu brand."),
    ("BDS",   "BDSec JSC",                                 "Financial Services","One of Mongolia's largest stockbroking and investment banking firms. Provides securities trading, research, and asset management."),
    ("BDL",   "Bogd Development LLC",                      "Financial Services","Investment and financial services company affiliated with the BDSec group."),
    ("TTL",   "Tushig Trans LLC",                          "Transportation",    "Transportation and logistics company operating in Mongolia."),
    ("MFC",   "MFC Holding JSC",                           "Financial Services","Diversified financial holding company providing lending, leasing, and investment services."),
    ("MNDL",  "Mandal Insurance",                          "Insurance",         "One of Mongolia's largest insurance companies, offering property, vehicle, and life insurance products."),
    ("INV",   "Invescore JSC",                             "Financial Services","Investment and brokerage firm listed on the MSE."),
    ("GOV",   "Gobi JSC",                                  "Consumer Goods",    "Mongolia's premier cashmere producer and exporter. Produces high-end knitwear and raw cashmere for global luxury brands."),
    ("SBM",   "State Bank of Mongolia",                    "Banking",           "State-owned commercial bank providing retail and corporate banking services throughout Mongolia."),
    ("ADB",   "Agricultural Development Bank of Mongolia", "Banking",           "Policy bank focused on rural finance, agricultural lending, and supporting herder households across Mongolia."),
    ("MMX",   "Mongolian Mining Corporation",              "Mining",            "Mongolia's largest coking coal producer and exporter. Operates the Ukhaa Khudag mine in the South Gobi. Also listed on the Hong Kong Stock Exchange."),
    ("AARD",  "Ard Financial Group",                       "Financial Services","Diversified financial group offering banking, insurance, brokerage, and fintech services. Operates the Ard app platform."),
    ("MNP",   "Monpol JSC",                                "Industrials",       "Mongolian industrial and manufacturing company listed on the MSE."),
    ("MLG",   "Mongol Gazar JSC",                          "Real Estate",       "Real estate development and property investment company operating in Ulaanbaatar."),
    ("NEH",   "Newcom JSC",                                "Technology",        "Technology and telecommunications holding company. Operates MobiFinance and other digital services in Mongolia."),
    ("MBW",   "Mongolyn Alt MAK JSC",                      "Mining",            "Coal mining and energy company with operations in the South Gobi region of Mongolia."),
    ("AIC",   "Ard Insurance",                             "Insurance",         "Insurance subsidiary of Ard Financial Group, offering motor, property, and life insurance products."),
    ("GLMT",  "Golomt Bank",                               "Banking",           "One of Mongolia's leading private commercial banks, providing retail, corporate, and investment banking services."),
    ("CUMN",  "Cumana JSC",                                "Energy",            "Energy sector company operating in Mongolia."),
    ("LEND",  "Lend JSC",                                  "Financial Services","Lending and credit services company providing consumer and SME loans in Mongolia."),
    ("MSE",   "Mongolian Stock Exchange",                  "Financial Services","The primary securities exchange of Mongolia, listing over 160 companies. Also traded as a listed entity on its own exchange."),
    ("TUM",   "Tumen Shuvuut JSC",                         "Consumer Goods",    "Consumer goods and retail company listed on the MSE."),
    ("ADU",   "Adu JSC",                                   "Industrials",       "Industrial company listed on the Mongolian Stock Exchange."),
    ("BAN",   "Baganuur JSC",                              "Mining",            "Coal mining company operating the Baganuur open-cast coal mine east of Ulaanbaatar, supplying the domestic heating market."),
    ("BODI",  "Bodi International LLC",                    "Financial Services","Financial services and trading company listed on the MSE."),
    ("ERDN",  "Erdenes Mongol JSC",                        "Mining",            "State-owned strategic minerals holding company. Holds stakes in Oyu Tolgoi, Erdenes Tavan Tolgoi, and other major mineral deposits."),
    ("ETR",   "Etranzact Mongolia",                        "Technology",        "Payment technology and fintech company providing digital transaction infrastructure in Mongolia."),
    ("GAZR",  "Mongolgas JSC",                             "Energy",            "State-owned natural gas distribution company responsible for gas supply and pipeline infrastructure in Mongolia."),
    ("HBO",   "HBO JSC",                                   "Industrials",       "Industrial and manufacturing company listed on the MSE."),
    ("HRM",   "Hermes JSC",                                "Financial Services","Financial services and brokerage company operating in Mongolia."),
    ("HSR",   "Housing and Construction Bank",             "Banking",           "Specialized bank focused on mortgage lending and housing finance in Mongolia."),
    ("ITLS",  "InterteleSystems LLC",                      "Technology",        "Information technology and telecommunications services company."),
    ("JTB",   "JTB JSC",                                   "Industrials",       "Mongolian industrial company listed on the stock exchange."),
    ("MBG",   "Mongolian Bank Group",                      "Banking",           "Banking and financial services group operating in Mongolia."),
    ("MGLA",  "Mongol Gal JSC",                            "Energy",            "Energy and fuel distribution company serving the Mongolian domestic market."),
    ("QPAY",  "QPay JSC",                                  "Technology",        "Digital payments and fintech company providing QR-code and mobile payment services in Mongolia."),
    ("RMC",   "Resource Mining Corporation",               "Mining",            "Mining exploration and development company with projects in Mongolia."),
    ("SEND",  "Send Money JSC",                            "Technology",        "Money transfer and payment services company operating in Mongolia."),
    ("TAND",  "Tand JSC",                                  "Consumer Goods",    "Consumer goods and retail distribution company listed on the MSE."),
    ("TGI",   "Tavan Golomt Invest JSC",                   "Financial Services","Investment company with holdings across the Mongolian financial and resources sectors."),
    ("AMT",   "Amtech JSC",                                "Technology",        "Technology solutions and services company operating in the Mongolian market."),
    ("AOI",   "Alt Oil JSC",                               "Energy",            "Oil and petroleum products distribution and trading company in Mongolia."),
    ("AZH",   "Azh JSC",                                   "Consumer Goods",    "Consumer goods company listed on the Mongolian Stock Exchange."),
    ("ERS",   "Erdenes Resources JSC",                     "Mining",            "Natural resources and mining company with exploration assets in Mongolia."),
    ("HRD",   "Khurd JSC",                                 "Industrials",       "Mongolian industrial and manufacturing company."),
    ("MRX",   "Merex JSC",                                 "Financial Services","Financial services company listed on the Mongolian Stock Exchange."),
]
# fmt: on


def get_db_conn():
    url = os.environ.get("DATABASE_SYNC_URL", "").replace("postgresql+psycopg2://", "postgresql://", 1)
    if not url:
        raise RuntimeError("DATABASE_SYNC_URL not set in .env")
    return psycopg2.connect(url)


UPSERT_SQL = """
INSERT INTO securities (ticker, name, sector, description)
VALUES (%s, %s, %s, %s)
ON CONFLICT (ticker) DO UPDATE SET
    name        = EXCLUDED.name,
    sector      = EXCLUDED.sector,
    description = EXCLUDED.description
"""


def main():
    parser = argparse.ArgumentParser(description="Seed securities with company names and descriptions")
    parser.add_argument("--dry-run", action="store_true", help="Print rows without writing to DB")
    args = parser.parse_args()

    if args.dry_run:
        for ticker, name, sector, desc in SECURITIES:
            print(f"{ticker:8} | {name[:45]:45} | {sector}")
        log.info("Dry run — %d companies listed, none inserted", len(SECURITIES))
        return

    conn = get_db_conn()
    count = 0
    try:
        with conn:
            with conn.cursor() as cur:
                for ticker, name, sector, desc in SECURITIES:
                    cur.execute(UPSERT_SQL, (ticker, name, sector, desc))
                    count += 1
    finally:
        conn.close()

    log.info("Upserted %d securities", count)


if __name__ == "__main__":
    main()
