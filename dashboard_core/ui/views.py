"""
View components for rendering tables and charts in the dashboard.

This module provides functions to render:
- Run tables
- PB progression charts
- Time improvement summaries
- WR count
- Community overview charts
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from constants import CONFIG
from dashboard_core.utils import format_time_seconds, generate_time_axis_ticks


def render_table(table_df):
    """
    Render a display-ready table from `table_df`.
    
    Expects `table_df` to include a formatted `"time_fmt"` column and `"place"`.
    Does not mutate the passed DataFrame.

    :param table_df: prepared table DataFrame
    """
    if table_df.empty:
        st.warning("No data available for this selection.")
        return None
    
    table_cols = ["place", "player_name", "time_fmt", "note_name", "date", "weblink", "id"]
    table_cols = [c for c in table_cols if c in table_df.columns]
    table_df = table_df[table_cols].rename(
        columns={
            "place": "Place",
            "player_name": "Player",
            "time_fmt": "Time",
            "note_name": "Note",
            "date": "Date",
            "weblink": "Weblink"
        }
    ).reset_index(drop=True)

    table_df.drop(columns=["id"], errors="ignore", inplace=True)

    with st.container(border=True):
        st.dataframe(
            table_df,
            hide_index=True,
            column_config={
                "Date": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Weblink": st.column_config.LinkColumn()
            },
        )
    return None


def render_chart(fig):
    """Render a Plotly figure with the app's standard configuration.
    Does nothing if `fig` is None.
    """
    with st.container(border=True):
        if fig:
            st.plotly_chart(fig, config=CONFIG)
            

def plot_pb_progression(chart_df, trace_col, pb_char_note_label):
    """
    Personal Best Progression plot.

    :param chart_df: DataFrame with `"submitted"`, `"date"`, `"primary_t"`
    :param trace_col: column used to group traces (ex: `"player_name"`)
    :param pb_char_note_label: label for character-note traces
    :return: Plotly Figure (`fig`) or `None` when no data
    """
    if chart_df.empty:
        st.warning("No PB data for this selection.")
        return None

    plot_df = chart_df.sort_values(by=["submitted"]).copy()

    # Compute PB per trace
    plot_df["pb"] = plot_df.groupby(trace_col, sort=False, observed=False)["primary_t"].cummin()
    pb_df = plot_df[["date", "pb", trace_col]].reset_index(drop=True)
    if pb_df["pb"].isna().all():
        st.warning("No PB data for this selection.")
        return None

    pb_df["pb_format"] = pb_df["pb"].apply(format_time_seconds)

    fig = px.line(
        pb_df, 
        x="date", 
        y="pb", 
        color=trace_col, 
        markers=True, 
        labels=pb_char_note_label,
        title="Personal Best Progression",
    )
    
    # Customize hover to show formatted PB time
    hover_prefix = pb_char_note_label if pb_char_note_label else "Player"
    for trace in fig.data:
        name = trace.name
        sub = pb_df[pb_df[trace_col] == name].set_index("date")
        xvals = trace.x
        custom = sub.reindex(xvals)["pb_format"].to_numpy().reshape(-1, 1)
        trace.customdata = custom
        trace.hovertemplate = (
            f"{hover_prefix}: {name}<br>"
            "Time: %{customdata[0]}<br>"
            "Date: %{x|%d/%m/%Y}<extra></extra>"
        )

    tickvals, ticktext = generate_time_axis_ticks(pb_df["pb"].values)
    fig.update_yaxes(
        title="Time",
        tickmode="array",
        tickvals=tickvals,
        ticktext=ticktext,
        automargin=True,
    )
    fig.update_xaxes(title="Date")
    fig.update_layout(
        legend_title_text=pb_char_note_label or "Player",
        dragmode="pan",
        margin=dict(l=0, r=0, t=35, b=0),
        hoverlabel=dict(font_size=16),
        height=600,
    )
    return fig


def plot_time_improvement(chart_df):
    """Plot total and per-run time improvements for players.

    :param chart_df: DataFrame with `"primary_t"`, `"submitted"`, `"player_name"`
    :return: Plotly Figure (`fig`) or `None` when insufficient data
    """
    if "primary_t" not in chart_df.columns or chart_df["primary_t"].isna().all():
        st.warning("No times available for time improvement calculation.")
        return None
    
    if chart_df.groupby("player_name").size().max() <= 1:
        st.info("Not enough runs to compute improvements for the selected parameters.")
        return None

    # Total improvement per player
    player_max_time = chart_df.groupby("player_name")["primary_t"].max()
    chart_df["total_improvement"] = chart_df["player_name"].map(player_max_time) - chart_df["primary_t"]

    # Per-run improvements
    chart_df.sort_values(["player_name", "submitted"], inplace=True)
    chart_df["previous_run_time"] = chart_df.groupby("player_name")["primary_t"].shift(1)
    chart_df["per_run_improvement"] = (chart_df["previous_run_time"] - chart_df["primary_t"]).clip(lower=0.0).fillna(0.0)
    
    chart_df["prev_run_time_fmt"] = chart_df["previous_run_time"].apply(format_time_seconds)
    chart_df["per_run_improv_fmt"] = chart_df["per_run_improvement"].apply(format_time_seconds)

    # Text for bar hover
    total_by_player = (
        chart_df.groupby("player_name", sort=False)["total_improvement"].max().reset_index()
    )
    # Order players by total improvement for bar display
    total_by_player = total_by_player.sort_values("total_improvement", ascending=True).reset_index(drop=True)
    total_text = total_by_player["total_improvement"].map(format_time_seconds)
    players_order = total_by_player["player_name"].tolist()
    
    fig = go.Figure()

    # Horizontal bars: total improvement
    # Use ordered player names as y-values
    fig.add_trace(
        go.Bar(
            x=total_by_player["total_improvement"],
            y=total_by_player["player_name"],
            orientation="h",
            name="Total Improvement",
            text=total_text,
            textposition="auto",
            hovertemplate="Player: %{y}<br>Total Improvement: %{text}<extra></extra>",
            opacity=0.6,
        )
    )

    # Scatter markers: per-run improvements
    for player in players_order:
        player_runs = chart_df[chart_df["player_name"] == player]
        if player_runs.empty:
            continue
        
        custom_cols = ["time_fmt", "prev_run_time_fmt", "per_run_improv_fmt", "date_fmt"]
        fig.add_trace(
            go.Scatter(
                x=player_runs["per_run_improvement"],
                y=player_runs["player_name"],
                mode="markers",
                marker=dict(symbol="circle", size=10, line=dict(color="black")),
                name=f"{player} runs",
                customdata=player_runs[custom_cols].values,
                hovertemplate=(
                    "Player: %{y}<br>"
                    "Run Time: %{customdata[0]}<br>"
                    "Previous Run Time: %{customdata[1]}<br>"
                    "Improvement: %{customdata[2]}<br>"
                    "Date: %{customdata[3]}<extra></extra>"
                ),
                showlegend=False,
            )
        )

    tickvals, ticktext = generate_time_axis_ticks(total_by_player["total_improvement"])
    fig.update_xaxes(title="Time Improvement", tickmode="array", tickvals=tickvals, ticktext=ticktext)
    fig.update_yaxes(title="Player", categoryorder="array", categoryarray=players_order)
    fig.update_layout(
        dragmode="pan", 
        legend_title_text="Legend", 
        template="plotly_white", 
        margin=dict(l=0, r=0, t=35, b=0),
        font=dict(size=16),
        hoverlabel=dict(font_size=15),
        height=600,
    )
    return fig


def plot_wr_count(df):
    """
    Create a donut of WR counts from a DataFrame with competition-style places.
    Uses precomputed 1st-place runs.
    
    :param df: DataFrame expected to contain a `"place"` column
    :return: Plotly Figure (`fig`)
    """
    wr_holders = df[df["place"] == 1]
    counts = wr_holders.groupby("player_name").size().reset_index(name="wr_count")
    total_wr = counts["wr_count"].sum()

    fig = px.pie(
        counts,
        names="player_name",
        values="wr_count",
        hole=0.25,
        title="Current WR Counts",
        labels={"player_name": "Player", "wr_count": "WR count"},
    )

    fig.update_traces(textinfo="label+percent",
        hovertemplate="%{label}<br>WRs: %{value}<br>Percent: %{percent}",
        automargin=True
    )
    
    fig.update_layout(
        annotations=[dict(text=f"Total<br>{total_wr}", x=0.5, y=0.5, showarrow=False)],
        margin=dict(l=0, r=0, t=30, b=0),
        font=dict(size=17),
        hoverlabel=dict(font_size=16),
        height=600,
            legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.2,
        xanchor="center",
        x=0.5
    )
    )
    return fig


def render_community_overview(df):
    """
    Render community-level summary charts and stats.

    Produces the following charts:
    - Runs Submitted Per Month
    - Most played level/category
    - Runs per category (treemap)
    
    :param df: DataFrame of runs
    """
    st.subheader("Community Overview")
    
    # Runs submitted per month
    with st.expander("Runs Submitted Per Month", expanded=True):
        runs_over_time = (
            df.assign(month=df["date"].dt.to_period("M").dt.to_timestamp())
            .groupby("month", observed=False)
            .size()
            .reset_index(name="Runs")
        )

        fig1 = px.bar(runs_over_time, x="month", y="Runs", text="Runs")
        
        fig1.update_xaxes(title="Month", dtick="M1", tickformat="%b %Y")
        month_labels = runs_over_time["month"].dt.strftime("%b %Y").to_numpy().reshape(-1, 1)
        
        fig1.update_traces(
            textposition="outside",
            customdata=month_labels,
            hovertemplate="%{customdata[0]}: %{y} runs<extra></extra>",
        )

        # Add character traces for their respective runs over time
        months = runs_over_time["month"]
        display_chars = (
            df["character_name"].dropna().value_counts().index.tolist()
        )
        if display_chars:
            char_month = (
                df.assign(month=df["date"].dt.to_period("M").dt.to_timestamp())
                .groupby(["month", "character_name"], observed=False)
                .size()
                .reset_index(name="Runs")
            )
            
            for char in display_chars:
                char_timeseries = (
                    char_month[char_month["character_name"] == char]
                    .set_index("month")["Runs"]
                    .reindex(months)
                    .fillna(0)
                )
                
                fig1.add_trace(
                    go.Scatter(
                        x=months,
                        y=char_timeseries.values,
                        mode="lines+markers",
                        name=str(char),
                        hovertemplate=f"Character: {char}<br>Runs: %{'{y}'}<extra></extra>",
                    )
                )

        fig1.update_layout(
            legend_title_text="Character",
            margin=dict(l=0, r=0, t=35, b=0),
            dragmode="pan",
            height=600,
            font=dict(size=14),
            hoverlabel=dict(font_size=16),
        )
        st.plotly_chart(fig1, config=CONFIG)

    # Most played level/category
    with st.expander("Most Played Level/Category", expanded=True):
        popularity = (
            df.groupby(["level_name", "category_name"], observed=False)
            .size()
            .reset_index(name="Runs")
            .sort_values("Runs", ascending=False)
        )

        # Combined label for display
        popularity["Level/Category"] = (
            popularity["level_name"].astype(str)
            + " (" 
            + popularity["category_name"].astype(str) 
            + ")"
        )
        top = popularity.head(15)
        fig2 = px.bar(
            top,
            x="Runs",
            y="Level/Category",
            orientation="h",
            template="seaborn",
        )
        fig2.update_traces(
            hovertemplate="%{label}<br>Runs: %{value}<br>"
        )
        fig2.update_yaxes(autorange="reversed") 
        fig2.update_layout(
            height=600,
            margin=dict(l=0, r=0, t=35, b=0),
            hovermode="closest",
            dragmode= "pan",
        )
        st.plotly_chart(fig2, config=CONFIG)

    # Most played category
    with st.expander("Most Played Category", expanded=True):
        category_counts = df.groupby("category_name", observed=False).size().reset_index(name="Runs")

        fig3 = go.Figure(
            go.Treemap(
                labels=category_counts["category_name"],
                parents=[""] * len(category_counts),
                values=category_counts["Runs"],
                marker=dict(
                    colors=category_counts["Runs"], 
                    colorscale="cividis_r", 
                    pad=dict(t=10),
                ),
                texttemplate="Category: %{label}<br>Runs: %{value}<br>% of Total Runs: %{percentEntry:.2%}",
                textfont=dict(size=18),
                textposition="middle center",
                hovertemplate=(
                    "Category: %{label}<br>" +
                    "Runs: %{value}<br>" +
                    "% of total runs: %{percentEntry:.2%}<extra></extra>"
                )
            )
        )
        fig3.update_layout(
            title=f"Runs per Category (Total Runs: {len(df)})",
            margin=dict(l=0, r=0, t=30, b=0),
            height=600,
            hoverlabel=dict(font_size=17),
        )
        st.plotly_chart(fig3)
