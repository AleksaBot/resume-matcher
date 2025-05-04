from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def match_resume_to_jobs(resume_text, jobs_df):
    documents = [resume_text] + jobs_df['description'].astype(str).tolist()
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)
    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    jobs_df['match_score'] = similarities
    return jobs_df.sort_values(by='match_score', ascending=False)
