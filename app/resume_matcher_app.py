import streamlit as st
import sys
import os
import tempfile
import pandas as pd
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.parser import extract_resume_text, parse_jobs_csv
from src.matcher import match_resume_to_jobs
from src.visualizer import display_top_matches
import tempfile

st.set_page_config(page_title="AI Resume Matcher", page_icon="🤖", layout="wide")

st.markdown("""
# 🤖 AI Resume Matcher
Compare your resume to job descriptions using Natural Language Processing (NLP).
Upload a PDF resume and a CSV of job postings — or scrape live job listings!
""")

with st.expander("📄 Upload Files", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        resume_file = st.file_uploader("Upload Your Resume (PDF)", type=["pdf"])
    with col2:
        jobs_file = st.file_uploader("Upload Job Descriptions (CSV)", type=["csv"])

# --- Scraping Utilities ---
def scrape_python_jobs(query):
    try:
        url = f"https://www.python.org/jobs/?q={query.replace(' ', '+')}"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        listings = soup.select("ul.list-recent-jobs li")
        scraped_jobs = []
        for i, job in enumerate(listings):
            title = job.select_one("h2 a").text.strip() if job.select_one("h2 a") else ""
            desc = job.select_one(".listing-summary").text.strip() if job.select_one(".listing-summary") else ""
            scraped_jobs.append({"job_id": i + 1, "title": title, "description": desc})
        return scraped_jobs
    except Exception as e:
        st.error(f"Failed to scrape Python.org: {e}")
        return []

def scrape_weworkremotely_jobs(keyword):
    try:
        url = "https://weworkremotely.com/categories/remote-programming-jobs"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        job_sections = soup.select("section.jobs article ul li")
        jobs = []
        for i, li in enumerate(job_sections):
            title_tag = li.find("span", class_="title")
            company_tag = li.find("span", class_="company")
            title = title_tag.text.strip() if title_tag else f"Job {i+1}"
            company = company_tag.text.strip() if company_tag else "Unknown"
            jobs.append({"job_id": i + 1, "title": f"{title} at {company}", "description": title})
        return jobs
    except Exception as e:
        st.error(f"Failed to scrape We Work Remotely: {e}")
        return []

def scrape_remoteok_jobs(keyword):
    try:
        url = f"https://remoteok.com/remote-{keyword.replace(' ', '-')}-jobs"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        jobs = []
        listings = soup.find_all("tr", class_="job")
        for i, job in enumerate(listings):
            title_tag = job.find("h2")
            company_tag = job.find("h3")
            title = title_tag.text.strip() if title_tag else f"Job {i+1}"
            company = company_tag.text.strip() if company_tag else "Unknown"
            jobs.append({"job_id": i + 1, "title": f"{title} at {company}", "description": title})
        return jobs
    except Exception as e:
        st.error(f"Failed to scrape Remote OK: {e}")
        return []

# --- Skill WordCloud ---
def generate_skill_wordcloud(text):
    stopwords = set(STOPWORDS)
    wordcloud = WordCloud(width=800, height=400, background_color='white',
                          stopwords=stopwords, colormap='viridis').generate(text)
    plt.figure(figsize=(10, 4))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    st.pyplot(plt.gcf())
    plt.clf()

with st.expander("🌐 Or Scrape Jobs from the Web"):
    source = st.selectbox("Source", ["Python.org", "We Work Remotely", "Remote OK"])

    common_keywords = ["developer", "software engineer", "data analyst", "machine learning", "python", "backend", "frontend"]
    selected = st.selectbox("Choose a common job keyword", common_keywords)
    custom = st.text_input("Or type a custom job keyword")
    keyword = custom if custom else selected

    location = st.text_input("Location (for future use)", value="Chicago")
    if st.button("Scrape Jobs") and keyword:
        try:
            if source == "Python.org":
                jobs_df = pd.DataFrame(scrape_python_jobs(keyword))
            elif source == "We Work Remotely":
                jobs_df = pd.DataFrame(scrape_weworkremotely_jobs(keyword))
            elif source == "Remote OK":
                jobs_df = pd.DataFrame(scrape_remoteok_jobs(keyword))
            else:
                jobs_df = pd.DataFrame()
            st.session_state["scraped_jobs"] = jobs_df
            st.success(f"Scraped {len(jobs_df)} jobs from {source}")
            st.dataframe(jobs_df)
        except Exception as scrape_error:
            st.error(f"An error occurred during scraping: {scrape_error}")

filter_keyword = st.text_input("🔍 Filter jobs by keyword")

if resume_file:
    job_source = st.radio("Job Source", ["Uploaded CSV", "Scraped Jobs"])
    if job_source == "Uploaded CSV" and not jobs_file:
        st.warning("Please upload a CSV file containing job descriptions.")
    elif job_source == "Scraped Jobs" and "scraped_jobs" not in st.session_state:
        st.warning("Please scrape jobs from the web first.")
    else:
        with st.spinner("Processing..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(resume_file.read())
                resume_text = extract_resume_text(tmp.name)
            if job_source == "Uploaded CSV":
                jobs_df = parse_jobs_csv(jobs_file)
            else:
                jobs_df = st.session_state["scraped_jobs"]
            if filter_keyword:
                jobs_df = jobs_df[jobs_df['description'].str.contains(filter_keyword, case=False, na=False)]
            results_df = match_resume_to_jobs(resume_text, jobs_df)
            results_df = results_df.sort_values(by="match_score", ascending=False)

            st.markdown("## 📊 Top Matches")
            display_top_matches(results_df)

            if not results_df.empty:
                st.metric("Top Score", f"{results_df['match_score'].iloc[0]:.2f}")

            st.markdown("## ☁️ Skill Word Cloud from Resume")
            generate_skill_wordcloud(resume_text)

            st.download_button("Download Results", results_df.to_csv(index=False), "matches.csv", "text/csv")
else:
    st.info("Upload a resume and jobs file or scrape job listings.")
