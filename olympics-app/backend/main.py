from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import pandas as pd

import helper

app = FastAPI(title="Olympics Data Analysis API")

# Allow the Streamlit frontend (or anything else) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the dataset once at startup and keep it in memory.
df = helper.load_data()
YEARS, COUNTRIES = helper.get_years_countries(df)


def df_to_records(d: pd.DataFrame):
    return d.replace({pd.NA: None}).where(pd.notnull(d), None).to_dict(orient="records")


@app.get("/")
def root():
    return {"status": "ok", "message": "Olympics Data Analysis API is running"}


@app.get("/meta")
def meta():
    """Returns the list of selectable years and countries for dropdowns."""
    return {"years": YEARS, "countries": COUNTRIES}


@app.get("/overall/stats")
def overall_stats():
    return helper.overall_stats(df)


@app.get("/overall/medal-tally")
def medal_tally(year: str = Query("Overall"), country: str = Query("Overall")):
    if year != "Overall" and year not in YEARS:
        raise HTTPException(status_code=400, detail="Invalid year")
    if country != "Overall" and country not in COUNTRIES:
        raise HTTPException(status_code=400, detail="Invalid country")
    result = helper.fetch_medal_tally(df, year, country)
    return df_to_records(result)


@app.get("/overall/participating-nations")
def participating_nations():
    return df_to_records(helper.data_over_time(df, "region"))


@app.get("/overall/events-over-time")
def events_over_time():
    return df_to_records(helper.data_over_time(df, "Event"))


@app.get("/overall/athletes-over-time")
def athletes_over_time():
    return df_to_records(helper.data_over_time(df, "Name"))


@app.get("/overall/most-successful")
def most_successful(sport: str = Query("Overall")):
    return df_to_records(helper.most_successful(df, sport))


@app.get("/overall/sports-list")
def sports_list():
    sports = sorted(df["Sport"].dropna().unique().tolist())
    return {"sports": ["Overall"] + sports}


@app.get("/country/medal-tally-over-years")
def country_medal_tally(country: str = Query(...)):
    if country not in COUNTRIES or country == "Overall":
        raise HTTPException(status_code=400, detail="Invalid country")
    return df_to_records(helper.yearwise_medal_tally(df, country))


@app.get("/country/heatmap")
def country_heatmap(country: str = Query(...)):
    if country not in COUNTRIES or country == "Overall":
        raise HTTPException(status_code=400, detail="Invalid country")
    pt = helper.country_event_heatmap(df, country)
    # Convert the pivot table into a simple long-format list for easy plotting.
    data = []
    for sport in pt.index:
        for year in pt.columns:
            val = pt.loc[sport, year]
            if val:
                data.append({"Sport": sport, "Year": int(year), "Count": int(val)})
    return data


@app.get("/country/top-athletes")
def country_top_athletes(country: str = Query(...)):
    if country not in COUNTRIES or country == "Overall":
        raise HTTPException(status_code=400, detail="Invalid country")
    return df_to_records(helper.most_successful_countrywise(df, country))


@app.get("/athlete/age-distribution")
def age_distribution():
    return helper.age_distribution(df)


@app.get("/athlete/age-distribution-by-sport")
def age_distribution_by_sport():
    return helper.age_distribution_by_sport(df)


@app.get("/athlete/men-vs-women")
def men_vs_women():
    return df_to_records(helper.men_vs_women(df))


@app.get("/athlete/height-weight")
def height_weight(sport: str = Query("Overall")):
    return df_to_records(helper.height_weight_scatter(df, sport))
