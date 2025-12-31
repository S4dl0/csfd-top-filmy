import streamlit as st
import pandas as pd
import altair as alt

from math import floor, ceil

from altair.vegalite.v6.theme import theme

df = pd.read_json("./data/csfd_movies.json")

st.set_page_config(
    page_title="Top filmy ČSFD",
    layout="wide"

)
_sidebar1, _main, _sidebar2 = st.columns([2, 6, 2])
with _main:
    st.title("ČSFD žebříček top filmů")
    st.write("Projekt zaměřený na end-to-end analýzu nejlépe hodnocených filmů z webu ČSFD")

    _data, _ratings, _genres, _directors, _scatter, _hist = st.tabs([
        "Dataset",
        "Hodnocení",
        "Žánry",
        "Režiséři",
        "Scatter plot",
        "Histogram"
    ])

    with _data:
        st.write(f"Žebříček obsahuje {len(df)} nejlépe hodnocených filmů z webu ČSFD. " +
                 "Data pocházejí z prosince 2025.")

        st.subheader("Filtry")

        all_genres = sorted({g for genres in df["genres"] for g in genres})
        if "selected_genres" not in st.session_state:
            st.session_state.selected_genres = all_genres.copy()

        toggle = st.button("Resetovat výběr žánrů")
        if toggle:
            if len(st.session_state.selected_genres) == len(all_genres):
                st.session_state.selected_genres = []
            else:
                st.session_state.selected_genres = all_genres.copy()

        selected_genres = st.pills(
            "Žánry",
            options=all_genres,
            selection_mode="multi",
            key="selected_genres"
        )

        _col1, _col2 = st.columns(2)

        with _col1:
            rating_range = st.slider(
                "Průměrné hodnocení (%)",
                min_value=floor(df["rating_avg"].min()),
                max_value=ceil(df["rating_avg"].max()),
                value=(floor(df["rating_avg"].min()), ceil(df["rating_avg"].max()))
            )

        with _col2:
            votes_range = st.slider(
                "Počet hodnocení",
                min_value=int(df["rating_total"].min()),
                max_value=int(df["rating_total"].max()),
                value=(int(df["rating_total"].min()), int(df["rating_total"].max()))
            )

        df_filtered = df[
            df["rating_avg"].between(*rating_range)
            & df["rating_total"].between(*votes_range)
            ]

        df_filtered = df_filtered[
            df_filtered["genres"].apply(
                lambda x: any(g in x for g in selected_genres)
            )
        ]

        st.subheader("Žebříček")
        st.write(f"Zobrazeno {len(df_filtered)} záznamů")
        st.dataframe(
            df_filtered,
            hide_index=True,
            column_config=
            {
                'no': 'Pořádí',
                'title': 'Název',
                'rating_avg': 'Průměrné hodnocení',
                'rating_total': 'Počet hodnocení',
                'year': 'Rok',
                'countries': 'Země',
                'genres': 'Žánry',
                'duration': 'Délka (min)',
                'directors': 'Režie',
                'actors': 'Herci'
            },
            column_order=
            (
                'no',
                'title',
                'rating_avg',
                'rating_total',
                'duration',
                'year',
                'countries',
                'genres',
                'directors',
                'actors'
            )
        )

    with _ratings:
        st.subheader("Průměrné hodnocení a počet hodnocení podle pořadí")

        base = alt.Chart(df).encode(
            x=alt.X("no:Q", title="Pořadí v žebříčku"),
            tooltip=[
                alt.Tooltip("no:Q", title="Pořadí:"),
                alt.Tooltip("title:N", title="Název:"),
                alt.Tooltip("rating_avg:Q", title="Průměr:"),
                alt.Tooltip("rating_total:Q", title="Počet:")
            ]
        )

        rating_line = base.mark_line(color="orangered").encode(
            y=alt.Y(
                "rating_avg:Q",
                scale=alt.Scale(domain=[80, 100]),
                title="Průměrné hodnocení (%)"
            )
        )

        votes_line = base.mark_line(opacity=0.8).encode(
            y=alt.Y(
                "rating_total:Q",
                title="Počet hodnocení"
            )
        )

        chart = alt.layer(
            rating_line,
            votes_line
        ).resolve_scale(
            y="independent"
        ).properties(height=400)

        st.altair_chart(chart)

    with _genres:
        st.subheader("Porovnání jednotlivých žánrů")

        df_exploded = df.explode("genres")

        genre_stats = (
            df_exploded
            .groupby("genres")
            .agg(
                avg_rating=("rating_avg", "mean"),
                avg_votes=("rating_total", "mean"),
                avg_duration=("duration", "mean")
            )
            .reset_index()
        )

        genre_labels = {
            "avg_rating": "Hodnocení (%)",
            "avg_votes": "Počet hodnocení",
            "avg_duration": "Délka filmu (min)"
        }

        selected_g_label = st.segmented_control(
            "Zobrazit podle průměru",
            options=list(genre_labels.keys()),
            format_func=lambda x: genre_labels[x],
            selection_mode="single",
            default="avg_rating"
        )

        chart = alt.Chart(genre_stats).mark_bar().encode(
            y=alt.Y(
                "genres:N",
                sort="-x",
                title="Žánr"
            ),
            x=alt.X(
                f"{selected_g_label}:Q",
                title=genre_labels[selected_g_label]
            ),
            tooltip=[
                alt.Tooltip("genres:N", title="Žánr:"),
                alt.Tooltip(
                    f"{selected_g_label}:Q",
                    title=f"{genre_labels[selected_g_label]}:",
                    format=".2f"
                )
            ]
        ).properties(height=400)

        st.altair_chart(chart)

    with _directors:
        st.subheader("Nejlepších 10 režisérů")

        df_dir = df.explode("directors").explode("genres")

        director_stats = (
            df_dir
            .groupby("directors")
            .agg(
                avg_rating=("rating_avg", "mean"),
                total_votes=("rating_total", "sum"),
                count_movies=("title", "count"),
                avg_footage=("duration", "mean"),
                count_genres=("genres", "nunique")
            )
            .reset_index()
        )

        director_labels = {
            "avg_rating": "Hodnocení (%)",
            "total_votes": "Počet hodnocení",
            "count_movies": "Počet filmů",
            "avg_footage": "Délka filmu (min)",
            "count_genres": "Počet žánrů"
        }

        selected_d_label = st.segmented_control(
            "Zobrazit podle",
            options=list(director_labels.keys()),
            format_func=lambda x: director_labels[x],
            selection_mode="single",
            default="avg_rating"
        )

        top_directors = (
            director_stats
            .sort_values(selected_d_label, ascending=False)
            .head(10)
            .sort_values("directors")
        )

        chart = alt.Chart(top_directors).mark_bar().encode(
            y=alt.Y(
                "directors:N",
                sort="-x",
                title="Režisér"
            ),
            x=alt.X(
                f"{selected_d_label}:Q",
                title=director_labels[selected_d_label]
            ),
            tooltip=[
                alt.Tooltip("directors:N", title="Režisér:"),
                alt.Tooltip(
                    f"{selected_d_label}:Q",
                    title=f"{director_labels[selected_d_label]}:",
                    format=".2f"
                )
            ]
        ).properties(height=400)

        st.altair_chart(chart)

    with _scatter:
        st.subheader("Vliv délky filmu na hodnocení")

        chart = alt.Chart(df).mark_circle(size=80).encode(
            x=alt.X("duration:Q",
                    scale=alt.Scale(domain=[df["duration"].min(), df["duration"].max()]),
                    title="Délka filmu (min)"),
            y=alt.Y(
                "rating_avg:Q",
                scale=alt.Scale(domain=[df["rating_avg"].min(), df["rating_avg"].max()]),
                title="Průměrné hodnocení (%)"
            ),
            tooltip=[
                alt.Tooltip("title:N", title="Název:"),
                alt.Tooltip("duration:Q", title="Délka (min):"),
                alt.Tooltip("rating_avg:Q", title="Hodnocení (%):", format=".1f")
            ]
        ).properties(height=400)

        st.altair_chart(chart + chart.transform_regression("duration", "rating_avg").mark_line(color='dodgerblue'))

    with _hist:
        st.subheader("Rozložení filmů")

        hist_labels = {
            "rating_avg": "Hodnocení (%)",
            "rating_total": "Počet hodnocení",
            "duration": "Délka filmu (min)",
            "year": "Rok vydání"
        }

        selected_h_label = st.segmented_control(
            "Zobrazit podle",
            options=list(hist_labels.keys()),
            format_func=lambda x: hist_labels[x],
            selection_mode="single",
            default="rating_avg"
        )

        step_dict = {
            "rating_avg": 1,
            "rating_total": 10000,
            "duration": 15,
            "year": 5
        }

        step = step_dict.get(selected_h_label, 1)

        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X(
                f"{selected_h_label}:Q",
                bin=alt.Bin(step=step),
                title=hist_labels[selected_h_label]
            ),
            y=alt.Y(
                "count():Q",
                title="Počet filmů"
            )
        ).properties(height=400)

        st.altair_chart(chart)
