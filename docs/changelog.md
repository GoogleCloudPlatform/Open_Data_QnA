# Release Notes - Open Data QnA v1.2.0
This release brings significant improvements and new features to enhance the stability, functionality, and user experience of the Open Data QnA.

## 🗝️ Key Enhancements:
* **Enhanced Functionality:** Added the ability to specify a list of table names to be processed in BQ, instead of parsing all tables in a dataset. 
* **Improved Debugging:** The SQL debugger now incorporates the user's question into its prompts, leading to more accurate and relevant debugging suggestions.
* **Simplified Setup:** Streamlined notebook setup and environment variable management for a smoother user experience.
* **Quickstart**: Added a standalone notebook for quick experimentation with the overall approach, limited to BQ. 
* **Flexible Configuration:** Introduced optional arguments for the CLI pipeline, allowing users to customize various parameters like table and column similarity thresholds.
* **Code Refinements:** Removed hardcoded embedding models and added a save_config function for cleaner configuration management.
* **Bug Fixes:** Resolved various bugs, including issues with root directory checking, utility initialization, source type determination, and safety settings.
* **Expanded Documentation:** Added comprehensive docstrings to functions for better clarity and understanding.

## 📈 Additional Improvements:
* **Code Cleanup:** Removed unnecessary files and redundant code, improving overall code maintainability.
* **Updated README:** Improved the README file with clearer instructions and updated information.
* **Enhanced User Interface:** Introduced a CLI approach (experimental) for more streamlined interaction.

## 🐜 Bug Fixes:
* Fixed bugs in standalone notebook functionality.
* Removed telemetry test code.
* Corrected embedding distances in BigQuery.
* Resolved various typos and inconsistencies in the codebase.

This release marks a significant step forward in the development of the Open Data QnA SQL Generation tool, making it more reliable, flexible, and user-friendly. We encourage you to upgrade and explore the new features!
