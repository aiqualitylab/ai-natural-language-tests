
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import argparse

import requests
from datasets import Dataset
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

def run(requirement, test_file, url):
    # Step 1: fetch page HTML as context
    page_html = requests.get(url, timeout=10).text[:4000] if url else "No context."

    # Step 2: read the generated test file
    test_code = open(test_file).read()

    # initialise LLM once, reuse below
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Step 3: answer must directly respond to the requirement using page HTML
    answer_prompt = ChatPromptTemplate.from_template(
        """
You are a QA assistant. Answer this question directly in 2-3 sentences:

Question: {requirement}

Use only what is visible in this page HTML to support your answer.
Start your answer with words from the question itself.

Page HTML:
{page_html_sample}
"""
    )
    answer_chain = answer_prompt | llm | StrOutputParser()
    answer = answer_chain.invoke({"requirement": requirement, "page_html_sample": page_html[:2000]})

    # Step 4: ground truth = what the page provides relevant to the requirement
    ground_truth_prompt = ChatPromptTemplate.from_template(
        """
In 2-3 sentences, describe only what a user can observe on this page that is relevant to: {requirement}
Base your answer only on what would be visible on the page at {url}.
Keep it factual and simple.
"""
    )
    ground_truth_chain = ground_truth_prompt | llm | StrOutputParser()
    ground_truth = ground_truth_chain.invoke({"requirement": requirement, "url": url})

    # Step 5: build Ragas dataset
    dataset = Dataset.from_list([{
        "question":     requirement,
        "answer":       answer,
        "contexts":     [page_html],
        "ground_truth": ground_truth,
    }])

    # Step 6: run evaluation
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=llm,
        embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
    )

    # Step 7: print scores to console
    scores = result.to_pandas()
    print(f"\n  Faithfulness      : {scores['faithfulness'].mean():.2f}")
    print(f"  Answer Relevancy  : {scores['answer_relevancy'].mean():.2f}")
    print(f"  Context Precision : {scores['context_precision'].mean():.2f}")
    print(f"  Context Recall    : {scores['context_recall'].mean():.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("requirement", help="e.g. 'Test login with valid credentials'")
    parser.add_argument("--test", required=True, help="Path to generated test file")
    parser.add_argument("--url", help="URL the test was generated from")
    args = parser.parse_args()
    run(args.requirement, args.test, args.url)