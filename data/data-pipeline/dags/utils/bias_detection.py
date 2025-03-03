import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import os
import pickle
import logging

# Set up custom logger
logger = logging.getLogger('bias_detection_logger')
logger.setLevel(logging.INFO)

# Create directory for logs if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'util_logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'bias_detection.log')

# Create file handler and set formatter
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# Prevent log propagation to Airflow's root logger
logger.propagate = False

# Define output directory for bias analysis
output_dir_name = "bias_analysis"

# Define key categorical features for bias detection
categorical_features = {
    'Authority': 'Authority bias (e.g., overrepresentation of U.S. Congress)',
    'Collections': 'Collection bias (e.g., focus on specific policy types)',
    'Most recent activity': 'Activity status bias (e.g., enacted vs. defunct)',
    'Primarily applies to the government': 'Applicability bias (gov vs. private)',
    'Primarily applies to the private sector': 'Applicability bias (private vs. gov)'
}

# Function to extract and count occurrences in multi-valued columns (e.g., Collections)
def count_multi_valued_column(column_data, delimiter=';'):
    try:
        all_values = []
        for entry in column_data.dropna():
            values = entry.split(delimiter)
            all_values.extend([v.strip() for v in values])
        return Counter(all_values)
    except Exception as e:
        logger.error(f"Error in count_multi_valued_column: {e}")
        raise

# Function to detect bias by analyzing distributions
def detect_bias(df, feature_name, description):
    try:
        logger.info(f"Detecting {description}")
        print(f"\nDetecting {description}")

        # Handle single-valued vs. multi-valued columns
        if feature_name == 'Collections':
            counts = count_multi_valued_column(df[feature_name])
            total = sum(counts.values())
        else:
            counts = df[feature_name].value_counts(dropna=False)
            total = counts.sum()

        # Log and print raw counts and percentages
        logger.info(f"Total entries for {feature_name}: {total}")
        print(f"Total entries: {total}")
        for key, value in counts.items():
            percentage = (value / total) * 100
            logger.info(f"{key}: {value} ({percentage:.2f}%)")
            print(f"{key}: {value} ({percentage:.2f}%)")

        # Flag potential bias if any category dominates (>50%)
        for key, value in counts.items():
            if (value / total) > 0.5:
                warning_msg = f"WARNING: Potential bias detected - '{key}' dominates with {value / total * 100:.2f}%"
                logger.warning(warning_msg)
                print(warning_msg)

        # Visualize the distribution
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_dir_name)
        os.makedirs(output_dir, exist_ok=True)
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
        plot_path = os.path.join(output_dir, f'bias_plot_{feature_name.lower().replace(" ", "_")}.png')
        plt.savefig(plot_path)
        plt.close()
        logger.info(f"Saved bias plot to {plot_path}")

    except Exception as e:
        logger.error(f"Error in detect_bias for {feature_name}: {e}")
        raise

# Function to simulate retrieval performance across slices (mock example)
def simulate_retrieval_performance(df, feature_name):
    try:
        logger.info(f"Simulating retrieval performance across {feature_name}")
        print(f"\nSimulating retrieval performance across {feature_name} slices")

        if feature_name == 'Collections':
            counts = count_multi_valued_column(df[feature_name])
            total_docs = sum(counts.values())
        else:
            counts = df[feature_name].value_counts(dropna=False)
            total_docs = counts.sum()

        for key, value in counts.items():
            mock_score = min(1.0, value / (total_docs * 0.1))  # Arbitrary normalization
            logger.info(f"{key}: Simulated retrieval score = {mock_score:.2f}")
            print(f"{key}: Simulated retrieval score = {mock_score:.2f}")
            if mock_score < 0.5:
                warning_msg = f"WARNING: Low retrieval performance for '{key}' (score: {mock_score:.2f})"
                logger.warning(warning_msg)
                print(warning_msg)

    except Exception as e:
        logger.error(f"Error in simulate_retrieval_performance for {feature_name}: {e}")
        raise

# Combined function to detect bias and simulate retrieval
def detect_and_simulate_bias(data):
    try:
        df = pickle.loads(data)
        logger.info("Loaded data from serialized input")

        # Create output directory
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_dir_name)
        os.makedirs(output_dir, exist_ok=True)
        os.chdir(output_dir)
        logger.info(f"Set working directory to {output_dir}")

        # Analyze each categorical feature
        for feature, description in categorical_features.items():
            detect_bias(df, feature, description)
            simulate_retrieval_performance(df, feature)

        # Save summary to a text file
        summary_path = os.path.join(output_dir, 'bias_detection_summary.txt')
        with open(summary_path, 'w') as f:
            f.write("Bias Detection Summary\n")
            f.write("=====================\n")
            for feature, description in categorical_features.items():
                f.write(f"\n{description}\n")
                if feature == 'Collections':
                    counts = count_multi_valued_column(df[feature])
                    total = sum(counts.values())
                else:
                    counts = df[feature].value_counts(dropna=False)
                    total = counts.sum()
                f.write(f"Total entries: {total}\n")
                for key, value in counts.items():
                    percentage = (value / total) * 100
                    f.write(f"{key}: {value} ({percentage:.2f}%)\n")
        logger.info(f"Saved bias detection summary to {summary_path}")

        logger.info("Bias detection and simulation complete")
        print("\nBias detection complete. Check 'bias_analysis' folder for results.")

    except Exception as e:
        logger.error(f"Error in detect_and_simulate_bias: {e}")
        raise

# Main function with limited functionality
def main():
    try:
        csv_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'merged_input/Documents_segments_merged.csv')
        if not os.path.exists(csv_file_path):
            logger.error(f"CSV file not found: {csv_file_path}")
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")

        df = pd.read_csv(csv_file_path)
        logger.info("Loaded CSV file for bias detection")

        serialized_data = pickle.dumps(df)
        detect_and_simulate_bias(serialized_data)
        logger.info("Bias detection and simulation completed successfully")

    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()