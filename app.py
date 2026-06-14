import streamlit as st
import yfinance as yf
import pandas as pd
from yahooquery import search

# -----------------------------
# TICKER RESOLVER (NAME → TICKER)
# -----------------------------
def get_ticker(query):
    try:
        # already a ticker
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
# DATA CACHE
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
# SCORING MODEL (BREAKDOWN)
# -----------------------------
def stock_score(d):
    roe = d.get("roe") or 0
    debt = d.get("debt") or 0
    growth = d.get("growth") or 0

    profitability = min(roe * 20, 10)
    risk = max(10 - debt * 3, 0)
    growth_score = min(growth * 50, 10)
    valuation = 7  # placeholder (can improve later)

    final = (
        profitability * 0.4 +
        risk * 0.3 +
        growth_score * 0.3
    )

    return {
        "final": round(final, 2),
        "profitability": round(profitability, 2),
        "risk": round(risk, 2),
        "growth": round(growth_score, 2),
        "valuation": valuation
    }


def etf_score(d):
    r = d.get("return_1y") or 0
    score = r * 10

    return {
        "final": round(score, 2),
        "performance": round(score, 2)
    }


# -----------------------------
# GRADE SYSTEM
# -----------------------------
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
# PROBABILITY MODEL (HEURISTIC)
# -----------------------------
def probability_of_profit(scores):
    base = (
        scores.get("profitability", 0) * 0.4 +
        scores.get("growth", 0) * 0.3 +
        scores.get("risk", 0) * 0.2 +
        scores.get("valuation", 5) * 0.1
    )

    prob = base * 10
    prob = max(5, min(prob, 95))

    return round(prob, 1)


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
            scores = etf_score(d)
            typ = "ETF"
        else:
            scores = stock_score(d)
            typ = "STOCK"

        rows.append({
            "Asset": ticker,
            "Type": typ,

            "Final Score": scores["final"],
            "Profitability": scores.get("profitability"),
            "Risk": scores.get("risk"),
            "Growth": scores.get("growth"),
            "Valuation": scores.get("valuation"),

            "Win Probability %": probability_of_profit(scores),

            "Grade": grade(scores["final"]),
            "Sector": d.get("sector") or "ETF/Broad Market"
        })

    if not rows:
        st.error("No valid assets found")
        return

    df = pd.DataFrame(rows).sort_values("Final Score", ascending=False)

    st.subheader("📊 Full Results")
    st.dataframe(df, use_container_width=True)

    st.subheader("🏆 Top Picks (≥ 7)")
    st.dataframe(df[df["Final Score"] >= 7], use_container_width=True)

    st.subheader("🟡 Watchlist (5–7)")
    st.dataframe(df[(df["Final Score"] >= 5) & (df["Final Score"] < 7)], use_container_width=True)

    st.subheader("🔴 Weak (<5)")
    st.dataframe(df[df["Final Score"] < 5], use_container_width=True)


# -----------------------------
# UI
# -----------------------------
st.title("📈 AI Stock + ETF Screener (Quant Mode)")

user_input = st.text_input("Enter companies or tickers (Apple, Tesla, NVDA, VOO)")

if user_input:
    items = [x.strip() for x in user_input.split(",")]
    analyze(items)
