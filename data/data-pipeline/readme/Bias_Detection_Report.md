# Bias Detection Report

## Overview

This bias detection analysis was conducted to evaluate the dataset used for developing a Retrieval-Augmented Generation (RAG) chatbot focused on AI governance and policy. It is available in the 'data/data-pipeline/dags/bias_analysis' folder.  The dataset, comprising legislative texts, executive orders, and corporate policies, was assessed across five key categorical features: Authority, Collections, Most Recent Activity, Primarily Applies to the Government, and Primarily Applies to the Private Sector. The goal was to identify potential biases that could influence the chatbot’s performance and ensure transparency in its design process.

## Findings

1. **Authority Bias**  
   The dataset exhibits a strong skew toward documents authored by the United States Congress, which dominates as the primary authority compared to state governments (e.g., California, Rhode Island), international bodies (e.g., Chinese central government), or private-sector entities. This overrepresentation suggests a U.S. federal legislative focus, with significantly less coverage of state-level, international, or corporate perspectives.

2. **Collection Bias**  
   The types of documents in the dataset lean heavily toward U.S. federal laws, with a notable emphasis on recent defense-related policies such as those tied to the National Defense Authorization Act (NDAA). Other collections, like state and local laws, corporate policies, and international agreements, are present but far less prominent, indicating a concentration on federal and defense-oriented content.

3. **Activity Status Bias**  
   The dataset includes a near-even split between defunct and enacted policies, with proposed policies forming a small minority. This distribution highlights a substantial presence of outdated documents alongside active ones, while emerging policies are underrepresented, potentially skewing the chatbot toward historical rather than forward-looking insights.

4. **Applicability Bias (Government vs. Private Sector)**  
   When examining applicability, the dataset shows a bias away from documents primarily targeting the government, with a majority not exclusively government-focused. Conversely, an even stronger skew exists against private-sector applicability, with only a small fraction of documents directly relevant to private entities. This suggests a broader societal focus but limited corporate-specific content.

## Implications for the Chatbot

These biases imply that the chatbot may perform best when addressing U.S. federal legislative queries—particularly those related to defense policies—while potentially underperforming on state-level, international, or private-sector topics. The emphasis on defunct and enacted policies over proposed ones could lead to responses that reflect historical contexts more than current or future trends. Moreover, the limited private-sector focus may restrict the chatbot's ability to provide robust insights into corporate AI governance, despite the prevalence of government-related authorities.

## Decision Against Mitigation

While mitigation strategies such as dropping overrepresented rows or upsampling underrepresented categories were considered, no adjustments will be made to the dataset. Removing dominant entries, such as those from the U.S. Congress, would significantly reduce the dataset’s size and eliminate critical data essential for the chatbot’s functionality. Given the dataset's role as the foundational knowledge base for the RAG system, retaining all entries ensures comprehensive coverage—even if biased. This trade-off prioritizes data availability over perfect balance, acknowledging that the chatbot's utility depends on having sufficient content to retrieve and generate responses, particularly for well-represented domains like U.S. federal policy.

## Conclusion

The detected biases—favoring U.S. Congress, federal laws, enacted/defunct statuses, and non-private-sector applicability—reflect the dataset’s composition and will shape the chatbot’s strengths and limitations. By preserving the full dataset, we maintain its richness and breadth, accepting the biases as inherent to the available data rather than an artifact to be corrected. Future iterations could explore supplementing the dataset with additional sources to address underrepresented areas, but for now, the focus remains on leveraging the existing content to deliver a functional and informative AI governance chatbot.
