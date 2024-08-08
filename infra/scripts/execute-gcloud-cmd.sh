export PROJECT_ID=$1
export SETPOLICY=$2
cd ../backend-apis

if [ $SETPOLICY = "YES" ]
then
        echo "Enforcing Org Policy.."
        gcloud resource-manager org-policies set-policy --project=$PROJECT_ID policy.yaml #This command will create policy that overrides to allow all domain
else
        echo "Deleting Org Policy.."
        gcloud resource-manager org-policies delete iam.allowedPolicyMemberDomains --project=$PROJECT_ID
fi
