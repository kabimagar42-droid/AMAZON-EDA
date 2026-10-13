# Amazon India Sales: Exploratory Data Analysis and Dashboard

An analysis of Amazon India product data to see how pricing, discounts and ratings relate across categories. The results are available as a live, filterable dashboard.

**Live dashboard:** [https://amazon-eda-fcgg9pcwpafkwxvedx8mqi.streamlit.app/]

## Questions this project answers

- Do bigger discounts go with better ratings?
- Which categories discount the most?
- How do prices spread within each category?
- Which products and categories get the most customer ratings?

## What I did

1. Loaded the Amazon India product sales dataset.
2. Cleaned it: fixed data types, removed currency symbols, handled missing values and dropped duplicates.
3. Explored it with Pandas and built charts to answer the questions above.
4. Turned the analysis into a Streamlit dashboard where you can filter by category and see the charts update.
5. Deployed the dashboard on Streamlit Community Cloud.

## Key findings

- [Finding 1, Correlation between discount % and rating: -0.16 (close to 0 means no real link)]
- [Finding 2, Categories Computers & Accessories, Electronics, Home & Kitchen, These three biggest categories rate almost the same, between 4.04 and 4.16 stars. also holds about 97% of all users]
- [Finding 3 Price, savings, and rating_count are heavily right-skewed. Most products are cheap and have few ratings, and a small number have very high values.]

## Tools used

- Python
- Pandas and NumPy
- Matplotlib
- Streamlit
- Jupyter Notebook
- GitHub

## Project structure

```
AMAZON-EDA/
├── data/                  # dataset used in the analysis
├── notebook.ipynb         # cleaning and exploration
├── app.py                 # Streamlit dashboard
├── requirements.txt       # packages needed to run the app
└── README.md
```

Change this to match your actual folders and file names.

## How to run it locally

```bash
git clone https://amazon-eda-fcgg9pcwpafkwxvedx8mqi.streamlit.app/
cd AMAZON-EDA
pip install -r requirements.txt
streamlit run app.py
```

The dashboard opens in your browser at `http://localhost:8501`.

## Dataset

Amazon India product sales data with fields for product category, actual price, discounted price, discount percentage, rating and rating count. Source: kaggel

## What I learned

This is my first end-to-end analytics project. I learned how to clean messy data, ask clear questions before charting, and deploy a working dashboard. I also learned how to fix package errors and keep a GitHub repo organised.

## About me

I'm Kabi Rana, based in Delhi NCR. I worked two years in BPO operations, tracking case metrics and finding process delays, and I'm now moving into data analysis. I'm looking for data analyst roles.

- LinkedIn: https://www.linkedin.com/in/kabi-rana-14baa9193?utm_source=share_via&utm_content=profile&utm_medium=member_android
- GitHub: https://github.com/kabimagar42-droid
