<h3 style="text-align:center;"> Deploy Frontend Demo UI </h3>

**Technologies and Components**

* **Framework:** Angular
* **Hosting Platform:** Firebase

**Note** : This UI demo doesn't configure any domain restrictions. If you choose to build one refer to this link https://firebase.google.com/docs/functions/auth-blocking-events?gen=2nd#only_allowing_registration_from_a_specific_domain

1. Install the firebase tools to run CLI commands
    ```
    cd applied-ai-engineering-samples

    npm install -g firebase-tools

    ```
    ```
    export PROJECT_ID=<Enter Project ID>
    export REGION=<Region for deploy and builds>
    ```


2. Build the firebase community builder image

    Cloud Build provides a Firebase community builder image that you can use to invoke firebase commands in Cloud Build. To use this builder in a Cloud Build config file, you must first build the image and push it to the Container Registry in your project.

    **Note**:*Please complete the steps carely and use the same project which you are going to host the app*

    Follow detailed instructions:
    
    1. Navigate to your project root directory.
    2. Clone the cloud-builders-community repository:

    ```
    git clone https://github.com/GoogleCloudPlatform/cloud-builders-community.git
    ```
    3. Navigate to the firebase builder image:

    ```
    cd cloud-builders-community/firebase 
    ```
    4. Submit the builder to your project, where REGION is one of the supported build regions: 

    ```
    gcloud builds submit --region=$REGION . --project=$PROJECT_ID
    ```

    5. Navigate back to your project root directory:
    
    ```
    cd ../..
    ```
 
    6. Remove the repository from your root directory:
    ```
    rm -rf cloud-builders-community/
    ```


4. Configure Firebase

    Login into firebase console (https://console.firebase.google.com/) and create project “Add existing GCP project” select your GCP project that you are using for the deployment of firebase. 

    Choose pay as you go plan and turn off Google Analytics and create.

    Once you added the project to firebase navigate and select your project

   * Navigate to Project Settings > General

   * Add App and select Web

   * Fill the details e.g. Nickname : opendataqna and just register the app

   * Once done continue back the general page and you should see the app

   * Add the linked firebase project as the same that your initialize firebase for hosting (same as the selected)

   * Copy the config object you will use in your app code in the later step


    <p align="center">
        <a href="../utilities/imgs/Firebase Config .png">
            <img src="../utilities/imgs/Firebase Config.png" alt="aaie image">
        </a>
    </p>


    * Navigate to Build>Authentication

    * Under Sign-in Method add provider as Google


4. Initialize Firebase

    ```
    cd applied-ai-engineering-samples

    cd frontend

    firebase login --no-localhost

    firebase init hosting 

    ```

    * firebase login --reauth --no-localhost # this command can be used re authenticate in case of authentication errors

    * Use the down arrow to select the option Use an existing project

    * For the public directory prompt provide >> /dist/frontend/browser
    
    * Rewrite all URLs to index prompt enter >> Yes (Enter No for any other options)

    * You should now see firebase.json created in the folder 



5. Update the Config Object and Endpoint URLs for the frontend

    In the file [`/frontend/src/assets/constants.ts`](/frontend/src/assets/constants.ts) replace the config object with the one you copied in the above step and replace the ENDPOINT_OPENDATAQNA with the Service URL from the Endpoint Deployment section above.

    ***Note that these variables need to be exported using "export" keyword. So make sure export is mentioned for both the variables***

    <p align="center">
        <a href="../utilities/imgs/constants update.png">
            <img src="../utilities/imgs/constants update.png" alt="aaie image">
        </a>
    </p>

6. Deploy the app

    Setup IAM permissions for the cloudbuild service account to deploy

    * Open the IAM page in the Google Cloud console

    * Select your project and click Open.

    * In the permissions table, locate the email ending with @cloudbuild.gserviceaccount.com, and click on the pencil icon. This is the Cloud Build service account. (If you cannot find it check the box on the top right of permissions list which say Include Google-provided role grants)

    * Add Cloud Build Service Account, Firebase Admin and API Keys Admin roles.

    * Click Save.

    
    Run the below commands on the terminal

    ```
    gcloud services enable firebase.googleapis.com # Enable firebase management API

    cd applied-ai-engineering-samples
    git checkout opendataqna
    cd frontend
    ```
    ```
    gcloud builds submit . --config frontend.yaml --substitutions _FIREBASE_PROJECT_ID=<Enter Project Id of the firebase> --project_id=$PROJECT_ID

    ```
    


    You can see the app URL at the end of successful deployment

    > Once deployed login if your Google Account > Select Business User > Select a database in the dropdown (top right) > Type in the Query > Hit Query

    A successful SQL generated will be show as below

    <p align="center">
        <a href="../utilities/imgs/App generate sql .png">
            <img src="../utilities/imgs/App generate sql .png" alt="aaie image">
        </a>
    </p>

    Hit on Result and then Visualize to see the results and charts as below

    <p align="center">
        <a href="../utilities/imgs/App Result and Viz.png">
            <img src="../utilities/imgs/App Result and Viz.png" alt="aaie image">
        </a>
    </p>


