import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

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

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    summary = llm.invoke(f"""
    You are a QA assistant. Summarize what this test does in 3-4 plain English sentences.
    Requirement: {requirement}
    Test code:
    {test_code[:2000]}
    """).content
    answer = f"This test covers: {requirement}.\n{summary}"

    ground_truth = llm.invoke(f"""
    In 2-3 sentences, describe what a good automated test for this requirement should do:
    Requirement: {requirement}
    URL: {url}
    """).content

    dataset = Dataset.from_list([{
        "question":     requirement,
        "answer":       answer,
        "contexts":     [page_html],
        "ground_truth": ground_truth,
    }])

    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=llm,
        embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
    )

    print(f"\n  Faithfulness      : {result['faithfulness']:.2f}")
    print(f"  Answer Relevancy  : {result['answer_relevancy']:.2f}")
    print(f"  Context Precision : {result['context_precision']:.2f}")
    print(f"  Context Recall    : {result['context_recall']:.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("requirement", help="e.g. 'Test login with valid credentials'")
    parser.add_argument("--test", required=True, help="Path to generated test file")
    parser.add_argument("--url", help="URL the test was generated from")
    args = parser.parse_args()
    run(args.requirement, args.test, args.url)