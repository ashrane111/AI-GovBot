import asyncio
import matplotlib.pyplot as plt
import os
import sys
import seaborn as sns
import pandas as pd
from collections import defaultdict

# Adjust sys.path to import RAGPipeline from src/main/
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from main.rag_pipeline import RAGPipeline

# Define output directory
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
print(output_dir)
os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn’t exist

queries = [
    "What regulations globally address the use of biometric recognition in consumer services?",
    "What are the safety requirements for generative AI services across different jurisdictions?",
    "Which frameworks globally outline ethical principles for AI development?",
    "What laws regulate AI use in national security across jurisdictions?",
    "What regulations address AI transparency and labeling worldwide?"
]

doc_to_jurisdiction = {
    "327": "US", "637": "US", "837": "US", "1293": "US", "554": "US", "436": "US",
    "906": "US", "1385": "US", "1387": "US", "1161": "US", "1737": "US",
    "36": "China", "1723": "China", "1064": "China", "1137": "China", "1126": "China",
    "1125": "China", "35": "China", "1129": "China", "1151": "China",
    "757": "Multi",
    "768": "Private", "767": "Private", "987": "Private", "769": "Private",
    "1382": "Multi", "1380": "Multi",
    "1044": "Other"
}

def calculate_retrieval_bias(doc_ids):
    """Calculate jurisdiction counts and bias score for retrieved documents."""
    jurisdiction_count = defaultdict(int)
    for doc_id in doc_ids:
        jurisdiction = doc_to_jurisdiction.get(doc_id, "Unknown")
        jurisdiction_count[jurisdiction] += 1
    total_docs = len(doc_ids)
    if total_docs == 0:
        return {}, 0.0
    max_count = max(jurisdiction_count.values())
    bias_score = max_count / total_docs
    return dict(jurisdiction_count), bias_score

def generate_report(bias_results, retrieved_docs):
    """Generate a text report of bias analysis."""
    report_lines = ["Jurisdictional Bias Report\n" + "="*50]
    for query, result in bias_results.items():
        counts, bias_score = result["counts"], result["bias_score"]
        assessment = "Strong Bias" if bias_score > 0.8 else "Moderate Bias" if bias_score > 0.5 else "Low Bias"
        report_lines.append(f"\nQuery: {query}")
        report_lines.append(f"Retrieved Docs: {', '.join(retrieved_docs[query])}")
        report_lines.append(f"Jurisdictions: {counts}")
        report_lines.append(f"Bias Score: {bias_score:.2f}")
        report_lines.append(f"Assessment: {assessment}")
    report_path = os.path.join(output_dir, "jurisdictional_bias_report.txt")
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
    print(f"Report saved to '{report_path}'")

def plot_bar_chart(df):
    """Plot a stacked bar chart of jurisdictional distribution."""
    plt.figure(figsize=(12, 6))
    df.plot(kind="bar", stacked=True, colormap="tab10")
    plt.title("Jurisdictional Distribution Across Queries")
    plt.xlabel("Query")
    plt.ylabel("Number of Retrieved Documents")
    plt.legend(title="Jurisdiction", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plot_path = os.path.join(output_dir, "jurisdiction_bar_chart.png")
    plt.savefig(plot_path)
    plt.close()
    print(f"Bar chart saved as '{plot_path}'")

def plot_heatmap(df):
    """Plot a heatmap of jurisdictional representation."""
    plt.figure(figsize=(10, 6))
    sns.heatmap(df, annot=True, cmap="YlGnBu", fmt="d", cbar_kws={"label": "Document Count"})
    plt.title("Heatmap of Jurisdictional Representation")
    plt.xlabel("Jurisdiction")
    plt.ylabel("Query")
    plt.tight_layout()
    plot_path = os.path.join(output_dir, "jurisdiction_heatmap.png")
    plt.savefig(plot_path)
    plt.close()
    print(f"Heatmap saved as '{plot_path}'")

def plot_bias_scores(bias_results):
    """Plot bias scores per query."""
    query_labels = [f"Q{i+1}" for i in range(len(queries))]
    bias_scores = [bias_results[q]["bias_score"] for q in queries]
    plt.figure(figsize=(8, 5))
    plt.bar(query_labels, bias_scores, color="skyblue")
    plt.axhline(y=0.8, color="red", linestyle="--", label="Bias Threshold (0.8)")
    plt.title("Jurisdictional Bias Scores per Query")
    plt.xlabel("Query")
    plt.ylabel("Bias Score")
    plt.ylim(0, 1.1)
    plt.legend()
    plt.tight_layout()
    plot_path = os.path.join(output_dir, "bias_score_plot.png")
    plt.savefig(plot_path)
    plt.close()
    print(f"Bias score plot saved as '{plot_path}'")

async def run_pipeline(query):
    """Run the RAGPipeline and return document IDs."""
    pipeline = RAGPipeline()
    query_dict = [{"role": "user", "content": query}]
    messages, retrieved_docs = await pipeline.run(query_dict)
    # Assuming retrieved_docs is a list of dicts with 'id' keys
    return retrieved_docs  # Return as-is; adjust in calculate_retrieval_bias if needed

async def main():
    """Main function to run bias detection with pipeline."""
    # Run pipeline for each query and collect retrieved docs
    retrieved_docs = {}
    for query in queries:
        print(query)
        doc_ids = await run_pipeline(query)
        retrieved_docs[query] = doc_ids
        print(f"Query: {query}\nRetrieved Docs: {doc_ids}")

    # Analyze bias
    bias_results = {}
    jurisdiction_data = defaultdict(list)
    
    for query, docs in retrieved_docs.items():
        counts, bias_score = calculate_retrieval_bias(docs)
        bias_results[query] = {"counts": counts, "bias_score": bias_score}
        for jurisdiction, count in counts.items():
            jurisdiction_data[jurisdiction].append(count)
        for jur in set(doc_to_jurisdiction.values()):
            if jur not in counts:
                jurisdiction_data[jur].append(0)

    # Generate report and visualizations
    generate_report(bias_results, retrieved_docs)
    jurisdictions = list(jurisdiction_data.keys())
    query_labels = [f"Q{i+1}" for i in range(len(queries))]
    df = pd.DataFrame(jurisdiction_data, index=query_labels)

    plot_bar_chart(df)
    plot_heatmap(df)
    plot_bias_scores(bias_results)

if __name__ == "__main__":
    asyncio.run(main())