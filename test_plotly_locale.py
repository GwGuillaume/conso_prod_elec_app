import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from babel.dates import format_datetime

# ------------------------------------------------------------
# Bloc JS pour forcer la locale FR de Plotly et afficher la locale active
# ------------------------------------------------------------
st.markdown(
    """
    <script>
        function setPlotlyLocaleFR() {
            if (window.Plotly) {
                try {
                    Plotly.setPlotConfig({locale: 'fr'});
                    const locale = Plotly.getPlotConfig().locale;
                    console.log("Plotly locale active :", locale);
                    const div = document.getElementById("locale-info");
                    if (div) div.innerHTML = "Locale Plotly détectée : <b>" + locale + "</b>";
                } catch (e) {
                    console.log("Erreur locale :", e);
                }
            } else {
                console.log("Plotly pas encore chargé");
            }
        }
        setTimeout(setPlotlyLocaleFR, 500);
    </script>

    <div id="locale-info" style="padding:10px;color:blue;font-weight:bold;">
        Locale Plotly détectée : (chargement…)
    </div>
    """,
    unsafe_allow_html=True
)

st.title("Test locale Plotly — Mois et jours en toutes lettres (FR)")

# ---- Données simples ----
df = pd.DataFrame({
    "date": pd.date_range("2024-02-01", periods=5, freq="D"),
    "valeur": [10, 20, 15, 30, 25]
})

# ---- Formatage français complet pour hovertemplate ----
df["date_fr"] = df["date"].apply(lambda d: format_datetime(d, "EEEE d MMMM y, HH:mm", locale="fr"))

# ---- Graph Plotly ----
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["valeur"],
        mode="lines+markers",
        name="Valeur",
        hovertemplate="%{customdata}<br>Valeur : %{y}<extra></extra>",
        customdata=df["date_fr"],
    )
)

fig.update_layout(
    title="Courbe de test — format français long",
    xaxis_title="Date",
    yaxis_title="Valeur",
)

st.plotly_chart(fig, use_container_width=True)
