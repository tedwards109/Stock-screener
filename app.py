def get_ticker(query):
    try:
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

# LONG TERM STOCK SCORING MODEL

# -----------------------------

def stock_score(d):


metrics = []

# QUALITY
quality = None
roe = d.get("roe")
if roe is not None:
    quality = min(max(roe * 25, 0), 10)
    metrics.append(quality)

# GROWTH
growth_rating = None
growth = d.get("growth")
if growth is not None:
    growth_rating = min(max(growth * 40, 0), 10)
    metrics.append(growth_rating)

# FINANCIAL STRENGTH
financial_strength = None
debt = d.get("debt")
if debt is not None:
    financial_strength = min(max(10 - (debt / 30), 0), 10)
    metrics.append(financial_strength)

# MOMENTUM
momentum = None
ret = d.get("return_1y")
if ret is not None:
    momentum = min(max((ret * 20) + 5, 0), 10)
    metrics.append(momentum)

# VALUATION
valuation = 5
metrics.append(valuation)

final = (
    (quality or 0) * 0.30 +
    (growth_rating or 0) * 0.25 +
    (financial_strength or 0) * 0.20 +
    valuation * 0.15 +
    (momentum or 0) * 0.10
)

confidence = round(
    (
        (quality is not None) +
        (growth_rating is not None) +
        (financial_strength is not None) +
        (momentum is not None)
    ) / 4 * 100
)

return {
    "final": round(final, 2),
    "quality": round(quality or 0, 2),
    "growth": round(growth_rating or 0, 2),
    "financial_strength": round(financial_strength or 0, 2),
    "valuation": valuation,
    "momentum": round(momentum or 0, 2),
    "confidence": confidence,
    "investment_attractiveness": round(final * 10)
}


# -----------------------------

# ETF SCORING

# -----------------------------

def etf_score(d):
r = d.get("return_1y") or 0


return {
    "final": round(r * 10, 2),
    "quality": None,
    "growth": None,
    "financial_strength": None,
    "valuation": None,
    "momentum": round(r * 10, 2),
    "confidence": 100,
    "investment_attractiveness": round(r * 100)
}


# -----------------------------

# GRADE SYSTEM

# -----------------------------

def grade(score):
if score >= 8.5:
return "A+"
elif score >= 8:
return "A"
elif score >= 7:
return "B"
elif score >= 6:
return "C"
else:
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
        scores = etf_score(d)
        typ = "ETF"
    else:
        scores = stock_score(d)
        typ = "STOCK"

    rows.append({
        "Asset": ticker,
        "Type": typ,

        "Overall": scores["final"],
        "Grade": grade(scores["final"]),

        "Confidence %": scores.get("confidence"),

        "Investment Attractiveness":
            scores.get("investment_attractiveness"),

        "Quality": scores.get("quality"),
        "Growth": scores.get("growth"),
        "Financial Strength":
            scores.get("financial_strength"),
        "Valuation": scores.get("valuation"),
        "Momentum": scores.get("momentum"),

        "Sector": d.get("sector") or "Unknown"
    })

if not rows:
    st.error("No valid assets found")
    return

df = pd.DataFrame(rows).sort_values(
    "Overall",
    ascending=False
)

st.subheader("📊 Full Results")
st.dataframe(df, use_container_width=True)

st.subheader("🏆 Top Picks (≥ 7)")
st.dataframe(
    df[df["Overall"] >= 7],
    use_container_width=True
)

st.subheader("🟡 Watchlist (5–7)")
st.dataframe(
    df[
        (df["Overall"] >= 5) &
        (df["Overall"] < 7)
    ],
    use_container_width=True
)

st.subheader("🔴 Weak (<5)")
st.dataframe(
    df[df["Overall"] < 5],
    use_container_width=True
)


# -----------------------------

# UI

# -----------------------------

st.title("📈 Long-Term Stock Screener")

user_input = st.text_input(
"Enter companies or tickers (Apple, Tesla, NVDA, VOO)"
)

if user_input:
items = [x.strip() for x in user_input.split(",")]
analyze(items)
