import os
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.figure_factory as ff

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
# Set BACKEND_URL as an environment variable on Render (or in a .env file
# locally) to point at your deployed FastAPI service, e.g.
#   BACKEND_URL = https://olympics-api.onrender.com
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Olympics Data Analysis", page_icon="🏅", layout="wide")


@st.cache_data(ttl=3600)
def api_get(path, params=None):
    resp = requests.get(f"{BACKEND_URL}{path}", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.title("🏅 Olympics Data Analysis")
menu = st.sidebar.radio(
    "Menu",
    ["Medal Tally", "Overall Analysis", "Country-wise Analysis", "Athlete-wise Analysis"],
)

try:
    meta = api_get("/meta")
except requests.exceptions.RequestException as e:
    st.error(
        f"Could not reach the backend API at {BACKEND_URL}. "
        f"Make sure the FastAPI service is running and BACKEND_URL is set correctly.\n\n{e}"
    )
    st.stop()

years = meta["years"]
countries = meta["countries"]

# ---------------------------------------------------------------------------
# 1. Medal Tally
# ---------------------------------------------------------------------------
if menu == "Medal Tally":
    st.sidebar.header("Filters")
    selected_year = st.sidebar.selectbox("Select Year", years)
    selected_country = st.sidebar.selectbox("Select Country", countries)

    data = api_get("/overall/medal-tally", {"year": selected_year, "country": selected_country})
    df = pd.DataFrame(data)

    if selected_year == "Overall" and selected_country == "Overall":
        st.title("Overall Tally")
    elif selected_year != "Overall" and selected_country == "Overall":
        st.title(f"Medal Tally in {selected_year} Olympics")
    elif selected_year == "Overall" and selected_country != "Overall":
        st.title(f"{selected_country}'s Overall Performance")
    else:
        st.title(f"{selected_country}'s Performance in {selected_year} Olympics")

    st.dataframe(df, use_container_width=True)

# ---------------------------------------------------------------------------
# 2. Overall Analysis
# ---------------------------------------------------------------------------
elif menu == "Overall Analysis":
    stats = api_get("/overall/stats")

    st.title("Top Statistics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Editions", stats["editions"])
    col2.metric("Hosts", stats["cities"])
    col3.metric("Sports", stats["sports"])

    col4, col5, col6 = st.columns(3)
    col4.metric("Events", stats["events"])
    col5.metric("Nations", stats["nations"])
    col6.metric("Athletes", stats["athletes"])

    nations_over_time = pd.DataFrame(api_get("/overall/participating-nations"))
    st.title("Participating Nations over the years")
    fig = px.line(nations_over_time, x="Year", y="count")
    st.plotly_chart(fig, use_container_width=True)

    events_over_time = pd.DataFrame(api_get("/overall/events-over-time"))
    st.title("Events over the years")
    fig = px.line(events_over_time, x="Year", y="count")
    st.plotly_chart(fig, use_container_width=True)

    athletes_over_time = pd.DataFrame(api_get("/overall/athletes-over-time"))
    st.title("Athletes over the years")
    fig = px.line(athletes_over_time, x="Year", y="count")
    st.plotly_chart(fig, use_container_width=True)

    st.title("Most Successful Athletes")
    sports_list = api_get("/overall/sports-list")["sports"]
    selected_sport = st.selectbox("Select a Sport", sports_list)
    top_athletes = pd.DataFrame(api_get("/overall/most-successful", {"sport": selected_sport}))
    st.dataframe(top_athletes, use_container_width=True)

# ---------------------------------------------------------------------------
# 3. Country-wise Analysis
# ---------------------------------------------------------------------------
elif menu == "Country-wise Analysis":
    st.sidebar.header("Filters")
    country_options = [c for c in countries if c != "Overall"]
    selected_country = st.sidebar.selectbox("Select a Country", country_options)

    tally = pd.DataFrame(api_get("/country/medal-tally-over-years", {"country": selected_country}))
    st.title(f"{selected_country} Medal Tally over the years")
    if not tally.empty:
        fig = px.line(tally, x="Year", y="Medal")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No medal data available for this country.")

    st.title(f"{selected_country} excels in the following sports")
    heatmap_data = api_get("/country/heatmap", {"country": selected_country})
    if heatmap_data:
        hdf = pd.DataFrame(heatmap_data)
        pivot = hdf.pivot(index="Sport", columns="Year", values="Count").fillna(0)
        fig = px.imshow(pivot, aspect="auto", labels=dict(color="Medals"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sport heatmap data available for this country.")

    st.title(f"Top 10 Athletes of {selected_country}")
    top_athletes = pd.DataFrame(api_get("/country/top-athletes", {"country": selected_country}))
    st.dataframe(top_athletes, use_container_width=True)

# ---------------------------------------------------------------------------
# 4. Athlete-wise Analysis
# ---------------------------------------------------------------------------
elif menu == "Athlete-wise Analysis":
    st.title("Distribution of Age")
    age_data = api_get("/athlete/age-distribution")
    labels = []
    hist_data = []
    for label in ["Overall", "Gold", "Silver", "Bronze"]:
        vals = age_data.get(label, [])
        if len(vals) > 1:
            labels.append(label)
            hist_data.append(vals)
    fig = ff.create_distplot(hist_data, labels, show_hist=False, show_rug=False)
    st.plotly_chart(fig, use_container_width=True)

    st.title("Distribution of Age for Gold Medalists (by Sport)")
    sport_age_data = api_get("/athlete/age-distribution-by-sport")
    labels = list(sport_age_data.keys())
    hist_data = [sport_age_data[s] for s in labels]
    if hist_data:
        fig = ff.create_distplot(hist_data, labels, show_hist=False, show_rug=False)
        st.plotly_chart(fig, use_container_width=True)

    st.title("Men vs Women Participation over the years")
    mvw = pd.DataFrame(api_get("/athlete/men-vs-women"))
    fig = px.line(mvw, x="Year", y=["Male", "Female"])
    st.plotly_chart(fig, use_container_width=True)

    st.title("Height vs Weight")
    sports_list = api_get("/overall/sports-list")["sports"]
    selected_sport = st.selectbox("Select a Sport", sports_list, key="hw_sport")
    hw = pd.DataFrame(api_get("/athlete/height-weight", {"sport": selected_sport}))
    if not hw.empty:
        fig = px.scatter(hw, x="Weight", y="Height", color="Medal", symbol="Sex")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No height/weight data available for this sport.")
