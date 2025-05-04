import os
import pandas as pd
from pdfminer.high_level import extract_text

def extract_resume_text(pdf_file):
    return extract_text(pdf_file)

def parse_jobs_csv(csv_file):
    return pd.read_csv(csv_file)
