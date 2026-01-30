# 간단한 주식 추천 앱 (NASDAQ / KOSPI)

이 프로젝트는 Python과 Streamlit을 사용해 초보자도 쉽게 따라할 수 있는 간단한 주식 추천 앱 예제입니다.

요구사항
- Python 3.9+
- Windows PowerShell 사용 예시

설치

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

실행

```powershell
streamlit run app.py
```

사용법 요약
- 마켓 선택: `NASDAQ` 또는 `KOSPI`
- 종목 입력: 쉼표로 구분 (KOSPI는 숫자 코드 예: `005930` 또는 `005930.KS`)
- 추천 버튼을 누르면 모멘텀 대비 변동성 비율이 높은 종목을 추천합니다.

참고
- 실제 투자 판단을 위한 충분한 검증이 필요합니다. 이 코드는 교육용 예제입니다.
