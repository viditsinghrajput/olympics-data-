import pandas as pd
import numpy as np
import os

DATA_DIR = os.path.dirname(os.path.abspath(__file__))


def load_data():
    """Load and preprocess the Olympics data exactly like the notebook does."""
    df = pd.read_csv(os.path.join(DATA_DIR, "athlete_events.csv"))
    region_df = pd.read_csv(os.path.join(DATA_DIR, "noc_regions.csv"))

    df = df[df["Season"] == "Summer"]
    df = df.merge(region_df, on="NOC", how="left")
    df.drop_duplicates(inplace=True)
    df = pd.concat([df, pd.get_dummies(df["Medal"], dtype=int)], axis=1)
    return df


def get_years_countries(df):
    years = df["Year"].unique().tolist()
    years.sort()
    years = ["Overall"] + [str(y) for y in years]

    countries = np.unique(df["region"].dropna().values).tolist()
    countries.sort()
    countries = ["Overall"] + countries

    return years, countries


def fetch_medal_tally(df, year, country):
    medal_df = df.drop_duplicates(
        subset=["Team", "NOC", "Games", "Year", "City", "Sport", "Event", "Medal"]
    )

    flag = 0
    if year == "Overall" and country == "Overall":
        temp_df = medal_df
    elif year == "Overall" and country != "Overall":
        flag = 1
        temp_df = medal_df[medal_df["region"] == country]
    elif year != "Overall" and country == "Overall":
        temp_df = medal_df[medal_df["Year"] == int(year)]
    else:
        temp_df = medal_df[
            (medal_df["Year"] == int(year)) & (medal_df["region"] == country)
        ]

    if flag == 1:
        x = (
            temp_df.groupby("Year")[["Gold", "Silver", "Bronze"]]
            .sum()
            .sort_values("Year")
            .reset_index()
        )
    else:
        x = (
            temp_df.groupby("NOC")[["Gold", "Silver", "Bronze"]]
            .sum()
            .sort_values("Gold", ascending=False)
            .reset_index()
        )

    x["Total"] = x["Gold"] + x["Silver"] + x["Bronze"]
    return x


def overall_stats(df):
    medal_df = df.drop_duplicates(
        subset=["Team", "NOC", "Games", "Year", "City", "Sport", "Event", "Medal"]
    )
    return {
        "editions": int(df["Year"].unique().shape[0]),
        "cities": int(df["City"].unique().shape[0]),
        "sports": int(df["Sport"].unique().shape[0]),
        "events": int(df["Event"].unique().shape[0]),
        "athletes": int(df["Name"].unique().shape[0]),
        "nations": int(df["region"].dropna().unique().shape[0]),
    }


def data_over_time(df, col):
    """col is 'region' (nations), 'Event' or 'Name' (athletes)."""
    nt = (
        df.drop_duplicates(["Year", col])["Year"]
        .value_counts()
        .reset_index()
        .sort_values("Year")
    )
    nt.columns = ["Year", "count"]
    nt["Year"] = nt["Year"].astype(int)
    return nt


def most_successful(df, sport):
    temp_df = df.dropna(subset=["Medal"])
    if sport != "Overall":
        temp_df = temp_df[temp_df["Sport"] == sport]

    x = temp_df["Name"].value_counts().reset_index().head(15)
    x.columns = ["Name", "Medals"]
    x = x.merge(df, on="Name", how="left")[
        ["Name", "Medals", "Sport", "region"]
    ].drop_duplicates("Name")
    x = x.rename(columns={"region": "Country"})
    return x


def yearwise_medal_tally(df, country):
    temp_df = df.dropna(subset=["Medal"])
    temp_df.drop_duplicates(
        subset=["Team", "NOC", "Games", "Year", "City", "Sport", "Event", "Medal"],
        inplace=True,
    )
    new_df = temp_df[temp_df["region"] == country]
    final_df = new_df.groupby("Year").count()["Medal"].reset_index()
    return final_df


def country_event_heatmap(df, country):
    temp_df = df.dropna(subset=["Medal"])
    temp_df.drop_duplicates(
        subset=["Team", "NOC", "Games", "Year", "City", "Sport", "Event", "Medal"],
        inplace=True,
    )
    new_df = temp_df[temp_df["region"] == country]
    pt = (
        new_df.pivot_table(index="Sport", columns="Year", values="Medal", aggfunc="count")
        .fillna(0)
    )
    return pt


def most_successful_countrywise(df, country):
    temp_df = df.dropna(subset=["Medal"])
    temp_df = temp_df[temp_df["region"] == country]

    x = temp_df["Name"].value_counts().reset_index().head(10)
    x.columns = ["Name", "Medals"]
    x = x.merge(df, on="Name", how="left")[["Name", "Medals", "Sport"]].drop_duplicates(
        "Name"
    )
    return x


def age_distribution(df):
    athlete_df = df.drop_duplicates(subset=["Name", "region"])
    x1 = athlete_df["Age"].dropna().tolist()
    x2 = athlete_df[athlete_df["Medal"] == "Gold"]["Age"].dropna().tolist()
    x3 = athlete_df[athlete_df["Medal"] == "Silver"]["Age"].dropna().tolist()
    x4 = athlete_df[athlete_df["Medal"] == "Bronze"]["Age"].dropna().tolist()
    return {"Overall": x1, "Gold": x2, "Silver": x3, "Bronze": x4}


FAMOUS_SPORTS = [
    "Basketball", "Judo", "Football", "Tug-Of-War", "Swimming", "Badminton",
    "Water Polo", "Cycling", "Tennis", "Baseball", "Polo", "Volleyball",
    "Ice Hockey", "Boxing", "Shooting", "Golf", "Table Tennis",
]


def age_distribution_by_sport(df):
    athlete_df = df.drop_duplicates(subset=["Name", "region"])
    result = {}
    for sport in FAMOUS_SPORTS:
        temp = athlete_df[
            (athlete_df["Sport"] == sport) & (athlete_df["Medal"] == "Gold")
        ]["Age"].dropna().tolist()
        if len(temp) > 0:
            result[sport] = temp
    return result


def men_vs_women(df):
    athlete_df = df.drop_duplicates(subset=["Name", "region"])
    men = athlete_df[athlete_df["Sex"] == "M"].groupby("Year").count()["Name"].reset_index()
    women = athlete_df[athlete_df["Sex"] == "F"].groupby("Year").count()["Name"].reset_index()
    final = men.merge(women, on="Year", how="left")
    final.rename(columns={"Name_x": "Male", "Name_y": "Female"}, inplace=True)
    final["Female"] = final["Female"].fillna(0)
    return final


def height_weight_scatter(df, sport):
    athlete_df = df.drop_duplicates(subset=["Name", "region"]).copy()
    athlete_df["Medal"] = athlete_df["Medal"].fillna("No Medal")
    if sport != "Overall":
        athlete_df = athlete_df[athlete_df["Sport"] == sport]
    cols = ["Name", "Weight", "Height", "Medal", "Sex"]
    return athlete_df[cols].dropna(subset=["Weight", "Height"])
