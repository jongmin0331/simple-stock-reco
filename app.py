import streamlit as st
from data_fetcher import fetch_history, ensure_kr_suffix
from recommender import recommend_by_momentum, recommend_advanced
from tickers_fetcher import fetch_nasdaq_list, fetch_kospi_list


st.set_page_config(page_title="간단 주식 추천 앱", layout="centered")

st.title("나스닥 & 코스피 간단 주식 추천 앱 — 고도화 버전")

# Single sidebar layout; avoid creating duplicate widgets with same labels
mode = st.sidebar.radio("모드 선택", ["Quick (수동 입력)", "Advanced Market Scan"], key="mode")
market = st.sidebar.selectbox("마켓 선택", ["NASDAQ", "KOSPI"], key="market")

if mode == "Quick (수동 입력)":
	tickers_input = st.sidebar.text_area("종목 입력 (쉼표로 구분)", value="AAPL, MSFT" if market=="NASDAQ" else "005930, 000660", key="tickers_input")
	top_n = st.sidebar.number_input("추천 개수", min_value=1, max_value=50, value=5, key="top_n")
	period_days = st.sidebar.slider("조회 기간(일)", min_value=30, max_value=365, value=120, key="period_days")

	if st.sidebar.button("추천 실행 (빠른 모드)", key="quick_run"):
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
			st.subheader("추천 결과 (빠른 모드)")
			st.dataframe(df_rec)

else:
	st.sidebar.markdown("주의: 시장 전체 스캔은 네트워크 요청이 많아 시간이 오래 걸립니다.")
	max_scan = st.sidebar.number_input("최대 스캔 종목 수", min_value=10, max_value=2000, value=200, key="max_scan")
	if st.sidebar.button("Advanced 스캔 실행", key="adv_run"):
		with st.spinner("티커 목록을 불러오는 중..."):
			try:
				if market == 'NASDAQ':
					universe = fetch_nasdaq_list()
				else:
					universe = fetch_kospi_list()
			except Exception as e:
				st.error(f"티커 목록을 불러오던 중 오류: {e}")
				universe = []

		if not universe:
			st.warning("티커 목록을 불러오지 못했습니다.")
		else:
			st.info(f"스캔 대상 티커 수: {len(universe)} (최대 {max_scan}개로 제한)")
			with st.spinner("고도화 스캔을 실행 중입니다... (시간이 걸립니다)"):
				result = recommend_advanced(lambda t, period: fetch_history(t, period=period), universe, max_scan=max_scan)

			# result is a dict with 'buy','sell','hold' DataFrames
			df_buy = result.get('buy', pd.DataFrame())
			df_sell = result.get('sell', pd.DataFrame())
			df_hold = result.get('hold', pd.DataFrame())

			if df_buy.empty and df_sell.empty and df_hold.empty:
				st.warning("추천 결과가 없습니다.")
			else:
				if not df_buy.empty:
					st.subheader("Buy 추천")
					st.dataframe(df_buy)
				if not df_sell.empty:
					st.subheader("Sell 추천")
					st.dataframe(df_sell)
				if not df_hold.empty:
					st.subheader("Hold / 기타")
					st.dataframe(df_hold)

st.markdown("---")
st.markdown("**설명:** 고급 모드는 RSI, 일목균형표, 간단한 뉴스 감성 점수를 결합해 `buy`/`sell`/`hold`를 출력합니다. 전체 시장 스캔 시 네트워크 요청과 시간이 많이 필요합니다.")

