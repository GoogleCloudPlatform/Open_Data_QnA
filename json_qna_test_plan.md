# JSON QnA System - Test Plan

## 1. Introduction

This document outlines the testing strategy and test cases for the JSON QnA system. The system is designed to understand natural language questions and retrieve information from a collection of JSON files, potentially using CSV files for lookups or broader corpus searching. The core of the system involves LLM-generated Python code for data retrieval and processing.

## 2. Testing Strategy

The testing strategy encompasses both unit tests for individual components (though not detailed here) and a primary focus on integration and end-to-end testing of the entire workflow.

### 2.1 Unit Testing (Conceptual)

*   **Individual Agents:** Each agent (`BuildJSONQueryAgent`, `ValidateJSONQueryAgent`, `DebugJSONQueryAgent`, `EmbedderAgent`, `ResponseAgent`) should ideally have unit tests to verify its specific logic (e.g., prompt formatting, basic validation with `ast.parse`, response structuring) using mock LLM calls and predefined inputs/outputs.
*   **Execution Script (`execute_json_query.py`):** Test `run_generated_code` with various valid and invalid Python code snippets, ensuring correct execution, error handling, and adherence to `restricted_globals`.
*   **Schema Preparation (`embedding_content_preparation.py`):** Test functions that generate descriptions from schema files.

### 2.2 Integration Testing Workflow (Primary Focus)

This workflow tests the collaboration of all components:

1.  **Prerequisites:**
    *   Ensure all necessary data files are in place (patient JSONs, `all_email_corpus.csv`, `master_patient_json_links.csv`).
    *   Ensure all schema description files (`patient_json_schema.json`, `csv_schema.txt`, `master_csv_schema.txt`, `json_filenames.txt`) are accurate and present.
    *   Run the embedding setup process (e.g., `python opendataqna.py --setup_embeddings` using the modified main script) to ensure the vector store has the latest embeddings for all schema descriptions and manifest files.

2.  **Test Execution:**
    *   Use the main application script (e.g., modified `opendataqna.py` or a dedicated test script that calls `run_json_query_pipeline`).
    *   For each test case:
        *   Input the natural language question.
        *   Log/Observe the generated Python code from `BuildJSONQueryAgent`.
        *   Log/Observe the validation result from `ValidateJSONQueryAgent`.
        *   If debugging occurs, log/Observe the corrected code from `DebugJSONQueryAgent`.
        *   Log/Observe the dictionary returned by `execute_json_query.run_generated_code` (containing `success`, `data`, `error`).
        *   Log/Observe the final natural language response from `ResponseAgent`.

3.  **Verification:**
    *   Compare the `data` from `run_generated_code` and the final natural language response against the "Expected Information/Behavior" defined in the test case.
    *   For failed tests, analyze the logs to pinpoint the failing component (e.g., incorrect Python code generation, faulty execution, misleading RAG context, poor natural language response).

### 2.3 Iteration and Refinement Process

Testing is an iterative process. If tests fail or produce suboptimal results:

1.  **Prompt Engineering:** Refine the system prompts for `BuildJSONQueryAgent` (Python code generation), `DebugJSONQueryAgent` (code correction), and `ResponseAgent` (NL response generation). This is often the first line of defense.
2.  **Schema Descriptions & RAG Context:**
    *   Ensure the schema description files (`patient_json_schema.json`, `csv_schema.txt`, etc.) are accurate and provide sufficient detail for the LLM.
    *   Update the `embedding_content_preparation.py` script if the way descriptions are generated needs improvement.
    *   Re-run the embedding process after schema/description changes.
3.  **Agent Logic:** Modify the internal logic of agents if prompt engineering or RAG context improvements are insufficient. For example, the parsing in `ValidateJSONQueryAgent` or the control flow in the main pipeline.
4.  **Execution Script (`execute_json_query.py`):** If runtime errors occur that are not due to faulty generated code, the execution environment itself (e.g., `restricted_globals`) might need adjustment, but with extreme caution regarding security.

## 3. Test Cases

The following test cases are designed to cover a range of functionalities and potential issues.
*(Note: Assumed patient JSON structure includes `patient_email_original`, `conversations` list, each with a `messages` list. Each message has `message_id`, `subject`, `body`, `date_iso`, `sender`, `direction`, `attachments` etc. `master_patient_json_links.csv` maps `Patient Email` to `JSON File Path (Relative to Output Root)`. `all_email_corpus.csv` has `patient_email`, `message_content`, `sentiment_score`, `topic`, `intent` etc.)*

---

**ID:** TC-001
**Question:** "What is the patient email for the JSON file named 'batch_001_aaronmeers73_at_gmail_com.json'?"
**Description/Goal:** Tests direct lookup/extraction from the main JSON structure (patient_email_original).
**Expected Information/Behavior:** Returns "aaronmeers73@gmail.com".
**Key Data Sources (Conceptual):** Specific patient JSON (`batch_001_aaronmeers73_at_gmail_com.json`).

---

**ID:** TC-002
**Question:** "How many conversations does aaronmeers73@gmail.com have?"
**Description/Goal:** Tests counting items in a list within the JSON (number of conversations).
**Expected Information/Behavior:** Returns an integer representing the total number of entries in the `conversations` array for `aaronmeers73@gmail.com`.
**Key Data Sources (Conceptual):** `master_patient_json_links.csv` (for lookup), `batch_001_aaronmeers73_at_gmail_com.json`.

---

**ID:** TC-003
**Question:** "List the message IDs in conversation `conv_001_outstanding_bal_aaronmeers` for patient `aaronmeers73@gmail.com`."
**Description/Goal:** Tests iterating through nested lists and extracting specific fields (message_id from messages within a specific conversation).
**Expected Information/Behavior:** Returns a list of all `message_id` strings for the specified conversation ID for `aaronmeers73@gmail.com`.
**Key Data Sources (Conceptual):** `master_patient_json_links.csv`, `batch_001_aaronmeers73_at_gmail_com.json`.

---

**ID:** TC-004
**Question:** "Get the full body of message `msg1_conv1` from conversation `conv1` for patient `aaronmeers73@gmail.com`." (Assuming `conv1` and `msg1_conv1` are valid IDs from sample data)
**Description/Goal:** Tests targeted retrieval of a specific field from a deeply nested message object.
**Expected Information/Behavior:** Returns the string content of the `body` field for the specified message.
**Key Data Sources (Conceptual):** `master_patient_json_links.csv`, `batch_001_aaronmeers73_at_gmail_com.json`.

---

**ID:** TC-005
**Question:** "What are the filenames of attachments for message `msg1_conv1` in conversation `conv1` for `aaronmeers73@gmail.com`?"
**Description/Goal:** Tests accessing an array of objects (`attachments`) within a message and extracting a field (`filename`).
**Expected Information/Behavior:** Returns a list of attachment filenames (e.g., `["lab_results.pdf", "symptoms_list.docx"]`).
**Key Data Sources (Conceptual):** `master_patient_json_links.csv`, `batch_001_aaronmeers73_at_gmail_com.json`.

---

**ID:** TC-006
**Question:** "Find all messages from `aaronmeers73@gmail.com` where the subject contains the word 'appointment'."
**Description/Goal:** Tests filtering messages based on a keyword in the `subject` and patient context. Assumes 'from' implies the patient is the sender or `direction` field is used.
**Expected Information/Behavior:** Returns a list of message objects (or relevant fields like subject, date, body) where the patient is the sender and 'appointment' is in the subject.
**Key Data Sources (Conceptual):** `master_patient_json_links.csv`, `batch_001_aaronmeers73_at_gmail_com.json`.

---

**ID:** TC-007
**Question:** "Show messages sent by 'doctor@example.com' to `aaronmeers73@gmail.com` during April 2023."
**Description/Goal:** Tests filtering messages by sender, recipient (implicitly the patient file), and a date range.
**Expected Information/Behavior:** Returns a list of message objects (or relevant fields) matching the criteria. Code must parse `date_iso` for comparison.
**Key Data Sources (Conceptual):** `master_patient_json_links.csv`, `batch_001_aaronmeers73_at_gmail_com.json`.

---

**ID:** TC-008
**Question:** "Which patients discussed 'insurance' in their emails and what are their conversation IDs?"
**Description/Goal:** Tests a broader query that might first use `all_email_corpus.csv` (for `message_content` search) to identify relevant `patient_email` and `conversation_id` values.
**Expected Information/Behavior:** Returns a list of dictionaries, each with `patient_email` and `conversation_id` for conversations where 'insurance' was mentioned.
**Key Data Sources (Conceptual):** `all_email_corpus.csv`, potentially `master_patient_json_links.csv` if further details are needed from JSONs.

---

**ID:** TC-009
**Question:** "List emails with a positive sentiment score and show their subject and sender. Only consider messages from `all_email_corpus.csv`."
**Description/Goal:** Tests filtering based on a numerical field (`sentiment_score` from CSV) and extracting other fields from the CSV.
**Expected Information/Behavior:** Returns a list of dictionaries with `subject` and `sender` for emails from `all_email_corpus.csv` that have a positive sentiment score (e.g., > 0.2, assuming a threshold is defined or LLM infers one).
**Key Data Sources (Conceptual):** `all_email_corpus.csv`.

---

**ID:** TC-010
**Question:** "Get emails for patient `nonexistent_patient_email@example.com`."
**Description/Goal:** Tests error handling for a non-existent patient.
**Expected Information/Behavior:** System should indicate that the patient was not found or no data is available for this patient. The `run_generated_code` should return `success: False` or `success: True` with empty data, and `ResponseAgent` should phrase this appropriately.
**Key Data Sources (Conceptual):** `master_patient_json_links.csv` (lookup will fail).

---

**ID:** TC-011
**Question:** "What is the meaning of life?"
**Description/Goal:** Tests how the system handles an ambiguous or irrelevant question.
**Expected Information/Behavior:** System should indicate it cannot answer this type of question or that no relevant information was found in the patient data. It should not attempt to query unrelated fields or hallucinate.
**Key Data Sources (Conceptual):** LLM's ability to stick to the task, potentially RAG context indicating data domains.

---

**ID:** TC-012
**Question:** "Show me the latest message sent by `aaronmeers73@gmail.com`."
**Description/Goal:** Tests sorting messages by date and selecting the most recent one where the patient is the sender.
**Expected Information/Behavior:** Returns the subject, body, and date of the most recent message sent by `aaronmeers73@gmail.com` (direction: "outbound").
**Key Data Sources (Conceptual):** `master_patient_json_links.csv`, `batch_001_aaronmeers73_at_gmail_com.json`.

---

**ID:** TC-013
**Question:** "Are there any messages for `aaronmeers73@gmail.com` that have attachments?"
**Description/Goal:** Tests checking for the existence/non-emptiness of an array (`attachments`) within messages.
**Expected Information/Behavior:** Returns a boolean (True/False) or a list of messages that have attachments, or a statement like "Yes, there are messages with attachments" or "No, no messages have attachments."
**Key Data Sources (Conceptual):** `master_patient_json_links.csv`, `batch_001_aaronmeers73_at_gmail_com.json`.

---

**ID:** TC-014
**Question:** "Find the JSON file path for `aaronmeers73@gmail.com`."
**Description/Goal:** Directly tests the system's ability to use `master_patient_json_links.csv` if the LLM is prompted to expose this. (More of an internal mechanism test).
**Expected Information/Behavior:** Returns the string for the JSON file path, e.g., "batch_001_aaronmeers73_at_gmail_com.json".
**Key Data Sources (Conceptual):** `master_patient_json_links.csv`.

---

**ID:** TC-015
**Question:** "What was the first message ever received by `aaronmeers73@gmail.com` from the clinic?"
**Description/Goal:** Tests sorting messages by date (ascending) and filtering by direction ('inbound').
**Expected Information/Behavior:** Returns the subject, body, and date of the earliest message received by the patient from the clinic.
**Key Data Sources (Conceptual):** `master_patient_json_links.csv`, `batch_001_aaronmeers73_at_gmail_com.json`.

---
**ID:** TC-016
**Question:** "List all unique senders who communicated with `aaronmeers73@gmail.com`."
**Description/Goal:** Tests collecting values from a field across all messages and finding unique entries.
**Expected Information/Behavior:** Returns a list of unique email addresses from the `sender` field in messages associated with `aaronmeers73@gmail.com`, excluding the patient's own email if only external senders are desired (prompt may need to be specific).
**Key Data Sources (Conceptual):** `master_patient_json_links.csv`, `batch_001_aaronmeers73_at_gmail_com.json`.

---
**ID:** TC-017
**Question:** "For patient `aaronmeers73@gmail.com`, are there any conversations with more than 5 messages?"
**Description/Goal:** Tests counting nested items (messages within conversations) and applying a condition.
**Expected Information/Behavior:** Returns True/False or a list of conversation IDs that meet the criteria.
**Key Data Sources (Conceptual):** `master_patient_json_links.csv`, `batch_001_aaronmeers73_at_gmail_com.json`.

---

This list provides a starting point and should be expanded based on the specific capabilities and complexities implemented in the JSON querying system.The test plan document `json_qna_test_plan.md` has been successfully created. It includes the testing strategy (unit, integration, iteration) and a diverse set of 15+ test cases with IDs, questions, descriptions, expected outcomes, and key data sources.

The tasks for this sub-objective were:
1.  **Create a Test Plan Document (`json_qna_test_plan.md`):**
    *   Outline testing strategy (unit, integration, iteration). - **Completed.**
    *   Develop 10-15 diverse test cases with specified fields (ID, Question, Description, Expected Info, Key Data Sources). - **Completed (17 test cases provided).**

2.  **Output:** The full content of the `json_qna_test_plan.md` document. - This will be the next step.

I will now output the content of `json_qna_test_plan.md`.
