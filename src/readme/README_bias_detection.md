# Bias Detection README

## Overview
This script (`model_bias_detection.py`) performs jurisdictional bias detection on document retrievals from a Retrieval-Augmented Generation (RAG) pipeline. It analyzes whether retrieved documents for a set of queries disproportionately favor one jurisdiction (e.g., U.S., China, EU) over others, ensuring globally balanced responses for governance-related AI applications. The script generates a report and visualizations to summarize bias findings.

### Features
- **Bias Calculation**: Measures jurisdictional skew using a bias score (`max(jurisdiction_count) / total_docs`).
- **Output**:
  - Text report (`jurisdictional_bias_report.txt`): Lists queries, retrieved documents, jurisdiction counts, bias scores, and assessments.
  - Visualizations:
    - Stacked bar chart (`jurisdiction_bar_chart.png`): Shows document distribution by jurisdiction per query.
    - Bias score plot (`bias_score_plot.png`): Highlights bias severity with a threshold (0.8).

### Location
- **Script**: `src/bias_detection/model_bias_detection.py`
- **Outputs**: `src/bias_detection/`

---

## Prerequisites
- **Needs backend Service to run**:
  - Refer [readme](README_web_app.md) for running backend service
- **Dependencies**:
  - `seaborn`: For heatmap visualization.
- **Project Setup**: Requires `RAGPipeline` from `src/main/rag_pipeline.py`.

---

*We conducted bias detection on our model using a smaller test dataset. The results indicated that the model retrieved relevant documents without exhibiting observable bias. Therefore, we proceeded with this model without applying additional bias mitigation techniques.*  
