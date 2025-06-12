import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from textblob import TextBlob

st.title("📁 Batch Sentiment Analysis on CSV")

# File uploader
uploaded = st.file_uploader("Upload a CSV file", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)
    st.write("Preview of uploaded data:", df.head())

    # Select text column
    text_cols = df.select_dtypes(include="object").columns.tolist()
    if text_cols:
        col = st.selectbox("Select the text column to analyze", text_cols)
        if st.button("Analyze CSV Sentiment"):
            df = df.copy()
            df["polarity"] = df[col].apply(lambda t: TextBlob(str(t)).sentiment.polarity)
            df["subjectivity"] = df[col].apply(lambda t: TextBlob(str(t)).sentiment.subjectivity)
            df["sentiment_label"] = df["polarity"].apply(
                lambda v: "Positive" if v > 0 else ("Negative" if v < 0 else "Neutral")
            )
            st.success("Sentiment analysis complete 🎉")
            st.dataframe(df[[col, "polarity", "subjectivity", "sentiment_label"]])

            # Plot polarity histogram
            fig = go.Figure(go.Bar(
                x=df["sentiment_label"].value_counts().index,
                y=df["sentiment_label"].value_counts().values,
                marker_color=["green", "gray", "red"]
            ))
            fig.update_layout(title="Sentiment Distribution", xaxis_title="Sentiment", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No text (object-type) columns found in CSV.")
else:
    st.info("Upload a CSV file to begin sentiment analysis.")

    # # This is a significant architectural change.
