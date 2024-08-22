

usage() {
    echo "Usage: $0 --project <your_project_id> --region <region>"
    exit 1  # Indicate an error
}

# Function to validate a parameter's value
validate_param() {
    local param_name="$1"
    local param_value="$2"

    if [ -z "$param_value" ]; then
        echo "Error: Parameter '$param_name' cannot be empty."
        usage  # Show usage and exit if the value is empty
    fi
}

# Check if enough arguments are provided
if [ $# -lt 4 ]; then  
    echo "Error: Insufficient arguments."
    usage
fi

while [ $# -gt 0 ]; do
    case "$1" in
        --project)
            validate_param "$1" "$2"
            PROJECT_ID=$2
            shift 2  # Move to the next parameter
            ;;
        --region)
            validate_param "$1" "$2"
            REGION=$2
            shift 2
            ;;
        *)  
            echo "Error: Unknown parameter '$1'."
            usage
            ;;
    esac
done

main(){
    pwd
    cd ../..
    pwd
    git clone https://github.com/GoogleCloudPlatform/cloud-builders-community.git
    cd cloud-builders-community/firebase 
    gcloud builds submit --region=$REGION . --project=$PROJECT_ID
    cd ../..
    rm -rf cloud-builders-community/
    cd Open_Data_QnA/frontend
    gcloud builds submit . --config frontend.yaml --substitutions _FIREBASE_PROJECT_ID=$PROJECT_ID --project=$PROJECT_ID
}

main