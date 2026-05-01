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

    result = evaluate(
    dataset=dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
    embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
    )

    print(f"\n  Faithfulness      : {result['faithfulness']:.2f}")
    print(f"  Answer Relevancy  : {result['answer_relevancy']:.2f}")
    print(f"  Context Precision : {result['context_precision']:.2f}")
    print(f"  Context Recall    : {result['context_recall']:.2f}")