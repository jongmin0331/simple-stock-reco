import streamlit as st
from data_fetcher import fetch_history, ensure_kr_suffix
from recommender import recommend_by_momentum


st.set_page_config(page_title="간단 주식 추천 앱", layout="centered")

st.title("나스닥 & 코스피 간단 주식 추천 앱")

market = st.sidebar.selectbox("마켓 선택", ["NASDAQ", "KOSPI"])
tickers_input = st.sidebar.text_area("종목 입력 (쉼표로 구분)", value="AAPL, MSFT" if market=="NASDAQ" else "005930, 000660")
top_n = st.sidebar.number_input("추천 개수", min_value=1, max_value=20, value=5)
period_days = st.sidebar.slider("조회 기간(일)", min_value=30, max_value=365, value=120)

if st.sidebar.button("추천 실행"):
	raw = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
	if market == "KOSPI":
		tickers = [ensure_kr_suffix(t) for t in raw]
	else:
		tickers = raw

	with st.spinner("데이터를 가져오고 추천을 계산 중입니다..."):
		try:
			df_rec = recommend_by_momentum(lambda t, period: fetch_history(t, period=period), tickers, period_days=period_days, top_n=top_n)
		except Exception as e:
			st.error(f"오류: {e}")
			df_rec = None

	if df_rec is None or df_rec.empty:
		st.warning("추천 결과가 없습니다. 종목명을 확인하세요.")
	else:
		st.subheader("추천 결과")
		st.dataframe(df_rec)

st.markdown("---")
st.markdown("**설명:** 이 앱은 간단한 모멘텀/변동성 기반 규칙으로 종목을 추천합니다. 교육용 예제일 뿐이며 투자 권유가 아닙니다.")

