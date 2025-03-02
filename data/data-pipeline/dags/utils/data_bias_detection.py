import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import os

# Load your dataset (replace with your actual file path)

csv_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'merged_input/Documents_segments_merged.csv')
pd_csv_file = pd.read_csv(csv_file_path)



# Define key categorical features for bias detection based on your new CSV
categorical_features = {
    'Authority': 'Authority bias (e.g., overrepresentation of U.S. Congress)',
    'Collections': 'Collection bias (e.g., focus on specific policy types)',
    'Most recent activity': 'Activity status bias (e.g., enacted vs. defunct)',
    'Primarily applies to the government': 'Applicability bias (gov vs. private)',
    'Primarily applies to the private sector': 'Applicability bias (private vs. gov)'
}

# Function to extract and count occurrences in multi-valued columns (e.g., Collections)
def count_multi_valued_column(column_data, delimiter=';'):
    # Split multi-valued entries and flatten the list
    all_values = []
    for entry in column_data.dropna():
        values = entry.split(delimiter)
        all_values.extend([v.strip() for v in values])
    return Counter(all_values)

# Function to detect bias by analyzing distributions
def detect_bias(pd_csv_file, feature_name, description):
    print(f"\nDetecting {description}")
    
    # Handle single-valued vs. multi-valued columns
    if feature_name == 'Collections':
        # For columns with multiple values separated by semicolons
        counts = count_multi_valued_column(pd_csv_file[feature_name])
        total = sum(counts.values())  # Sum Counter values
    else:
        # For single-valued columns like Authority or status fields
        counts = pd_csv_file[feature_name].value_counts(dropna=False)  # pandas Series
        total = counts.sum()  # Sum pandas Series values directly

    # Print raw counts and percentages
    print(f"Total entries: {total}")
    for key, value in counts.items():
        percentage = (value / total) * 100
        print(f"{key}: {value} ({percentage:.2f}%)")

    # Flag potential bias if any category dominates (e.g., >50% of total)
    for key, value in counts.items():
        if (value / total) > 0.5:
            print(f"WARNING: Potential bias detected - '{key}' dominates with {value / total * 100:.2f}%")

    # Visualize the distribution
    plt.figure(figsize=(10, 6))
    if feature_name == 'Collections':
        plt.bar(counts.keys(), counts.values())
        plt.xticks(rotation=45, ha='right')
    else:
        counts.plot(kind='bar')
    plt.title(f'Distribution of {feature_name}')
    plt.xlabel(feature_name)
    plt.ylabel('Count')
    plt.tight_layout()
    plt.savefig(f'bias_plot_{feature_name.lower().replace(" ", "_")}.png')
    plt.close()

# Function to simulate retrieval performance across slices (mock example)
def simulate_retrieval_performance(pd_csv_file, feature_name):
    print(f"\nSimulating retrieval performance across {feature_name} slices")
    # Mock performance: Assume higher document count = better retrieval
    if feature_name == 'Collections':
        counts = count_multi_valued_column(pd_csv_file[feature_name])
        total_docs = sum(counts.values())
    else:
        counts = pd_csv_file[feature_name].value_counts(dropna=False)
        total_docs = counts.sum()
    
    for key, value in counts.items():
        # Simulated score: proportional to document availability (0-1 scale)
        mock_score = min(1.0, value / (total_docs * 0.1))  # Arbitrary normalization
        print(f"{key}: Simulated retrieval score = {mock_score:.2f}")
        if mock_score < 0.5:
            print(f"WARNING: Low retrieval performance for '{key}' (score: {mock_score:.2f})")

# Main bias detection process
def main():
    # Create a directory for output if it doesn’t exist
    if not os.path.exists('bias_analysis'):
        os.makedirs('bias_analysis')
    os.chdir('bias_analysis')

    # Analyze each categorical feature
    for feature, description in categorical_features.items():
        detect_bias(pd_csv_file, feature, description)
        simulate_retrieval_performance(pd_csv_file, feature)

    # Save summary to a text file
    with open('bias_detection_summary.txt', 'w') as f:
        f.write("Bias Detection Summary\n")
        f.write("=====================\n")
        for feature, description in categorical_features.items():
            f.write(f"\n{description}\n")
            if feature == 'Collections':
                counts = count_multi_valued_column(pd_csv_file[feature])
                total = sum(counts.values())
            else:
                counts = pd_csv_file[feature].value_counts(dropna=False)
                total = counts.sum()
            f.write(f"Total entries: {total}\n")
            for key, value in counts.items():
                percentage = (value / total) * 100
                f.write(f"{key}: {value} ({percentage:.2f}%)\n")

    print("\nBias detection complete. Check 'bias_analysis' folder for results.")

if __name__ == "__main__":
    main()