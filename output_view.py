from urllib.parse import unquote

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

df_data = pandas.DataFrame()
for summary in response.json()["grouped_distributional_summaries"]:
    summary_type = [
        "inputID",
        "instanceID",
        "versionID",
    ]  # get the distributional summaries by inputID, instanceID, and versionID
    if all(key in summary["group_keys"] for key in summary_type):
        metadata = dict(zip(summary["group_keys"], summary["group_values"]))
        values = dict(zip(summary["indicator_keys"], "indicator_distributions"))

        for indicator in summary["indicator_keys"]:
            data = {
                "inputID": metadata.get("inputID"),
                "instanceID": metadata.get("instanceID"),
                "versionID": metadata.get("versionID"),
                "indicator": indicator,
            }
            data["min"] = summary["indicator_distributions"][indicator]["min"]
            data["max"] = summary["indicator_distributions"][indicator]["max"]
            data["count"] = summary["indicator_distributions"][indicator]["count"]
            data["mean"] = summary["indicator_distributions"][indicator]["mean"]
            data["std"] = summary["indicator_distributions"][indicator]["std"]
            data["shifted_geometric_mean_value"] = summary["indicator_distributions"][
                indicator
            ]["shifted_geometric_mean"]["value"]
            data["shifted_geometric_mean_shift"] = summary["indicator_distributions"][
                indicator
            ]["shifted_geometric_mean"]["shift"]
            data["p01"] = summary["indicator_distributions"][indicator]["percentiles"][
                "p01"
            ]
            data["p05"] = summary["indicator_distributions"][indicator]["percentiles"][
                "p05"
            ]
            data["p10"] = summary["indicator_distributions"][indicator]["percentiles"][
                "p10"
            ]
            data["p25"] = summary["indicator_distributions"][indicator]["percentiles"][
                "p25"
            ]
            data["p50"] = summary["indicator_distributions"][indicator]["percentiles"][
                "p50"
            ]
            data["p75"] = summary["indicator_distributions"][indicator]["percentiles"][
                "p75"
            ]
            data["p90"] = summary["indicator_distributions"][indicator]["percentiles"][
                "p90"
            ]
            data["p95"] = summary["indicator_distributions"][indicator]["percentiles"][
                "p95"
            ]
            data["p99"] = summary["indicator_distributions"][indicator]["percentiles"][
                "p99"
            ]
            df_data = df_data.append(data, ignore_index=True)

        st.wrie(df_data)
