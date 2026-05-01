import os, requests, argparse
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

def run(requirement, test_file, url):
    page_html = requests.get(url, timeout=10).text[:4000] if url else "No context."

    test_code = open(test_file).read()

    dataset = Dataset.from_list([{
        "question":     requirement,  
        "answer":       test_code,    
        "contexts":     [page_html],  
        "ground_truth": requirement, 
    }])