Sentiment Analysis Dashboard
Overview
This is an interactive Sentiment Analysis Dashboard built with Streamlit. It allows users to upload CSV files or input text directly to analyze the sentiment of customer reviews or social media posts. The dashboard computes polarity, subjectivity, and extracts keywords from the text using TextBlob. Results are visualized with Plotly charts and can be exported in CSV, JSON, or PDF formats.

Features
Batch sentiment analysis of CSV files containing a text column

Single text input analysis for instant feedback

Extraction of keywords (noun phrases) from text

Visualize sentiment polarity trends over time with interactive bar charts

Sentiment class distribution displayed as a pie chart (Positive, Negative, Neutral)

Data export options: CSV, JSON, and PDF with formatted tables

History of analyzed text stored within the session

Installation
Clone this repository:

bash
Copy
Edit
git clone https://github.com/your-username/sentiment-analysis-dashboard.git
cd sentiment-analysis-dashboard
Create and activate a Python environment (recommended):

bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install required packages:

bash
Copy
Edit
pip install -r requirements.txt
(Create a requirements.txt with the needed libs: streamlit, pandas, textblob, plotly, fpdf)

Download TextBlob corpora (if not already installed):

bash
Copy
Edit
python -m textblob.download_corpora
Usage
Run the Streamlit app:

bash
Copy
Edit
streamlit run main.py
The app will open in your browser. You can:

Upload a CSV file containing a text column to analyze multiple entries at once.

Enter individual text snippets in the text area for quick sentiment and keyword extraction.

View interactive charts showing sentiment trends and distributions.

Download the full analysis history in CSV, JSON, or PDF formats.

Code Structure
main.py: Main Streamlit app containing all logic and UI components.

Uses TextBlob for sentiment and keyword extraction.

Plotly for interactive visualizations.

FPDF for generating PDF reports.

Future Improvements
Integrate transformer-based sentiment models (e.g., HuggingFace transformers) for improved accuracy.

Enhance keyword extraction with NLP libraries like SpaCy or YAKE.

Support more file formats (Excel, JSON).

Add user authentication and persistent storage.

License
This project is licensed under the MIT License.

Acknowledgments
Streamlit

TextBlob

Plotly

FPDF


