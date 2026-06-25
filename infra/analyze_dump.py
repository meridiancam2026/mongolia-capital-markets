from bs4 import BeautifulSoup

html = open(
    "/mnt/c/Users/CameronThomas/OneDrive - Meridian Universal/Documents/02_Agent Projects/Local Capital Markets/mongolia-capital-markets/logs/mse_page_dump.html",
    encoding="utf-8"
).read()

soup = BeautifulSoup(html, "html.parser")
table = soup.find("table")
if not table:
    print("No table found")
    exit()

# Print headers
print("=== HEADERS ===")
for th in table.find_all("th"):
    print(f"  [{th.get('colspan','1')}col, {th.get('rowspan','1')}row] {th.get_text(strip=True)}")

# Print first 3 data rows
print("\n=== FIRST 3 DATA ROWS (cell text by index) ===")
tbody = table.find("tbody")
if not tbody:
    print("No tbody found")
    exit()

rows = tbody.find_all("tr")
print(f"Total tbody rows: {len(rows)}")
for i, row in enumerate(rows[:3]):
    cells = [td.get_text(strip=True) for td in row.find_all("td")]
    print(f"\nRow {i}: {len(cells)} cells")
    for j, cell in enumerate(cells):
        print(f"  [{j}] {cell!r}")
