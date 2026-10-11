import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Amazon India Sales EDA", page_icon="🛒", layout="wide")

# ------------------------------------------------------------------
# CONFIG: change these to match YOUR column names (run df.columns)
# ------------------------------------------------------------------
FILE = "amazon.csv"  # put the CSV in the same folder as app.py
COL = {
    "name": "product_name",
    "category": "category",
    "price": "discounted_price",
    "actual": "actual_price",
    "discount": "discount_percentage",
    "rating": "rating",
    "count": "rating_count",
}


def to_num(series):
    """Turn strings like '₹1,099' or '64%' into numbers."""
    cleaned = series.astype(str).str.replace(r"[₹,%\s]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


@st.cache_data
def load_data():
    df = pd.read_csv(FILE)
    for key in ["price", "actual", "discount", "rating", "count"]:
        df[COL[key]] = to_num(df[COL[key]])
    # Main category = first part of 'A|B|C' style category strings
    df["main_category"] = df[COL["category"]].astype(str).str.split("|").str[0]
    return df.dropna(subset=[COL["price"], COL["rating"]])


try:
    df = load_data()
except FileNotFoundError:
    st.error(f"Could not find '{FILE}'. Put it in the same folder as app.py.")
    st.stop()
except KeyError as e:
    st.error(f"Column {e} not found. Update the COL dictionary at the top of app.py.")
    st.stop()

# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------
st.title("🛒 Amazon India Product Sales: EDA Dashboard")
st.caption("Explore pricing, discounts, ratings and categories. Use the sidebar to filter.")

# ------------------------------------------------------------------
# Sidebar filters
# ------------------------------------------------------------------
st.sidebar.header("Filters")

categories = sorted(df["main_category"].unique())
chosen_cats = st.sidebar.multiselect("Category", categories, default=categories)

pmin, pmax = float(df[COL["price"]].min()), float(df[COL["price"]].max())
price_range = st.sidebar.slider("Discounted price (₹)", pmin, pmax, (pmin, pmax))

rating_range = st.sidebar.slider("Rating", 0.0, 5.0, (0.0, 5.0), step=0.1)
min_discount = st.sidebar.slider("Minimum discount (%)", 0, 100, 0)

filtered = df[
    df["main_category"].isin(chosen_cats)
    & df[COL["price"]].between(*price_range)
    & df[COL["rating"]].between(*rating_range)
    & (df[COL["discount"]].fillna(0) >= min_discount)
]

if filtered.empty:
    st.warning("No products match these filters. Try widening them.")
    st.stop()

# ------------------------------------------------------------------
# KPI row
# ------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Products", f"{len(filtered):,}")
k2.metric("Avg discounted price", f"₹{filtered[COL['price']].mean():,.0f}")
k3.metric("Avg discount", f"{filtered[COL['discount']].mean():.1f}%")
k4.metric("Avg rating", f"{filtered[COL['rating']].mean():.2f} ★")

st.divider()

# ------------------------------------------------------------------
# Tabs
# ------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Pricing & Discounts", "Ratings", "Data"])

with tab1:
    c1, c2 = st.columns(2)

    by_cat = filtered["main_category"].value_counts().reset_index()
    by_cat.columns = ["Category", "Products"]
    c1.plotly_chart(
        px.bar(by_cat, x="Products", y="Category", orientation="h", title="Products per category"),
        use_container_width=True,
    )

    disc_cat = (
        filtered.groupby("main_category")[COL["discount"]].mean().sort_values().reset_index()
    )
    disc_cat.columns = ["Category", "Avg discount %"]
    c2.plotly_chart(
        px.bar(disc_cat, x="Avg discount %", y="Category", orientation="h", title="Average discount by category"),
        use_container_width=True,
    )

with tab2:
    c1, c2 = st.columns(2)
    c1.plotly_chart(
        px.histogram(filtered, x=COL["price"], nbins=40, title="Distribution of discounted price"),
        use_container_width=True,
    )
    c2.plotly_chart(
        px.scatter(
            filtered,
            x=COL["discount"],
            y=COL["rating"],
            color="main_category",
            hover_name=COL["name"],
            opacity=0.6,
            title="Does a bigger discount mean a better rating?",
        ),
        use_container_width=True,
    )
    corr = filtered[COL["discount"]].corr(filtered[COL["rating"]])
    st.info(f"Correlation between discount % and rating: **{corr:.2f}**")

with tab3:
    c1, c2 = st.columns(2)
    c1.plotly_chart(
        px.histogram(filtered, x=COL["rating"], nbins=20, title="Rating distribution"),
        use_container_width=True,
    )
    top = (
        filtered.sort_values(COL["count"], ascending=False)
        .head(10)[[COL["name"], COL["rating"], COL["count"]]]
    )
    top[COL["name"]] = top[COL["name"]].str[:50]
    c2.subheader("Top 10 most-reviewed products")
    c2.dataframe(top, hide_index=True, use_container_width=True)

with tab4:
    st.dataframe(filtered, use_container_width=True)
    st.download_button(
        "Download filtered data (CSV)",
        filtered.to_csv(index=False).encode("utf-8"),
        file_name="amazon_filtered.csv",
        mime="text/csv",
    )
