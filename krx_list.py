import csv
import os

_CSV_PATH = os.path.join(os.path.dirname(__file__), "krx_stocks.csv")

with open(_CSV_PATH, encoding="utf-8") as f:
    KRX_STOCKS = [(row["code"], row["name"]) for row in csv.DictReader(f)]
