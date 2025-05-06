import streamlit as st
import pandas as pd
import pickle
import re
import nltk
from streamlit_option_menu import option_menu
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import plotly.graph_objs as go

# NLTK downloads
nltk.download('stopwords')
nltk.download('punkt_tab')
nltk.download('wordnet')
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# =================== THEME HANDLER ===================
def inject_fullpage_theme(mode):
    is_dark = mode == "Dark"
    bg = "#121212" if is_dark else "#f6f5f6"
    fg = "#ffffff" if is_dark else "#0e0d0e"
    card_bg = "#1e1e1e" if is_dark else "#ffffff"
    sidebar_bg = "#1c1c1c" if is_dark else "#ffffff"
    dropdown_text_color = "#ffffff" if is_dark else "#000000"
    button_bg = "#000000" if is_dark else "#e0e0e0"
    button_text = "#ffffff" if is_dark else "#000000"

    st.markdown(f"""
        <style>
        html, body, [class*="stApp"] {{
            background-color: {bg} !important;
            color: {fg} !important;
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: {sidebar_bg} !important;
            color: {fg} !important;
        }}

        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] div[role="radiogroup"] > div {{
            color: {fg} !important;
        }}

        /* Dropdown */
        section[data-testid="stSidebar"] .stSelectbox {{
            background-color: transparent !important;
        }}

        section[data-testid="stSidebar"] .stSelectbox div[role="combobox"] {{
            background-color: transparent !important;
            color: {dropdown_text_color} !important;
            border: 1px solid #777 !important;
            border-radius: 8px;
        }}

        .stSelectbox div[data-baseweb="popover"] {{
            background-color: {sidebar_bg} !important;
            color: {dropdown_text_color} !important;
        }}

        /* Buttons */
        button[kind="primary"], .stButton>button {{
            background-color: {button_bg} !important;
            color: {button_text} !important;
            border: 1px solid #ffffff33;
            border-radius: 6px;
            padding: 0.4rem 0.9rem;
        }}

        button[kind="primary"]:hover, .stButton>button:hover {{
            background-color: #333333 !important;
            color: #ffffff !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    return bg, fg





# =================== TEXT CLEANER ===================
def preprocess_text(text):
    text = str(text).lower()
    text = re.sub(r'https?://\S+|www\.\S+|\[.*?\]|[^a-zA-Z\s]+|\w*\d\w*', ' ', text)
    text = re.sub(r'\n', ' ', text)
    stop_words = set(stopwords.words("english"))
    words = text.split()
    filtered_words = [word for word in words if word not in stop_words]
    tokens = nltk.word_tokenize(' '.join(filtered_words).strip())
    lemmatizer = WordNetLemmatizer()
    lem_tokens = [lemmatizer.lemmatize(token) for token in tokens]
    return ' '.join(lem_tokens)

# =================== VISUALIZER ===================
def display_result(result):
    emojis = {
        "Positive": ":smile:",
        "Negative": ":pensive:",
        "Neutral": ":neutral_face:"
    }
    st.subheader(f"{result[0]} {emojis.get(result[0], '')}")

def classify_multiple(dataframe, bg, fg):
    st.write(f"There are a total of {dataframe.shape[0]} reviews given")

    dataframe.columns = ["Review"]
    data = dataframe.copy()
    data["Review"] = data["Review"].apply(preprocess_text)

    sentiments = []
    counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for i in range(data.shape[0]):
        rev = vect.transform([data["Review"].iloc[i]])
        res = model.predict(rev)[0]
        sentiments.append(res)
        counts[res] += 1

    x = list(counts.keys())
    y = list(counts.values())

    # Bar Plot
    fig = go.Figure(data=[go.Bar(name='Reviews', x=x, y=y, marker_color='#8d7995')])
    fig.update_layout(title='Sentiment Distribution',
                      xaxis_title='Sentiment',
                      yaxis_title='Count',
                      plot_bgcolor=bg,
                      paper_bgcolor=bg,
                      font=dict(color=fg))
    st.plotly_chart(fig, use_container_width=True)

    # Word Cloud
    wordcloud_data = " ".join(dataframe["Review"].astype(str))
    wordcloud = WordCloud(width=800, height=400, max_words=100,
                          background_color=bg,
                          colormap='viridis').generate(wordcloud_data)
    fig_wordcloud = plt.figure(figsize=(8, 4), facecolor=bg)
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.title('Word Cloud - Most Frequent Words', color=fg)
    plt.gca().set_facecolor(bg)
    st.pyplot(fig_wordcloud, use_container_width=True)

    dataframe["Sentiment"] = sentiments
    st.dataframe(dataframe, use_container_width=True)

# =================== MAIN ===================
def main():
    st.set_page_config(page_title="Amazon Review Analyzer", layout="wide")

    # Sidebar: Theme Switch
    mode = st.sidebar.radio("Choose Theme", ("Light", "Dark"))
    bg_color, text_color = inject_fullpage_theme(mode)

      # Add a title heading
    st.title("E commerce Product Review Sentiment Analysis Project")

    # Navbar
    selected = option_menu(None, ["Single Review", "Bulk Reviews"],
                           icons=['chat-left-text', 'file-earmark-spreadsheet'],
                           menu_icon="cast", default_index=0, orientation="horizontal")

    # Load Models
    with open("models.p", 'rb') as mod:
        data = pickle.load(mod)
    global vect, model
    vect = data['vectorizer']
    classifier = st.sidebar.selectbox("Classifier:", ["Logistic Regression", "SVM"])
    model = data["logreg"] if classifier == "Logistic Regression" else data["svm"]

    st.sidebar.markdown(f"**Using:** {classifier}")

    if selected == "Single Review":
        st.title("📝 Analyze a Single Amazon Review")
        review = st.text_area("Enter your review:")
        if st.button("Analyze"):
            clean = preprocess_text(review)
            transformed = vect.transform([clean])
            result = model.predict(transformed)
            display_result(result)

    elif selected == "Bulk Reviews":
        st.title("📦 Analyze Multiple Amazon Reviews (CSV)")
        uploaded_file = st.file_uploader("Upload a CSV with a single `Review` column", type="csv")
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            if df.shape[1] != 1:
                st.error("❌ CSV should contain only one column named `Review`.")
            else:
                classify_multiple(df, bg_color, text_color)

    # Footer
    st.markdown(f"""
    <hr style="border: 0.5px solid gray;">
    <div style='text-align: center; color: gray; font-size: small;'>
        Made with ❤️ - <a href="https://github.com/SayanRony/Amazon-Reviews-Sentiment-Analysis.git" style="color:{text_color};" target="_blank">Group 44 Final Year Project 
        </a>
    </div>
    <div style='text-align: center; color: gray; font-size: small;'>
        Made by <a href="https://github.com/SayanRony/Amazon-Reviews-Sentiment-Analysis.git" style="color:{text_color};" target="_blank">Nilambar Giri , Pallav Bag , Sayani Jana , Sayantan Chakrbarti , Srinjoy Das
        </a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
