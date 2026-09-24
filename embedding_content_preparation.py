import json
import os # Required for os.path.exists in the demo main block

def generate_json_schema_description_from_file(json_schema_filepath):
    """
    Reads a formal JSON schema from a file and generates a human-readable string
    describing its structure, focusing on key elements as per user prompt.
    """
    try:
        with open(json_schema_filepath, 'r') as f:
            schema = json.load(f)
    except FileNotFoundError:
        return f"Error: JSON schema file not found at {json_schema_filepath}."
    except json.JSONDecodeError:
        return f"Error: Could not decode JSON from file {json_schema_filepath}."
    except Exception as e:
        return f"Error reading or parsing JSON schema file {json_schema_filepath}: {e}"

    description_lines = [f"JSON Schema Description (from {json_schema_filepath}):"]

    properties = schema.get("properties", {})
    if not properties:
        return description_lines[0] + "\n- Schema has no top-level properties defined."

    description_lines.append(f"- Top-level keys: {', '.join(properties.keys())}.")

    # patient_email_original
    if 'patient_email_original' in properties:
        prop_details = properties['patient_email_original']
        desc = prop_details.get('description', 'No description.')
        ptype = prop_details.get('type', 'N/A')
        description_lines.append(f"  - 'patient_email_original' ({ptype}): {desc}")

    # conversations
    if 'conversations' in properties and properties['conversations'].get('type') == 'array':
        conv_details = properties['conversations']
        conv_desc = conv_details.get('description', 'List of conversation threads.')
        description_lines.append(f"  - 'conversations' (array of objects): {conv_desc}")

        conv_items_props = conv_details.get('items', {}).get('properties', {})
        if conv_items_props:
            description_lines.append(f"    - Each conversation object includes keys like: {', '.join(list(conv_items_props.keys())[:3])}...") # Show a few common keys

            # messages within conversations
            if 'messages' in conv_items_props and conv_items_props['messages'].get('type') == 'array':
                msg_details = conv_items_props['messages']
                msg_desc = msg_details.get('description', 'List of messages within the conversation.')
                description_lines.append(f"      - 'messages' (array of objects): {msg_desc}")

                msg_items_props = msg_details.get('items', {}).get('properties', {})
                if msg_items_props:
                    description_lines.append(f"        - Each message object includes keys like: {', '.join(list(msg_items_props.keys())[:3])}...") # Show a few common keys

                    # Specific message sub-fields as requested
                    for key_name in ['message_id', 'date_iso', 'subject', 'body', 'sender', 'recipients_to', 'attachments', 'direction']:
                        if key_name in msg_items_props:
                            key_prop = msg_items_props[key_name]
                            key_type = key_prop.get('type', 'N/A')
                            key_format = key_prop.get('format')
                            key_enum = key_prop.get('enum')
                            key_desc_text = key_prop.get('description', 'No description.')

                            type_str = key_type
                            if key_format: type_str += f" ({key_format})"
                            if key_enum: type_str += f" (enum: {', '.join(key_enum)})"

                            description_lines.append(f"          - '{key_name}' ({type_str}): {key_desc_text}")

                            if key_name == 'attachments' and key_prop.get('type') == 'array':
                                attach_items_props = key_prop.get('items',{}).get('properties',{})
                                if attach_items_props:
                                     description_lines.append(f"            - Each attachment object has keys: {', '.join(attach_items_props.keys())}")
    return "\n".join(description_lines)

def generate_text_file_schema_description(filepath, data_description_name):
    """
    Reads a text file (expected to contain a schema or description) and returns its content,
    prefixed with a title indicating what it describes.
    """
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        return f"Schema Description for {data_description_name} (from {filepath}):\n{content}"
    except FileNotFoundError:
        return f"Error: Schema file not found at {filepath} for {data_description_name}."
    except Exception as e:
        return f"Error reading file {filepath} for {data_description_name}: {e}"

def generate_json_filenames_summary_description_from_file(filepath):
    """
    Reads a file containing a list of JSON filenames (one per line) and provides a summary description.
    This description is intended for RAG to help the LLM understand the naming convention of data files.
    """
    try:
        with open(filepath, 'r') as f:
            filenames = [line.strip() for line in f if line.strip()]

        if not filenames:
            return f"No filenames found in {filepath}."

        description = f"Summary of JSON Data Filenames (from {filepath}):\n"
        description += "The system accesses patient-specific data stored in JSON files. Here are examples of such filenames:\n"
        for fname in filenames[:5]: # Show up to 5 examples
            description += f"- {fname}\n"
        if len(filenames) > 5:
            description += "- ... and more.\n"

        description += "\nKey characteristics of these filenames:\n"
        description += "- They often include batch numbers (e.g., 'batch_001_').\n"
        description += "- Patient identifiers (like email addresses) are part of the filename, with special characters (e.g., '@', '.') typically replaced (e.g., '_at_', '_dot_').\n"
        description += "This list and description help in understanding how to reference or locate individual patient JSON data files programmatically."
        return description
    except FileNotFoundError:
        return f"Error: Filenames file not found at {filepath}."
    except Exception as e:
        return f"Error reading or processing filenames from {filepath}: {e}"

if __name__ == '__main__':
    print("--- Demonstrating Content Preparation Functions for RAG ---")

    # Define file paths (these files were created in a previous step)
    json_schema_file = "patient_json_schema.json"
    csv_schema_file = "csv_schema.txt" # Describes all_email_corpus.csv
    master_csv_file = "master_csv_schema.txt" # Describes master_patient_json_links.csv
    json_filenames_list_file = "json_filenames.txt"

    # Ensure dummy files exist for the demo to run if not already present
    if not os.path.exists(json_schema_file):
        with open(json_schema_file, "w") as f: json.dump({"properties": {"patient_email_original": {"type":"string"}}}, f)
    if not os.path.exists(csv_schema_file):
        with open(csv_schema_file, "w") as f: f.write("turn_id,patient_email")
    if not os.path.exists(master_csv_file):
        with open(master_csv_file, "w") as f: f.write("Patient Email,JSON File Path")
    if not os.path.exists(json_filenames_list_file):
        with open(json_filenames_list_file, "w") as f: f.write("dummy_patient_at_example_com.json")

    print("\n1. JSON Schema Description (from file):")
    json_desc = generate_json_schema_description_from_file(json_schema_file)
    print(json_desc)

    print("\n2. CSV Schema Description for 'all_email_corpus.csv' (from file):")
    csv_desc = generate_text_file_schema_description(csv_schema_file, "'all_email_corpus.csv'")
    print(csv_desc)

    print("\n3. Master CSV Schema Description for 'master_patient_json_links.csv' (from file):")
    master_csv_desc = generate_text_file_schema_description(master_csv_file, "'master_patient_json_links.csv'")
    print(master_csv_desc)

    print("\n4. JSON Filenames Summary Description (from file):")
    filenames_desc = generate_json_filenames_summary_description_from_file(json_filenames_list_file)
    print(filenames_desc)

    print("\n--- End of Demonstration ---")
