

usage() {
    echo "Usage: $0 --project <your_project_id>"
    exit 1  # Indicate an error
}

# Function to validate a parameter's value
validate_param() {
    local param_name="$1"
    local param_value="$2"

    if [[ -z "$param_value" ]]; then
        echo "Error: Parameter '$param_name' cannot be empty."
        usage  # Show usage and exit if the value is empty
    fi
}

# Check if enough arguments are provided
if [[ $# -lt 2 ]]; then  
    echo "Error: Insufficient arguments."
    usage
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project)
            validate_param "$1" "$2"
            PROJECT_ID=$2
            shift 2  # Move to the next parameter
            ;;
        *)  
            echo "Error: Unknown parameter '$1'."
            usage
            ;;
    esac
done

main(){
    pwd
    cd ../frontend
    gcloud builds submit . --config frontend.yaml --substitutions _FIREBASE_PROJECT_ID=$PROJECT_ID --project=$PROJECT_ID
}

main