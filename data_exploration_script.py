# data_exploration_script.py

def explore_json_structure(sample_json_object):
    """
    Explores and prints the structure of a sample JSON object.
    """
    print("\n--- Exploring JSON Structure ---")
    if not isinstance(sample_json_object, dict):
        print("Provided sample is not a dictionary.")
        return

    print("Top-level keys:", list(sample_json_object.keys()))

    for key, value in sample_json_object.items():
        if isinstance(value, dict):
            print(f"  Keys in nested dictionary '{key}':", list(value.keys()))
        elif isinstance(value, list):
            if value: # Check if list is not empty
                first_item = value[0]
                if isinstance(first_item, dict):
                    print(f"  Keys in first item of list '{key}':", list(first_item.keys()))
                else:
                    print(f"  List '{key}' contains elements of type: {type(first_item).__name__}")
            else:
                print(f"  List '{key}' is empty.")
    print("--- End of JSON Structure Exploration ---")

def list_csv_columns():
    """
    Prints the expected column names for all_email_corpus.csv.
    """
    print("\n--- Expected CSV Columns (all_email_corpus.csv) ---")
    expected_columns = [
        "message_id",
        "conversation_id",
        "patient_email_original",
        "date_iso",
        "direction",
        "subject",
        "body"
    ]
    print(expected_columns)
    print("--- End of CSV Columns ---")

# Conceptual Mapping from CSV to JSON:
# - Use 'patient_email_original' from CSV to identify the relevant JSON file
#   (assuming a naming convention like 'patient_email_original.json' or a lookup mechanism).
# - Within the identified JSON file, iterate through 'conversations'.
# - For each conversation, iterate through 'messages'.
# - Match 'conversation_id' and 'message_id' from the CSV row with the
#   corresponding fields in the JSON message to locate the specific message.

if __name__ == "__main__":
    print("Starting data exploration script...")

    # Sample JSON object based on the problem description
    # (e.g., from a file like 'patient_email_original.json')
    sample_json = {
        "patient_email_original": "patient1@example.com",
        "total_conversations": 2,
        "conversations": [
            {
                "conversation_id": "conv1",
                "start_date_iso": "2023-01-10T10:00:00Z",
                "total_messages": 2,
                "participants": ["patient1@example.com", "doctor@example.com"],
                "messages": [
                    {
                        "message_id": "msg1_conv1",
                        "sender": "patient1@example.com",
                        "recipient": "doctor@example.com",
                        "date_iso": "2023-01-10T10:00:00Z",
                        "subject": "Regarding my appointment",
                        "body": "Hello Dr. Smith, I wanted to confirm my appointment.",
                        "attachments": [
                            {"filename": "lab_results.pdf", "size_kb": 1200},
                            {"filename": "symptoms_list.docx", "size_kb": 35}
                        ],
                        "read_status": True
                    },
                    {
                        "message_id": "msg2_conv1",
                        "sender": "doctor@example.com",
                        "recipient": "patient1@example.com",
                        "date_iso": "2023-01-10T10:05:00Z",
                        "subject": "Re: Regarding my appointment",
                        "body": "Confirmed, see you then.",
                        "attachments": [],
                        "read_status": True
                    }
                ]
            },
            {
                "conversation_id": "conv2",
                "start_date_iso": "2023-02-15T14:30:00Z",
                "total_messages": 1,
                "participants": ["patient1@example.com", "nurse@example.com"],
                "messages": [
                    {
                        "message_id": "msg1_conv2",
                        "sender": "patient1@example.com",
                        "recipient": "nurse@example.com",
                        "date_iso": "2023-02-15T14:30:00Z",
                        "subject": "Question about medication",
                        "body": "Hi Nurse Betty, I have a question about my new medication.",
                        "attachments": [],
                        "read_status": False
                    }
                ],
                "tags": ["medication", "query"] # Example of a list of simple types
            }
        ],
        "last_updated_iso": "2023-03-01T12:00:00Z",
        "patient_preferences": {
            "contact_method": "email",
            "appointment_reminders": True
        }
    }

    explore_json_structure(sample_json)
    list_csv_columns()

    print("\nData exploration script finished.")
    print("Purpose: This script helps in understanding the structure of the expected JSON data format")
    print("and lists the columns of the related CSV file to aid in planning the mapping between them.")
