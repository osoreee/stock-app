import csv
import os

_CSV_PATH = os.path.join(os.path.dirname(__file__), "krx_stocks.csv")

with open(_CSV_PATH, encoding="utf-8") as f:
    _CSV_STOCKS = [(row["code"], row["name"]) for row in csv.DictReader(f)]

# 2018년 스냅샷 이후 신규상장했거나 사명이 바뀐 주요 종목 보정.
# 검색은 옛 이름/새 이름 둘 다 되도록 원본 목록에 추가만 하고,
# 화면 표시용 이름(KRX_NAME_BY_CODE)은 여기 있는 최신 이름을 우선한다.
KRX_EXTRA = [
    ("042660", "한화오션"), ("011200", "HMM"), ("005490", "POSCO홀딩스"),
    ("003670", "포스코퓨처엠"), ("373220", "LG에너지솔루션"), ("326030", "SK바이오팜"),
    ("293490", "카카오게임즈"), ("352820", "하이브"), ("323410", "카카오뱅크"),
    ("377300", "카카오페이"), ("259960", "크래프톤"), ("302440", "SK바이오사이언스"),
    ("402340", "SK스퀘어"), ("361610", "SK아이이테크놀로지"), ("267250", "HD현대"),
    ("009540", "HD한국조선해양"), ("010620", "HD현대미포"), ("450080", "에코프로머티리얼즈"),
]

KRX_STOCKS = _CSV_STOCKS + KRX_EXTRA

KRX_NAME_BY_CODE = {code: name for code, name in _CSV_STOCKS}
KRX_NAME_BY_CODE.update({code: name for code, name in KRX_EXTRA})
