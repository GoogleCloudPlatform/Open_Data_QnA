echo "#####################################################################################"
echo "                              STARTING DEPLOYMENT                                    "
echo "#####################################################################################"

original_dir=$(pwd)
echo "Current Working Directory: $original_dir"
echo "-------------------------------------------------------------------------------------"
echo "                             EXECUTING TERRAFORM                                     "
echo "-------------------------------------------------------------------------------------"
terraform init && \
terraform apply -var=project_id=$(gcloud config get project) -auto-approve || exit 1
echo "-------------------------------------------------------------------------------------"
echo "                        TERRAFORM EXECUTION SUCCESSFUL                               "
echo "-------------------------------------------------------------------------------------"
echo "The below values from terraform output will be used for deployment of frontend and backend services:" 

cloudrun_service_name=$(terraform output -raw service_name)
echo "cloudrun_service_name: $cloudrun_service_name"
project_id=$(terraform output -raw project_id)
echo "project_id: $project_id"
deploy_region=$(terraform output -raw deploy_region)
echo "deploy_region: $deploy_region"
service_account=$(terraform output -raw service_account)
echo "service_account: $service_account"

echo "-------------------------------------------------------------------------------------"
echo "                        DEPLOYING BACKEND CLOUD RUN                                  "
echo "-------------------------------------------------------------------------------------"
sh scripts/backend-deployment.sh --servicename $cloudrun_service_name --project $project_id --region $deploy_region --sa $service_account || exit 1

echo "-------------------------------------------------------------------------------------"
echo "                        BACKEND DEPLOYMENT SUCCESSFUL                                "
echo "-------------------------------------------------------------------------------------"

echo "Current working directory: $original_dir"
echo "-------------------------------------------------------------------------------------"
echo "                        DEPLOYING FRONTEND SERVICE                                   "
echo "-------------------------------------------------------------------------------------"
sh scripts/frontend-deployment.sh --project $project_id --region $deploy_region || exit 1
echo "-------------------------------------------------------------------------------------"
echo "                      FRONTEND DEPLOYMENT SUCCESSFUL                                 "
echo "-------------------------------------------------------------------------------------"

echo "#####################################################################################"
echo "        APPLICATION DEPLOYMENT COMPLETED! PLEASE FOLLOW README FOR NEXT STEPS        "
echo "#####################################################################################"
