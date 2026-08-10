# 내 주식 포트폴리오

국장/미장/ETF 보유 종목을 검색해서 추가하고, 당일 등락률·등락액·관련 뉴스를 확인하는 웹앱.
로그인 기반이라 여러 사람이 같은 배포 주소를 써도 각자 자기 포트폴리오만 봅니다.

## 1. Supabase 설정 (최초 1회, 무료)

1. https://supabase.com 가입 후 새 프로젝트 생성 (리전은 Northeast Asia 가까운 곳 추천)
2. 왼쪽 메뉴 **SQL Editor** 에서 `sql/schema.sql` 내용을 붙여넣고 실행
3. 왼쪽 메뉴 **Project Settings → API** 에서 `Project URL` 과 `anon public` 키를 복사

## 2. 로컬 실행

```bash
pip install -r requirements.txt
```

`.streamlit/secrets.toml.example` 을 복사해서 `.streamlit/secrets.toml` 로 만들고, 1번에서 복사한 값을 채웁니다.

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속. 같은 와이파이의 휴대폰에서 쓰려면 PC의 로컬 IP로 접속하면 됩니다 (`ipconfig`로 확인).

## 3. 배포 (Streamlit Community Cloud, 무료)

1. 이 폴더를 GitHub 저장소로 push (`secrets.toml`은 `.gitignore`에 이미 포함되어 올라가지 않음)
2. https://share.streamlit.io 에서 GitHub로 로그인 → "New app" → 저장소/브랜치/`app.py` 선택
3. 배포 화면의 **Advanced settings → Secrets** 에 아래 내용을 붙여넣기

   ```toml
   SUPABASE_URL = "..."
   SUPABASE_KEY = "..."
   ```

4. Deploy. 완료되면 나오는 URL로 PC 꺼져 있어도 휴대폰/어디서든 접속 가능.

## 파일 구조

- `app.py` — 메인 화면 (종목 추가/삭제, 시세, 뉴스)
- `auth.py` — 회원가입/로그인
- `db.py` — Supabase 클라이언트
- `stocks.py` — yfinance 시세/뉴스 조회
- `portfolio.py` — 보유 종목 DB read/write
- `sql/schema.sql` — Supabase 테이블 생성 스크립트

## 참고

- 비밀번호는 bcrypt로 해시해서 저장합니다. 다만 이 앱은 개인/소규모 사용을 가정한 간단한 자체 로그인이라, 이메일 인증·비밀번호 재설정 같은 기능은 없습니다.
- 시세/뉴스는 Yahoo Finance(yfinance)에서 가져옵니다. 국내 종목은 `005930.KS`처럼 티커 뒤에 `.KS`(코스피)/`.KQ`(코스닥)가 붙습니다 — 검색 결과에서 선택하면 자동으로 맞는 티커가 들어갑니다.
