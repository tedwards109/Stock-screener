
import streamlit as st
import yfinance as yf
import pandas as pd

# -----------------------------
# NAME → TICKER MAP
# -----------------------------
name_map = {
    "tesla": "TSLA",
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "nvidia": "NVDA",
    "amd": "AMD",
    "ford": "F",
    "gm": "GM",
    "toyota": "TM",
    "voo": "VOO",
    "spy": "SPY",
    "qqq": "QQQ",
    "vti": "VTI"
}

cache = {}

def get_data(ticker):
    if ticker in cache:
        return cache[ticker]

    try:
        s = yf.Ticker(ticker)
        info = s.info
        hist = s.history(period="1y")

        data = {
            "ticker": ticker,
            "is_etf": info.get("quoteType") == "ETF",
            "sector": info.get("sector"),
            "roe": info.get("returnOnEquity"),
            "debt": info.get("debtToEquity"),
            "growth": info.get("revenueGrowth"),
            "return_1y": None
        }

        if hist is not None and not hist.empty:
            start = hist["Close"].iloc[0]
            end = hist["Close"].iloc[-1]
            data["return_1y"] = (end - start) / start

        cache[ticker] = data
        return data

    except:
        return None

def stock_score(d):
    roe = d.get("roe") or 0
    debt = d.get("debt") or 0
    growth = d.get("growth") or 0

    return (
        min(roe * 20, 10) * 0.4 +
        max(10 - debt * 3, 0) * 0.3 +
        min(growth * 50, 10) * 0.3
    )

def etf_score(d):
    r = d.get("return_1y") or 0
    return r * 10

def grade(s):
    if s >= 8: return "A+"
    if s >= 7: return "A"
    if s >= 6: return "B"
    if s >= 5: return "C"
    return "D"

def analyze(inputs):
    rows = []

    for name in inputs:
        ticker = name_map.get(name.lower())
        if not ticker:
            continue

        d = get_data(ticker)
        if not d:
            continue

        if d["is_etf"]:
            score = etf_score(d)
            typ = "ETF"
        else:
            score = stock_score(d)
            typ = "STOCK"

        rows.append({
            "Asset": ticker,
            "Type": typ,
            "Score": round(score, 2),
            "Grade": grade(score),
            "Sector": d.get("sector", "ETF")
        })

    if not rows:
        st.error("No valid data found")
        return

    df = pd.DataFrame(rows).sort_values("Score", ascending=False)

    st.subheader("📊 Results")
    st.dataframe(df)

    st.subheader("🏆 Top Picks")
    st.dataframe(df[df["Score"] >= 7])

    st.subheader("🟡 Watchlist")
    st.dataframe(df[(df["Score"] >= 5) & (df["Score"] < 7)])

st.title("📈 Stock + ETF Screener")

user_input = st.text_input("Enter assets (Tesla, Apple, VOO, QQQ)")

if user_input:
    items = [x.strip() for x in user_input.split(",")]
    analyze(items)
