import streamlit as st
from FlightRadar24 import FlightRadar24API
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import airportsdata

# Initialise the API and airport database
fr_api = FlightRadar24API()
airports = airportsdata.load("IATA")

st.title("✈️ Live Flight Dashboard")
st.markdown("Tracking live flights using FlightRadar24 data")

# Fetch flights
with st.spinner("Fetching live flight data..."):
    flights = fr_api.get_flights()

# Convert to DataFrame
data = []
for f in flights:
    data.append({
        "Callsign": f.callsign,
        "Aircraft": f.aircraft_code,
        "Registration": f.registration,
        "Airline (IATA)": f.airline_iata,
        "Origin Airport": f.origin_airport_iata,
        "Destination Airport": f.destination_airport_iata,
        "Latitude": f.latitude,
        "Longitude": f.longitude,
        "Altitude (ft)": f.altitude,
        "Speed (kt)": f.ground_speed,
        "Vertical Speed": f.vertical_speed,
        "Heading": f.heading,
        "On Ground": f.on_ground,
    })

df = pd.DataFrame(data)

# ---- FILTERS (sidebar) ----
st.sidebar.header("Filters")

hide_ground = st.sidebar.checkbox("Hide on-ground aircraft", value=True)
if hide_ground:
    df = df[df["On Ground"] == 0]

aircraft_types = sorted(df["Aircraft"].dropna().unique().tolist())
selected_aircraft = st.sidebar.multiselect(
    "Filter by Aircraft Type",
    options=aircraft_types,
    default=[]
)
if selected_aircraft:
    df = df[df["Aircraft"].isin(selected_aircraft)]

# ---- METRICS ----
col1, col2, col3 = st.columns(3)
col1.metric("Total Flights", len(df))
col2.metric("Avg Altitude (ft)", f"{df['Altitude (ft)'].mean():,.0f}")
col3.metric("Avg Speed (kt)", f"{df['Speed (kt)'].mean():,.0f}")

# ---- TABS ----
tab1, tab2, tab3 = st.tabs(["Live Flights", "Route Map", "Data"])

with tab1:
    st.subheader("Live Flight Map")
    fig = px.scatter_geo(df,
        lat="Latitude",
        lon="Longitude",
        hover_name="Callsign",
        hover_data=["Aircraft", "Altitude (ft)", "Speed (kt)"],
        projection="natural earth"
    )
    st.plotly_chart(fig, use_container_width=True)


with tab2:
    st.subheader("Route Map")

    route_df = df[
        df["Origin Airport"].isin(airports) &
        df["Destination Airport"].isin(airports)
    ].copy()

    st.caption(f"Showing {len(route_df)} flights with known origin and destination")

    fig_routes = go.Figure()

    for _, row in route_df.iterrows():
        origin = airports[row["Origin Airport"]]
        destination = airports[row["Destination Airport"]]

        fig_routes.add_trace(go.Scattergeo(
            lon=[origin["lon"], destination["lon"]],
            lat=[origin["lat"], destination["lat"]],
            mode="lines",
            line=dict(width=0.5, color="royalblue"),
            opacity=0.4,
            hoverinfo="skip",
            showlegend=False
        ))

    fig_routes.add_trace(go.Scattergeo(
        lon=route_df["Longitude"],
        lat=route_df["Latitude"],
        mode="markers",
        marker=dict(size=4, color="red"),
        text=route_df["Callsign"],
        hovertemplate="<b>%{text}</b><extra></extra>",
        showlegend=False
    ))

    fig_routes.update_layout(
        geo=dict(
            projection_type="natural earth",
            showland=True,
            landcolor="lightgray",
            showocean=True,
            oceancolor="aliceblue",
            showcoastlines=True,
            coastlinecolor="white"
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=600
    )

    st.plotly_chart(fig_routes, use_container_width=True)

with tab3:
    st.subheader("Flights by Aircraft Type")
    aircraft_counts = (
        df.groupby("Aircraft")
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )
    st.dataframe(aircraft_counts, use_container_width=True)

    st.subheader("Flight Data")
    st.dataframe(df, use_container_width=True)