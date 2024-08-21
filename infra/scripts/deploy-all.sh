original_dir=$(pwd)
echo "$original_dir"
terraform init
terraform apply -var=project_id=$(gcloud config get project) -auto-approve

cloudrun_service_name=$(terraform output -raw service_name)
echo "$cloudrun_service_name"
project_id=$(terraform output -raw project_id)
echo "$project_id"
deploy_region=$(terraform output -raw deploy_region)
echo "$deploy_region"
service_account=$(terraform output -raw service_account)
echo "$service_account"

sh scripts/backend-deployment.sh --servicename $cloudrun_service_name --project $project_id --region $deploy_region --sa $service_account

cd "$original_dir"

sh scripts/frontend-deployment.sh --project $project_id