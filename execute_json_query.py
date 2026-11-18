import json
import csv
import pandas # Added pandas as LLM is instructed to use it for CSVs
import os # For os.path.join, os.path.exists if LLM-generated code uses it (carefully)
from datetime import datetime # If generated code uses datetime objects

# Security Warning:
# The use of exec() is inherently risky if the executed code is not fully trusted.
# While restricted_globals are used here to limit the scope, it's crucial that:
# 1. The Python code string comes from a vetted source or has undergone rigorous validation.
# 2. The capabilities within restricted_globals are minimal and carefully chosen.
# 3. File system access is tightly controlled. The paths (json_base_path, etc.)
#    should be absolute and validated by the calling environment. The LLM-generated
#    code should be instructed to only use these provided base paths and not construct
#    arbitrary file paths.
# 4. Network access and other system calls should be disabled or heavily restricted.
#    The provided restricted_globals below does not explicitly enable network modules.

def run_generated_code(
    python_code_string: str,
    # These paths should be absolute and validated by the calling infrastructure
    # to prevent the LLM-generated code from accessing arbitrary file system locations.
    # The LLM will be instructed to generate code that uses these as base paths.
    json_base_path: str,
    all_emails_csv_path: str,
    master_links_csv_path: str
) -> dict:
    """
    Executes a string of Python code in a restricted environment.
    The Python code is expected to define a function called 'query_data_for_question'
    which will be called to perform the data querying.

    Args:
        python_code_string (str): The Python code (as a string) to execute.
                                  Expected to define 'query_data_for_question()'.
        json_base_path (str): Absolute base path to the directory containing JSON data files.
        all_emails_csv_path (str): Absolute path to the all_email_corpus.csv file.
        master_links_csv_path (str): Absolute path to the master_patient_json_links.csv file.

    Returns:
        dict: A dictionary containing the execution result:
              {'success': True/False, 'data': result_data, 'error': error_message}
    """
    print(f"Executing generated code. JSON Base: {json_base_path}, Master CSV: {master_links_csv_path}")

    # Define allowed global modules and functions for the exec environment
    # This list should be minimal and carefully curated.
    # Granting access to 'open' or 'os' is risky and should be done
    # if the generated code is strictly confined to using pre-validated base paths.
    # The LLM prompt for BuildJSONQueryAgent instructs it to use specific file names
    # like 'master_patient_json_links.csv' and a base path for JSONs.
    restricted_globals = {
        '__builtins__': {
            'print': print, # Allow print for potential debugging within generated code (if any)
            'list': list,
            'dict': dict,
            'str': str,
            'int': int,
            'float': float,
            'len': len,
            'sorted': sorted,
            'any': any,
            'all': all,
            'range': range,
            'zip': zip,
            'enumerate': enumerate,
            'isinstance': isinstance,
            'Exception': Exception, # Allow raising/catching generic exceptions
            'ValueError': ValueError,
            'TypeError': TypeError,
            'KeyError': KeyError,
            'FileNotFoundError': FileNotFoundError,
            'StopIteration': StopIteration, # For iterators
            'datetime': datetime, # For date parsing/comparison
        },
        'json': json,    # For json.load, json.loads
        'pd': pandas,    # For pandas.read_csv as LLM is instructed to use it
        # 'csv': csv,    # Alternative to pandas for CSV, if needed
        # 'os': {        # Very restricted os, only if absolutely necessary and specific functions
        #     'path': {
        #         'join': os.path.join, # If code needs to join paths
        #         'exists': os.path.exists # If code needs to check existence
        #     }
        # },
        # Pre-define the paths within the scope if not passing as args to the function
        # This makes them available as global-like variables to the exec'd code.
        # The generated code from BuildJSONQueryAgent is expected to define a function
        # that doesn't take these as arguments, but uses them from its environment (as per prompt example).
        # However, the prompt example for BuildJSONQueryAgent actually shows the generated function
        # defining these paths internally. For greater control and to ensure the generated code
        # uses the *exact* paths provided by the secure calling environment, it's better if
        # the generated function *accepts* them or they are injected.
        # For now, let's assume the generated code defines a function `query_data_for_question`
        # which does NOT take these paths as arguments, but expects them to be available
        # (e.g. by being defined in its global scope, or the LLM hardcodes them as per its prompt).
        # The prompt for BuildJSONQueryAgent instructs the LLM to use specific paths/filenames.
        # The paths like `json_base_path` are for the *execution environment* to manage.
        # The LLM-generated code is prompted to use fixed names like 'master_patient_json_links.csv'
        # and a fixed base for JSONs like './all_patient_jsons_with_prefix/'.
        # The execution environment should ensure these files are at those locations relative
        # to where the code is run, or adjust the paths.
        #
        # Let's refine this: The prompt for BuildJSONQueryAgent was:
        # "JSON file paths are constructed by prepending the base path './all_patient_jsons_with_prefix/'
        #  to the path found in master_patient_json_links.csv."
        # And "Your generated Python code MUST use this CSV to determine the correct JSON file path for a given patient_email."
        # And "master_df = pd.read_csv('master_patient_json_links.csv')"
        #
        # This implies the generated code will try to open 'master_patient_json_links.csv' directly.
        # We need to ensure that when `exec` runs, it can find this file.
        # The paths `master_links_csv_path` and `all_emails_csv_path` given to this `run_generated_code`
        # function should be the actual, accessible paths to these files.
        # One way is to inject these specific filenames into the globals, mapped to their real paths.
        # This is safer than letting the generated code assume relative paths.
        'MASTER_LINKS_CSV_FILE_PATH': master_links_csv_path,
        'ALL_EMAILS_CSV_FILE_PATH': all_emails_csv_path,
        'JSON_BASE_DIR_PATH': json_base_path
    }

    # The LLM is prompted to generate a function, typically 'query_data_for_question'.
    # This function will be defined in local_scope after exec.
    local_scope = {}

    # The LLM prompt instructs generated code to use specific paths/filenames.
    # For example, it's told the base path for JSONs is './all_patient_jsons_with_prefix/'
    # and to read 'master_patient_json_links.csv'.
    # The `run_generated_code` function receives `json_base_path`, `all_emails_csv_path`, `master_links_csv_path`.
    # The generated code should be modified by the LLM to use these injected path variables.
    # The BuildJSONQueryAgent prompt was updated to reflect this need:
    # e.g., master_df = pd.read_csv(MASTER_LINKS_CSV_FILE_PATH)
    # json_file_path = JSON_BASE_DIR_PATH + relative_json_path

    try:
        # Execute the generated Python code string.
        # This will define functions from the string in local_scope.
        exec(python_code_string, restricted_globals, local_scope)

        # Call the main function defined in the executed code.
        # The prompt for BuildJSONQueryAgent instructs the LLM to name this function
        # 'query_data_for_question' and that it should take no arguments.
        function_name_to_call = 'query_data_for_question'

        if function_name_to_call in local_scope and callable(local_scope[function_name_to_call]):
            # Call the function retrieved from the local_scope.
            # It will use MASTER_LINKS_CSV_FILE_PATH etc. from restricted_globals.
            result = local_scope[function_name_to_call]()
            return {'success': True, 'data': result, 'error': None}
        else:
            return {'success': False, 'data': None, 'error': f"Function '{function_name_to_call}' not found or not callable in generated code."}

    except SyntaxError as e:
        return {'success': False, 'data': None, 'error': f"SyntaxError in generated code: {e.msg} (line {e.lineno}, offset {e.offset})", 'details': str(e)}
    except FileNotFoundError as e:
        # This will catch FileNotFoundError if the generated code tries to open a file that doesn't exist
        # using the paths derived from the injected global path variables.
        return {'success': False, 'data': None, 'error': f"FileNotFoundError: {e}. Ensure files exist at provided paths. JSON Base: {json_base_path}, Master Links CSV: {master_links_csv_path}, All Emails CSV: {all_emails_csv_path}", 'details': str(e.strerror)}
    except KeyError as e:
        return {'success': False, 'data': None, 'error': f"KeyError: {e}. This often means the code tried to access a dictionary key that doesn't exist. Check if JSON/dictionary keys in the generated code match the actual data structure and schema.", 'details': f"Key: {str(e)}"}
    except pd.errors.EmptyDataError as e: # Specific pandas error
        return {'success': False, 'data': None, 'error': f"Pandas EmptyDataError: {e}. This means a CSV file might be empty or improperly formatted.", 'details': str(e)}
    except Exception as e:
        # General catch-all for other runtime errors from the executed code.
        import traceback
        tb_str = traceback.format_exc()
        return {'success': False, 'data': None, 'error': f"An unexpected error occurred during execution of generated code: {type(e).__name__} - {e}", 'details': tb_str}


if __name__ == '__main__':
    print("--- Testing execute_json_query.py ---")

    # Define dummy paths for testing (in a real scenario, these are absolute & validated)
    # For this test, we assume the script is run from the project root where dummy files might be.
    # The generated code will use these paths.
    current_dir = os.path.dirname(__file__) # Not ideal for __main__, better to use fixed paths for testing
    dummy_json_base_path = os.path.abspath(os.path.join(current_dir, "../all_patient_jsons_with_prefix/")) # Example path
    dummy_master_links_csv = "master_patient_json_links.csv" # Expects this in CWD or provide full path
    dummy_all_emails_csv = "all_email_corpus.csv"       # Expects this in CWD or provide full path

    # Create dummy files if they don't exist for the test to run
    if not os.path.exists(dummy_master_links_csv):
        with open(dummy_master_links_csv, "w") as f:
            f.write("Patient Email,JSON File Path (Relative to Output Root)\n")
            f.write("test@example.com,test_at_example_com.json\n")
            f.write("aaronmeers73@gmail.com,batch_001_aaronmeers73_at_gmail_com.json\n")


    dummy_patient_json_dir = os.path.join(dummy_json_base_path, "batch_001_aaronmeers73_at_gmail_com_json_dir") # incorrect, should be base path
    if not os.path.exists(dummy_json_base_path):
        os.makedirs(dummy_json_base_path, exist_ok=True)

    # Path for the specific JSON file mentioned in master_links
    specific_json_file_path = os.path.join(dummy_json_base_path, "batch_001_aaronmeers73_at_gmail_com.json")
    if not os.path.exists(specific_json_file_path):
         with open(specific_json_file_path, "w") as f:
            json.dump({
                "patient_email_original": "aaronmeers73@gmail.com",
                "conversations": [{
                    "messages": [
                        {"subject": "Test Subject 1", "date_iso": "2023-01-01T10:00:00Z", "direction": "outbound"},
                        {"subject": "Test Subject 2", "date_iso": "2023-01-02T11:00:00Z", "direction": "outbound"}
                    ]
                }]
            }, f)


    # Example 1: Valid Python code string (simulates LLM output)
    # This code uses the global path variables injected into restricted_globals
    valid_code_str = """
import json
import pandas as pd # pd is available via restricted_globals
from datetime import datetime

def query_data_for_question():
    patient_email_to_find = "aaronmeers73@gmail.com"

    # Use the injected global path for master_links_csv
    master_df = pd.read_csv(MASTER_LINKS_CSV_FILE_PATH)

    file_path_series = master_df[master_df["Patient Email"] == patient_email_to_find]["JSON File Path (Relative to Output Root)"]
    if file_path_series.empty:
        return f"Error: Patient email {patient_email_to_find} not found in master CSV."

    relative_json_path = file_path_series.iloc[0]
    # Use the injected global path for json_base_dir
    json_file_path = JSON_BASE_DIR_PATH + "/" + relative_json_path # Ensure correct path joining
                                                                # os.path.join is safer but os not fully exposed

    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return f"Error: JSON file not found at {json_file_path} (derived from {relative_json_path})."

    subjects = []
    for conv in data.get("conversations", []):
        for msg in conv.get("messages", []):
            if msg.get("direction") == "outbound":
                subjects.append(msg.get("subject"))

    # Sort by date to get last 2 (if date was extracted and sorted)
    # For simplicity, just returning all outbound subjects here
    return subjects[:2] # Get last 2 subjects based on order in file
"""
    print("\n--- Test 1: Executing valid generated code ---")
    result1 = run_generated_code(valid_code_str, dummy_json_base_path, dummy_all_emails_csv, dummy_master_links_csv)
    print(f"Result 1: {result1}")
    assert result1['success']
    assert "Test Subject 1" in result1['data']

    # Example 2: Code with a runtime FileNotFoundError (if JSON path was wrong)
    # (Simulated by asking for a patient not in our dummy master_links_csv or whose JSON doesn't exist)
    code_filenotfound_str = """
import json
import pandas as pd
def query_data_for_question():
    patient_email_to_find = "unknown@example.com" # This patient is not in dummy master_links_csv
    master_df = pd.read_csv(MASTER_LINKS_CSV_FILE_PATH)
    file_path_series = master_df[master_df["Patient Email"] == patient_email_to_find]["JSON File Path (Relative to Output Root)"]
    if file_path_series.empty:
        # This path will be taken for unknown@example.com
        return f"Error: Patient email {patient_email_to_find} not found in master CSV."

    # This part won't be reached for unknown@example.com, but demonstrates FileNotFoundError handling
    # if it were a valid patient with a missing JSON file.
    relative_json_path = file_path_series.iloc[0]
    json_file_path = JSON_BASE_DIR_PATH + "/" + "some_non_existent_file.json"
    with open(json_file_path, 'r') as f: # This would cause FileNotFoundError
        data = json.load(f)
    return data.get("patient_email_original")
"""
    print("\n--- Test 2: Code designed to show patient not found in CSV ---")
    result2 = run_generated_code(code_filenotfound_str, dummy_json_base_path, dummy_all_emails_csv, dummy_master_links_csv)
    print(f"Result 2: {result2}")
    assert not result2['success']
    assert "Patient email unknown@example.com not found" in result2['error']


    # Example 3: Code with a SyntaxError
    code_syntaxerror_str = """
def query_data_for_question() # Missing colon
    return "This won't compile"
"""
    print("\n--- Test 3: Code with SyntaxError ---")
    result3 = run_generated_code(code_syntaxerror_str, dummy_json_base_path, dummy_all_emails_csv, dummy_master_links_csv)
    print(f"Result 3: {result3}")
    assert not result3['success']
    assert "SyntaxError" in result3['error']

    # Example 4: Code with a KeyError
    code_keyerror_str = """
import json
import pandas as pd
def query_data_for_question():
    patient_email_to_find = "aaronmeers73@gmail.com"
    master_df = pd.read_csv(MASTER_LINKS_CSV_FILE_PATH)
    file_path_series = master_df[master_df["Patient Email"] == patient_email_to_find]["JSON File Path (Relative to Output Root)"]
    if file_path_series.empty: return "Error: Patient not found."
    relative_json_path = file_path_series.iloc[0]
    json_file_path = JSON_BASE_DIR_PATH + "/" + relative_json_path
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    # Intentional KeyError: 'non_existent_key'
    return data["non_existent_key"]
"""
    print("\n--- Test 4: Code with KeyError ---")
    result4 = run_generated_code(code_keyerror_str, dummy_json_base_path, dummy_all_emails_csv, dummy_master_links_csv)
    print(f"Result 4: {result4}")
    assert not result4['success']
    assert "KeyError" in result4['error']

    print("\n--- All tests finished ---")
