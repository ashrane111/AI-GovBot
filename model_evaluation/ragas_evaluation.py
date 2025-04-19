import os
import sys
import json
import logging
import pandas as pd
from langfuse import Langfuse
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
)
from datasets import Dataset
from dotenv import load_dotenv

# --- Evaluation Thresholds ---
# Define your minimum acceptable average scores for alerting
FAITHFULNESS_THRESHOLD = 1.1
ANSWER_RELEVANCY_THRESHOLD = 1.1

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration & Initialization ---
logger.info("Loading configuration and initializing clients...")
load_dotenv()

required_env_vars = ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST", "OPENAI_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(f"CRITICAL ERROR: Missing environment variables: {', '.join(missing_vars)}")
else:
    logger.info("Environment variables loaded successfully.")

try:
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST"),
    )
    logger.info("Langfuse client initialized.")
except Exception as e:
    logger.error(f"Failed to initialize Langfuse client: {e}", exc_info=True)
    sys.exit("CRITICAL ERROR: Failed to initialize Langfuse client.")

# --- Data Fetching & Extraction ---
logger.info("Fetching traces from Langfuse...")
data_for_ragas = []
# How many recent traces (conversations) to evaluate
TRACE_LIMIT = 50 # Adjust as needed

try:
    traces_generator = langfuse.get_traces(
        limit=TRACE_LIMIT,
        order_by={"startTime": "DESC"}
    )
    logger.info(f"Fetched trace data object. Attempting to process up to {TRACE_LIMIT} traces (received {len(traces_generator.data)})...")

    traces_processed_count = 0
    for i, trace in enumerate(traces_generator.data):
        last_query = None
        final_answer = None
        retrieved_contexts = [] # Reset for each trace

        try:
            # Extract Last User Query
            if (isinstance(trace.input, dict) and
                (kwargs := trace.input.get('kwargs')) and isinstance(kwargs, dict) and
                (query_body := kwargs.get('query_body')) and isinstance(query_body, dict) and
                (input_messages := query_body.get('messages')) and isinstance(input_messages, list)):
                for msg in reversed(input_messages):
                    if isinstance(msg, dict) and msg.get('role') == 'user' and 'content' in msg:
                        last_query = str(msg['content']).strip()
                        break

            # Extract Final Assistant Answer
            if (isinstance(trace.output, dict) and
                (answer_dict := trace.output.get('answer')) and isinstance(answer_dict, dict) and
                'content' in answer_dict):
                final_answer = str(answer_dict['content']).strip()

            # Extract Contexts
            if (isinstance(trace.output, dict) and
                (answer_dict := trace.output.get('answer')) and isinstance(answer_dict, dict) and
                (output_messages := answer_dict.get('messages')) and isinstance(output_messages, list)):
                for msg in reversed(output_messages):
                    if isinstance(msg, dict) and msg.get('role') == 'user' and 'content' in msg:
                        content_str = str(msg['content'])
                        context_prefix = "Context: "
                        context_start_index = content_str.find(context_prefix)
                        if context_start_index != -1:
                            context_block = content_str[context_start_index + len(context_prefix):].strip()
                            if context_block:
                                retrieved_contexts = [context_block]
                                logger.debug(f"Trace {trace.id}: Extracted context block (length: {len(context_block)}).")
                        break

            # Populate data ONLY if query, answer, AND context are present
            if last_query and final_answer and retrieved_contexts:
                ragas_entry = {
                    "question": last_query,
                    "answer": final_answer,
                    "contexts": retrieved_contexts,
                }
                data_for_ragas.append(ragas_entry)
                traces_processed_count += 1
            else:
                missing_parts = []
                if not last_query: missing_parts.append("last_query")
                if not final_answer: missing_parts.append("final_answer")
                if not retrieved_contexts: missing_parts.append("retrieved_contexts")
                logger.debug(f"Skipping trace {trace.id}: Missing required parts: {', '.join(missing_parts)}.")

        except Exception as e:
            logger.error(f"Error processing trace {getattr(trace, 'id', 'UNKNOWN')} (Index {i}): {e}", exc_info=False)

    logger.info(f"Finished processing traces. Extracted data for {traces_processed_count} interactions with context.")

except Exception as e:
    logger.error(f"Fatal error fetching or processing Langfuse traces: {e}", exc_info=True)
    sys.exit("CRITICAL ERROR: Failed fetching/processing Langfuse traces.")

# --- Dataset Preparation ---
ragas_dataset = None
if not data_for_ragas:
    logger.warning("No data with context available after extraction. Cannot run Ragas evaluation.")
    logger.info("Exiting: No data extracted for evaluation.")
    # Set outputs indicating no alert needed before exiting
    print(f"::set-output name=alert_needed::false")
    print(f"::set-output name=alert_details::No data with context available for evaluation.")
    sys.exit(0)
else:
    logger.info(f"Preparing dataset for Ragas with {len(data_for_ragas)} entries...")
    try:
        for item in data_for_ragas:
            item['contexts'] = [str(ctx) for ctx in item['contexts']]

        ragas_dataset = Dataset.from_list(data_for_ragas)
        logger.info(f"Dataset created with {len(ragas_dataset)} entries.")

        required_cols = ["question", "answer", "contexts"]
        if not all(col in ragas_dataset.column_names for col in required_cols):
            logger.error(f"Dataset is missing required columns! Found: {ragas_dataset.column_names}. Needed: {required_cols}")
            ragas_dataset = None

    except Exception as e:
        logger.error(f"Error creating Hugging Face Dataset: {e}", exc_info=True)
        ragas_dataset = None

# --- RAGAS Evaluation ---
evaluation_results = {} # Stores average scores {metric_name: score}
alert_needed = False
alert_details = [] # Stores reasons for alerting

if ragas_dataset:
    logger.info("Starting Ragas evaluation...")
    metrics_to_run = [
        faithfulness,
        answer_relevancy,
    ]
    logger.info(f"Evaluating with metrics: {[m.name for m in metrics_to_run]}")

    try:
        results = evaluate(
            dataset=ragas_dataset,
            metrics=metrics_to_run,
            raise_exceptions=False
        )

        # --- Process Results & Check Thresholds ---
        logger.info("Ragas evaluation completed.")
        try:
            results_df = None
            # Try to convert results to DataFrame for easier average calculation
            if hasattr(results, 'to_pandas'):
                 results_df = results.to_pandas()
                 logger.info("Results converted to DataFrame.")
            elif isinstance(results, dict):
                 # If results is already a dict of averages, use it directly
                 evaluation_results = {k: v for k, v in results.items() if isinstance(v, (int, float))}
                 logger.info(f"Direct evaluation results (averages): {evaluation_results}")
            else:
                 logger.warning(f"Unexpected Ragas results format: {type(results)}. Cannot automatically extract averages.")

            # --- REMOVED CSV Saving Block ---
            # The following lines were removed:
            # results_csv_filename = "ragas_evaluation_results.csv"
            # logger.info(f"Saving Ragas results to: {results_csv_filename}")
            # results_df.to_csv(results_csv_filename, index=False, encoding='utf-8')
            # --- End of Removed Block ---


            # Calculate averages from DataFrame if needed
            if results_df is not None and not evaluation_results:
                logger.info("Calculating average scores from DataFrame...")
                print("\n--- Average Scores (for logs) ---") # Print header for logs
                for metric in metrics_to_run:
                    metric_col_name = metric.name
                    if metric_col_name in results_df.columns:
                        if pd.api.types.is_numeric_dtype(results_df[metric_col_name]):
                           average_score = results_df[metric_col_name].mean(skipna=True)
                           if pd.notna(average_score):
                               print(f"Average {metric_col_name}: {average_score:.4f}")
                               evaluation_results[metric_col_name] = average_score
                           else:
                               print(f"Average {metric_col_name}: Could not be calculated (all values NaN?).")
                               evaluation_results[metric_col_name] = None
                        else:
                            logger.warning(f"Metric column '{metric_col_name}' is not numeric.")
                            evaluation_results[metric_col_name] = None
                    else:
                        logger.warning(f"Metric column '{metric_col_name}' not found in results.")
                        evaluation_results[metric_col_name] = None

            # Check Thresholds
            if not evaluation_results:
                logger.error("Could not determine average scores to check thresholds.")
                alert_needed = True
                alert_details.append("Failed to extract average scores from Ragas results.")
            else:
                logger.info("Checking thresholds against calculated average scores...")
                # Faithfulness Check
                if 'faithfulness' in evaluation_results and evaluation_results['faithfulness'] is not None:
                    if evaluation_results['faithfulness'] < FAITHFULNESS_THRESHOLD:
                        alert_needed = True
                        msg = f"Faithfulness ({evaluation_results['faithfulness']:.4f}) < threshold ({FAITHFULNESS_THRESHOLD})"
                        alert_details.append(msg)
                        logger.warning(f"ALERT: {msg}")
                elif 'faithfulness' not in evaluation_results or evaluation_results['faithfulness'] is None:
                    logger.warning("Faithfulness score not available for threshold check.")

                # Answer Relevancy Check
                if 'answer_relevancy' in evaluation_results and evaluation_results['answer_relevancy'] is not None:
                    if evaluation_results['answer_relevancy'] < ANSWER_RELEVANCY_THRESHOLD:
                        alert_needed = True
                        msg = f"Answer Relevancy ({evaluation_results['answer_relevancy']:.4f}) < threshold ({ANSWER_RELEVANCY_THRESHOLD})"
                        alert_details.append(msg)
                        logger.warning(f"ALERT: {msg}")
                elif 'answer_relevancy' not in evaluation_results or evaluation_results['answer_relevancy'] is None:
                    logger.warning("Answer Relevancy score not available for threshold check.")

        except Exception as e:
             logger.error(f"Error processing evaluation results: {e}", exc_info=True)
             alert_needed = True
             alert_details.append("Error processing Ragas evaluation results.")

    except Exception as e:
        logger.error(f"Error during Ragas evaluate() call: {e}", exc_info=True)
        alert_needed = True
        alert_details.append("Error occurred during Ragas evaluate() call.")
else:
     logger.warning("Skipping Ragas evaluation because dataset preparation failed.")
     alert_needed = True # Assume failure if dataset prep failed
     alert_details.append("Ragas evaluation skipped because dataset preparation failed.")

# --- Set GitHub Actions Outputs ---
logger.info(f"Setting GitHub Actions outputs (alert_needed={alert_needed})...")
print(f"::set-output name=alert_needed::{str(alert_needed).lower()}")

if alert_needed:
    details_string = " | ".join(alert_details)
    details_string_cleaned = details_string.replace("\n", " ").replace("\r", "")
    print(f"::set-output name=alert_details::{details_string_cleaned}")
    logger.info(f"Alert details: {details_string_cleaned}")
else:
    print(f"::set-output name=alert_details::Evaluation metrics met thresholds or evaluation skipped gracefully.")
    logger.info("Evaluation metrics met thresholds or evaluation skipped gracefully. No alert needed.")

# --- Cleanup ---
if 'langfuse' in locals() and hasattr(langfuse, 'flush'):
    try:
        langfuse.flush()
        logger.info("Langfuse client flushed.")
    except Exception as e:
        logger.error(f"Error flushing Langfuse client: {e}", exc_info=True)

logger.info("Script finished.")