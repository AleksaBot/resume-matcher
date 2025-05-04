import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud, STOPWORDS
import pandas as pd
import streamlit as st

def display_top_matches(results_df, top_n=5):
    """Display top N job matches in a styled table."""
    if results_df.empty:
        st.warning("No matches found.")
        return
    top_matches = results_df.head(top_n)[["title", "match_score"]]
    st.dataframe(top_matches.style.background_gradient(cmap="Blues").format({"match_score": "{:.2f}"}))

import textwrap

def generate_skill_wordcloud(text):
    """Generate and display a word cloud from resume text."""
    stopwords = set(STOPWORDS)
    wordcloud = WordCloud(width=800, height=400, background_color='white',
                          stopwords=stopwords, colormap='viridis').generate(text)
    plt.figure(figsize=(10, 4))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    st.pyplot(plt.gcf())
    plt.clf()
