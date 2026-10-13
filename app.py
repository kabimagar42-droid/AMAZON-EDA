import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import streamlit as st
from wordcloud import STOPWORDS, WordCloud

st.set_page_config(page_title="Amazon India Sales EDA", page_icon="🛒", layout="wide")

FILE = "amazon.csv"  # must sit in the same folder as app.py


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def star_bar(value, size=30):
    """Stars filled to the exact rating, e.g. 4.10 fills 82% of 5 stars."""
    pct = max(0.0, min(float(value), 5.0)) / 5 * 100
    return (
        f'<span style="position:relative;display:inline-block;font-size:{size}px;line-height:1;">'
        f'<span style="color:#cfcfcf;">★★★★★</span>'
        f'<span style="color:#f5a623;position:absolute;left:0;top:0;width:{pct:.1f}%;'
        f'overflow:hidden;white-space:nowrap;">★★★★★</span></span>'
    )


def star_text(value):
    n = int(float(value) + 0.5)
    return "★" * n + "☆" * (5 - n)


def make_cloud(texts, extra_stopwords=()):
    text = " ".join(texts.dropna().astype(str)).lower()
    try:
        wc = WordCloud(
            width=900,
            height=450,
            background_color="white",
            stopwords=set(STOPWORDS) | set(extra_stopwords),
            collocations=False,
            max_words=100,
        ).generate(text)
    except ValueError:  # no usable words
        return None
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    return fig


# ------------------------------------------------------------------
# Data (same cleaning steps as the Amazon_EDA notebook)
# ------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(FILE)

    for col in ["discounted_price", "actual_price"]:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(r"[₹,]", "", regex=True), errors="coerce")
    df["discount_percentage"] = pd.to_numeric(
        df["discount_percentage"].astype(str).str.replace("%", "", regex=False), errors="coerce"
    )
    df["rating_count"] = pd.to_numeric(df["rating_count"].astype(str).str.replace(",", "", regex=False), errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")  # junk '|' becomes NaN

    df = df.dropna(subset=["rating", "rating_count", "discounted_price"]).drop_duplicates()

    df["savings"] = df["actual_price"] - df["discounted_price"]
    parts = df["category"].astype(str).str.split("|")
    df["main_category"] = parts.str[0]
    df["sub_category"] = parts.str[1]
    df["desc_length"] = df["about_product"].astype(str).str.len()
    return df


@st.cache_data
def explode_users(df):
    """Each row holds several comma-separated users; make one row per user."""
    rows = []
    for cat, pid, rating, uids, names in zip(
        df["main_category"], df["product_id"], df["rating"], df["user_id"], df["user_name"]
    ):
        ids = [i.strip() for i in str(uids).split(",") if i.strip()]
        nms = [n.strip() for n in str(names).split(",")]
        if len(nms) != len(ids):
            nms = ids
        for uid, nm in zip(ids, nms):
            rows.append((cat, pid, rating, uid, nm))
    return pd.DataFrame(rows, columns=["main_category", "product_id", "rating", "user_id", "user_name"])


try:
    df = load_data()
except FileNotFoundError:
    st.error(f"Could not find '{FILE}'. Put it in the same folder as app.py.")
    st.stop()
except KeyError as e:
    st.error(f"Column {e} not found in the CSV. Check the column names in load_data().")
    st.stop()

# ------------------------------------------------------------------
# Sidebar slicers
# ------------------------------------------------------------------
st.sidebar.header("Filters")

all_cats = sorted(df["main_category"].unique())
chosen_cats = st.sidebar.multiselect("Category", all_cats, default=all_cats)

pmin, pmax = float(df["discounted_price"].min()), float(df["discounted_price"].max())
price_range = st.sidebar.slider("Discounted price (₹)", pmin, pmax, (pmin, pmax))

rating_range = st.sidebar.slider("Rating", 0.0, 5.0, (0.0, 5.0), step=0.1)

dmin, dmax = int(df["desc_length"].min()), int(df["desc_length"].max())
desc_range = st.sidebar.slider("Product description length (characters)", dmin, dmax, (dmin, dmax))

filtered = df[
    df["main_category"].isin(chosen_cats)
    & df["discounted_price"].between(*price_range)
    & df["rating"].between(*rating_range)
    & df["desc_length"].between(*desc_range)
]

if filtered.empty:
    st.warning("No products match these filters. Try widening them.")
    st.stop()

# ------------------------------------------------------------------
# Header + stars + KPIs
# ------------------------------------------------------------------
st.title("🛒 Amazon India Product Sales: EDA Dashboard")

avg_rating = filtered["rating"].mean()
hero, k1, k2, k3 = st.columns([2, 1, 1, 1])
hero.markdown(
    f"<div style='font-size:14px;color:gray;'>Average rating</div>"
    f"<div style='font-size:40px;font-weight:600;line-height:1.1;'>{avg_rating:.2f} "
    f"{star_bar(avg_rating, 34)}</div>",
    unsafe_allow_html=True,
)
k1.metric("Products", f"{len(filtered):,}")
k2.metric("Median price", f"₹{filtered['discounted_price'].median():,.0f}")
k3.metric("Avg discount", f"{filtered['discount_percentage'].mean():.1f}%")

st.divider()

tab_over, tab_price, tab_rate, tab_wc, tab_users, tab_data = st.tabs(
    ["Overview", "Pricing & Discounts", "Ratings", "Word Clouds", "Users by Category", "Data"]
)

# ------------------------------------------------------------------
# Overview
# ------------------------------------------------------------------
with tab_over:
    c1, c2 = st.columns(2)

    counts = filtered["main_category"].value_counts().reset_index()
    counts.columns = ["Category", "Products"]
    fig_counts = px.bar(
        counts, x="Products", y="Category", orientation="h", title="Products per category", text_auto=True
    )
    fig_counts.update_traces(textposition="outside", cliponaxis=False)
    c1.plotly_chart(fig_counts)

    desc_hist = px.histogram(filtered, x="desc_length", nbins=40, title="Product description length (characters)")
    c2.plotly_chart(desc_hist)

# ------------------------------------------------------------------
# Pricing & Discounts
# ------------------------------------------------------------------
with tab_price:
    c1, c2 = st.columns(2)
    c1.plotly_chart(
        px.histogram(filtered, x="discounted_price", nbins=40, title="Distribution of discounted price"),
    )
    c2.plotly_chart(
        px.scatter(
            filtered,
            x="discount_percentage",
            y="rating",
            color="main_category",
            hover_name="product_name",
            opacity=0.6,
            title="Discount % vs rating",
        ),
    )
    corr = filtered["discount_percentage"].corr(filtered["rating"])
    st.info(f"Correlation between discount % and rating: **{corr:.2f}** (close to 0 means no real link)")

# ------------------------------------------------------------------
# Ratings (with stars)
# ------------------------------------------------------------------
with tab_rate:
    by_cat = (
        filtered.groupby("main_category")
        .agg(Products=("product_id", "count"), Avg_rating=("rating", "mean"))
        .reset_index()
        .sort_values("Avg_rating", ascending=False)
    )
    by_cat["Stars"] = by_cat["Avg_rating"].apply(star_text)
    by_cat["Avg_rating"] = by_cat["Avg_rating"].round(2)
    by_cat = by_cat.rename(columns={"main_category": "Category", "Avg_rating": "Avg rating"})

    c1, c2 = st.columns(2)
    c1.subheader("Average rating by category")
    c1.dataframe(by_cat[["Category", "Stars", "Avg rating", "Products"]], hide_index=True)
    c2.plotly_chart(px.histogram(filtered, x="rating", nbins=20, title="Rating distribution"))

    st.subheader("Top 10 most-reviewed products")
    top = filtered.sort_values("rating_count", ascending=False).head(10).copy()
    top["Stars"] = top["rating"].apply(star_text)
    top["product_name"] = top["product_name"].str[:70]
    st.dataframe(top[["product_name", "Stars", "rating", "rating_count"]], hide_index=True)

# ------------------------------------------------------------------
# Word clouds (with category slicer)
# ------------------------------------------------------------------
with tab_wc:
    cats = ["All"] + sorted(filtered["main_category"].unique())
    wc_cat = st.selectbox("Category", cats, key="wc_cat")
    wc_df = filtered if wc_cat == "All" else filtered[filtered["main_category"] == wc_cat]
    st.caption(f"{len(wc_df):,} products in this selection")

    c1, c2 = st.columns(2)
    c1.subheader("Product descriptions")
    fig = make_cloud(wc_df["about_product"], {"will", "can", "also", "use", "using", "make", "one"})
    if fig:
        c1.pyplot(fig)
    else:
        c1.info("Not enough text for a word cloud.")

    c2.subheader("Review titles")
    fig = make_cloud(wc_df["review_title"])
    if fig:
        c2.pyplot(fig)
    else:
        c2.info("Not enough text for a word cloud.")

# ------------------------------------------------------------------
# Users by category
# ------------------------------------------------------------------
with tab_users:
    users = explode_users(filtered)

    u1, u2, u3 = st.columns(3)
    u1.metric("Unique users", f"{users['user_id'].nunique():,}")
    u2.metric("User reviews", f"{len(users):,}")
    multi = (users.groupby("user_id")["main_category"].nunique() > 1).sum()
    u3.metric("Users active in 2+ categories", f"{multi:,}")

    per_cat = (
        users.groupby("main_category")
        .agg(
            Unique_users=("user_id", "nunique"),
            Reviews=("user_id", "size"),
            Products_reviewed=("product_id", "nunique"),
            Avg_product_rating=("rating", "mean"),
        )
        .reset_index()
        .sort_values("Unique_users", ascending=False)
    )
    per_cat["Avg_product_rating"] = per_cat["Avg_product_rating"].round(2)
    per_cat.columns = ["Category", "Unique users", "Reviews", "Products reviewed", "Avg rating of products"]

    c1, c2 = st.columns(2)
    c1.subheader("Users per category")
    c1.dataframe(per_cat, hide_index=True)
    fig_users = px.bar(
        per_cat, x="Unique users", y="Category", orientation="h", title="Unique users per category", text_auto=True
    )
    fig_users.update_traces(textposition="outside", cliponaxis=False)
    c2.plotly_chart(fig_users)

    st.subheader("Top users in a category")
    user_cat = st.selectbox("Category", sorted(users["main_category"].unique()), key="user_cat")
    top_users = (
        users[users["main_category"] == user_cat]
        .groupby(["user_id", "user_name"])
        .agg(Products_reviewed=("product_id", "nunique"), Avg_rating=("rating", "mean"))
        .reset_index()
        .sort_values("Products_reviewed", ascending=False)
        .head(15)
    )
    top_users["Avg_rating"] = top_users["Avg_rating"].round(2)
    top_users.columns = ["User ID", "User name", "Products reviewed", "Avg rating of products"]
    st.dataframe(top_users, hide_index=True)

# ------------------------------------------------------------------
# Data
# ------------------------------------------------------------------
with tab_data:
    show = filtered.drop(columns=["img_link", "product_link"], errors="ignore")
    st.dataframe(show)
    st.download_button(
        "Download filtered data (CSV)",
        show.to_csv(index=False).encode("utf-8"),
        file_name="amazon_filtered.csv",
        mime="text/csv",
    )
