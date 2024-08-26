usage() {
    echo "Usage: $0 --servicename <cloudrun_service_name> --project <your_project_id> --region <region> --sa <your_cloud_run_sa>"
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
if [ $# -lt 8 ]; then  
    echo "Error: Insufficient arguments."
    usage
fi

# Parse and validate named parameters
while [ $# -gt 0 ]; do
    case "$1" in
        --servicename)
            validate_param "$1" "$2"
            SERVICE_NAME=$2
            shift 2  # Move to the next parameter
            ;;
        --project)
            validate_param "$1" "$2"
            PROJECT_ID=$2
            shift 2  # Move to the next parameter
            ;;
        --region)
            validate_param "$1" "$2"
            DEPLOY_REGION=$2
            shift 2
            ;;
        --sa)
            validate_param "$1" "$2"
            SERVICE_ACCOUNT=$2
            shift 2
            ;;
        *)  
            echo "Error: Unknown parameter '$1'."
            usage
            ;;
    esac
done

# Deploys backend to Cloud Run using the provided region and service account
main(){
    pwd
    cd ../backend-apis

    echo "Setting orgpolicy to allow all IAM domains"
    
    gcloud resource-manager org-policies set-policy --project=$PROJECT_ID policy.yaml || exit 1 #This command will create policy that overrides to allow all domain
    
    cd ../
    
    echo "Deploying cloud run service.."
    pwd
    gcloud beta run deploy $SERVICE_NAME --region $DEPLOY_REGION --source . --service-account=$SERVICE_ACCOUNT --service-min-instances=1  --allow-unauthenticated --project=$PROJECT_ID || exit 1

    echo "Deleting the previously create dorg policy.."

    gcloud resource-manager org-policies delete iam.allowedPolicyMemberDomains --project=$PROJECT_ID || exit 1

}

main
