import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import json, asyncio, argparse
from ragas.metrics.collections import RougeScore, NonLLMStringSimilarity


# Load all test samples from the JSON file
def load_samples(path):
    return json.load(open(path))


# Score one sample using ROUGE and SIM
async def score_one(response, reference):
    rouge = await RougeScore().ascore(response=response, reference=reference)
    sim   = await NonLLMStringSimilarity().ascore(response=response, reference=reference)
    return round(rouge.value, 2), round(sim.value, 2)


# Run evaluation on all samples
async def run(path):
    samples = load_samples(path)
    all_scores = []

    for sample in samples:
        rouge, sim = await score_one(sample["response"], sample["reference"])
        avg = round((rouge + sim) / 2, 2)
        all_scores.append(avg)
        print(sample["name"], "→ ROUGE:", rouge, " SIM:", sim, " AVG:", avg)

    print("\n  Overall Average:", round(sum(all_scores) / len(all_scores), 2))


# Entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="test_dataset.json")
    asyncio.run(run(parser.parse_args().dataset))