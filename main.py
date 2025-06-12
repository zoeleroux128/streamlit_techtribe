import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from textblob import TextBlob 
from fpdf import FPDF
import base64
import asyncio  # kept per your requirements, though not critical here
# websockets removed – not needed for this textual use case

st.title("🎯 Sentiment Analysis Dashboard")

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["timestamp", "text", "polarity", "subjectivity", "keywords"])

# --- CSV upload section ---
st.subheader("📂 Upload CSV for batch analysis")
uploaded_file = st.file_uploader("Upload a CSV file containing a 'text' column", type=["csv"])

if uploaded_file is not None:
    try:
        csv_data = pd.read_csv(uploaded_file)
        
        
        if "text" not in csv_data.columns:
            st.error("CSV must have a 'text' column.")
        else:
            if st.button("Analyze CSV Sentiment"):
                # Analyze each text row
                results = []
                for text in csv_data["text"].dropna():
                    blob = TextBlob(str(text))
                    polarity = blob.sentiment.polarity
                    subjectivity = blob.sentiment.subjectivity
                    keywords = ", ".join(blob.noun_phrases)
                    results.append({
                        "timestamp": pd.Timestamp.now(),
                        "text": text.strip(),
                        "polarity": polarity,
                        "subjectivity": subjectivity,
                        "keyword":keywords
                        

                    })
                # Append to session history
                new_df = pd.DataFrame(results)
                st.session_state.history = pd.concat([st.session_state.history, new_df], ignore_index=True)
                st.success(f"Analyzed {len(results)} rows from CSV and added to history.")
    except Exception as e:
        st.error(f"Error reading CSV: {e}")

# Text input form
user_text = st.text_area("Enter customer review / social media post:")

if st.button("Analyze Sentiment"):
    if user_text.strip():
        blob = TextBlob(user_text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        keywords = ", ".join(blob.noun_phrases)  # Extract keywords here
        timestamp = pd.Timestamp.now()
        st.session_state.history = pd.concat([
            st.session_state.history,
            pd.DataFrame({
                "timestamp": [timestamp],
                "text": [user_text.strip()],
                "polarity": [polarity],
                "subjectivity": [subjectivity],
                "keywords": [keywords]  # Correct key and value as list
            })
        ], ignore_index=True)
        label = "Positive" if polarity > 0 else "Negative" if polarity < 0 else "Neutral"
        st.success(f"Sentiment: **{label}**  |  Polarity: {polarity:.2f}  |  Subjectivity: {subjectivity:.2f}")
    else:
        st.warning("Please enter some text first.")
# Display history and trend chart
st.subheader("📈 Sentiment Trend Over Time")
if not st.session_state.history.empty:
    
    df = st.session_state.history.copy()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["timestamp"],
        y=df["polarity"],
        marker_color=df["polarity"].apply(lambda v: "green" if v > 0 else ("red" if v < 0 else "gray")),
        name="Polarity",


    ))
    fig.update_layout(
        xaxis_title="Timestamp",
        yaxis_title="Polarity (–1 to +1)",
        title="Sentiment History"

    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Sentiment distribution pie chart ---
    st.subheader("📊 Sentiment Class Distribution")

    def get_sentiment_label(p):
        if p > 0:
            return "Positive"
        elif p < 0:
            return "Negative"
        else:
            return "Neutral"

    df["sentiment"] = df["polarity"].apply(get_sentiment_label)
    sentiment_counts = df["sentiment"].value_counts().reset_index()
    sentiment_counts.columns = ["Sentiment", "Count"]

    pie_chart = go.Figure(data=[go.Pie(
        labels=sentiment_counts["Sentiment"],
        values=sentiment_counts["Count"],
        hole=0.4,  # donut-style
        marker=dict(colors=["green", "red", "gray"])
    )])

    pie_chart.update_layout(title_text="Sentiment Distribution (Pie Chart)")
    st.plotly_chart(pie_chart, use_container_width=True)

    st.dataframe(df[["timestamp", "text", "polarity", "subjectivity", "keywords"]], use_container_width=True)

      # --- Export buttons ---

    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')

    def convert_df_to_json(df):
        return df.to_json(orient="records", force_ascii=False)

    def convert_df_to_pdf(df):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        line_height = pdf.font_size * 2.5
        col_widths = [30, 80, 30, 30, 50]  # adjust as needed

        # Header
        headers = ["Timestamp", "Text", "Polarity", "Subjectivity", "Keywords"]
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], line_height, header, border=1)
        pdf.ln(line_height)

        # Rows (limit text length for PDF readability)
        max_text_len = 50
        for _, row in df.iterrows():
            pdf.cell(col_widths[0], line_height, str(row["timestamp"]), border=1)
            text = (row["text"][:max_text_len] + '...') if len(row["text"]) > max_text_len else row["text"]
            pdf.cell(col_widths[1], line_height, text, border=1)
            pdf.cell(col_widths[2], line_height, f"{row['polarity']:.2f}", border=1)
            pdf.cell(col_widths[3], line_height, f"{row['subjectivity']:.2f}", border=1)
            keywords_text = str(row["keywords"]) if pd.notna(row["keywords"]) else ""
            if len(keywords_text) > max_text_len:
                keywords_text = keywords_text[:max_text_len] + "..."
            pdf.cell(col_widths[4], line_height, keywords_text, border=1)
            pdf.ln(line_height)

        pdf_output = pdf.output(dest='S').encode('latin1')
        return pdf_output

    csv_data = convert_df_to_csv(df)
    json_data = convert_df_to_json(df)
    pdf_data = convert_df_to_pdf(df)

    st.download_button(
        label="Download data as CSV",
        data=csv_data,
        file_name="sentiment_history.csv",
        mime="text/csv"
    )

    st.download_button(
        label="Download data as JSON",
        data=json_data,
        file_name="sentiment_history.json",
        mime="application/json"
    )

    st.download_button(
        label="Download data as PDF",
        data=pdf_data,
        file_name="sentiment_history.pdf",
        mime="application/pdf"
    )

else:
    st.info("No analyses yet. Submit your first review above.")



st.markdown("""
---

### 🧠 How it works
- Uses **TextBlob** to compute **polarity** (–1 to +1) and **subjectivity** (0 to 1).  
- Plots polarity over time using **Plotly** & **pandas** for data handling.  
- Fully interactive UI via **Streamlit**.

**Tip**: Want more accuracy or nuance? Upgrade to transformer-based models (e.g., `cardiffnlp/twitter-roberta-base-sentiment`) using `transformers` and `pipeline("sentiment-analysis")`.

""")
