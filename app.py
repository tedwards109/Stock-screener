import streamlit as st
import yfinance as yf
import pandas as pd
from yahooquery import search

# -----------------------------
# TICKER RESOLVER (NAME OR SYMBOL)
# -----------------------------
def get_ticker(query):
    try:
        # If user already entered ticker
        if query.isupper() and len(query) <= 5:
            return query

        result = search(query)
        quotes = result.get("quotes", [])

        if not quotes:
            return None

        return quotes[0].get("symbol")

    except:
        return None


# -----------------------------
# DATA FETCH
# -----------------------------
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


# -----------------------------
# SCORING
# -----------------------------
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


def grade(score):
    if score >= 8:
        return "A+"
    elif score >= 7:
        return "A"
    elif score >= 6:
        return "B"
    elif score >= 5:
        return "C"
    return "D"


# -----------------------------
# ANALYSIS ENGINE
# -----------------------------
def analyze(inputs):

    rows = []

    for item in inputs:

        ticker = get_ticker(item)

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
            "Sector": d.get("sector") or "ETF/Broad Market"
        })

    if not rows:
        st.error("No valid assets found")
        return

    df = pd.DataFrame(rows).sort_values("Score", ascending=False)

    st.subheader("📊 Full Results")
    st.dataframe(df, use_container_width=True)

    st.subheader("🏆 Top Picks (≥ 7)")
    st.dataframe(df[df["Score"] >= 7], use_container_width=True)

    st.subheader("🟡 Watchlist (5–7)")
    st.dataframe(df[(df["Score"] >= 5) & (df["Score"] < 7)], use_container_width=True)

    st.subheader("🔴 Weak (<5)")
    st.dataframe(df[df["Score"] < 5], use_container_width=True)


# -----------------------------
# UI
# -----------------------------
st.title("📈 AI Stock + ETF Screener (Pro Mode)")

user_input = st.text_input("Enter companies or tickers (e.g. Apple, Tesla, VOO, NVDA)")

if user_input:
    items = [x.strip() for x in user_input.split(",")]
    analyze(items)
