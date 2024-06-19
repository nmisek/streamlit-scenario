from urllib.parse import unquote

import altair as alt
import pandas
import requests as req
import streamlit as st

from token_handler import init_auth_state, sendTokenRefreshMessageToParent

st.set_page_config(layout="wide")

query_params = st.query_params

app_id = query_params.get("app_id")
batch_id = query_params.get("batch_id")
api_base_url = unquote(query_params.get("url", ""))

init_auth_state()

error = False

if app_id is None or app_id == "":
    app_id = "temp-demand-forecast"

if batch_id is None or batch_id == "":
    batch_id = "sdfsdfs"

if api_base_url == "" or api_base_url is None:
    api_base_url = "https://api.cloud.nextmv.io"

if error:
    st.stop()

headers = st.session_state.headers

results_url = f"{api_base_url}/v1/applications/{app_id}/experiments/batch/{batch_id}"
response = req.get(results_url, headers=headers)

if response.status_code != 200:
    st.error(f"Error: {response.text}")
    st.stop()
if (
    response.status_code == 403 or response.status_code == 401
) and st.session_state.get("api_key") == None:
    sendTokenRefreshMessageToParent()
    st.stop()

if response.status_code != 200:
    st.error(f"Error: {response.text}")
    st.stop()

results = response.json()

# convert the results to a pandas dataframe
# loop through the grouped distributional summaries and append to a df
df = pandas.DataFrame()
summaries = results["grouped_distributional_summaries"]
st.write(summaries)
st.write(type(summaries))

for key, value in summaries.items():
    st.write(f"Key: {key}")
    st.write(f"Value: {value}")

    scatter_plot = (
        alt.Chart(df)
        .mark_circle()
        .encode(
            x="count",
            y="forecast",
            color=alt.Color("approach", scale=alt.Scale(scheme="category10")),
            tooltip=["count", "forecast", "approach"],
        )
    )

# add line y = x
line = (
    alt.Chart(pandas.DataFrame({"x": [df["count"].min(), df["count"].max()]}))
    .mark_line(color="black")
    .encode(x=alt.X("x", title="Actuals"), y=alt.Y("x", title="Forecasts"))
)

# widen plot
chart = alt.layer(scatter_plot, line).properties(width=800).interactive()
st.altair_chart(chart)

# compute the residuals
df["residual"] = df["count"] - df["forecast"]

# histogram of the residuals colored by approach
bin_size = st.slider(
    "Select bin size for histogram", min_value=1, max_value=100, value=20
)

order = sorted(df["approach"].unique(), key=lambda x: (x == "ensemble", x))

# Create the histogram
histogram = (
    alt.Chart(df)
    .mark_bar(opacity=0.75)
    .encode(
        x=alt.X("residual", bin=alt.Bin(step=bin_size), title="Residuals"),
        y="count()",
        color=alt.Color("approach", scale=alt.Scale(scheme="category10")),
        order=alt.Order("approach", sort="ascending"),
    )
)

if "ensemble" in df["approach"].values:
    # Create a histogram for the 'ensemble' approach with a black outline
    histogram_ensemble = (
        alt.Chart(df[df["approach"] == "ensemble"])
        .mark_bar(color="transparent", stroke="black", strokeWidth=2)
        .encode(
            alt.X("residual", bin=alt.Bin(step=bin_size)),
            alt.Y("count()"),
        )
    )
    histogram = alt.layer(histogram, histogram_ensemble)

histogram = histogram.properties(width=800)
st.altair_chart(histogram)
