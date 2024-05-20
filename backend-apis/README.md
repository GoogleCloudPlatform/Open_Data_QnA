



<h3 style="text-align:center;"> Create Endpoints </h3>

   Here we are going to create publicly accessible endpoints (no authentication) .

   If you're working on a managed GCP project, it is common that there would be Domain Restricted Sharing Org Policies that will not allow the creation of a public facing endpoint.

   So we can allow all the domains and re-enable the same policy so that we don’t change the existing policy.

   Please run the below command before proceeding ahead. You need to have Organization Policy Admin rights to run the below commands.
```
export PROJECT_ID=<PROJECT_ID>
```

```
cd applied-ai-engineering-samples
git checkout opendataqna
cd backend-apis

gcloud resource-manager org-policies set-policy --project=$PROJECT_ID policy.yaml #This command will create policy that overrides to allow all domain

```

Create the service account and add roles to run the solution backend for the APIs

```
gcloud iam service-accounts create opendataqna --project=$PROJECT_ID
gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:opendataqna@$PROJECT_ID.iam.gserviceaccount.com --role='roles/cloudsql.client' --project=$PROJECT_ID --quiet
gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:opendataqna@$PROJECT_ID.iam.gserviceaccount.com --role='roles/bigquery.admin' --project=$PROJECT_ID --quiet
gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:opendataqna@$PROJECT_ID.iam.gserviceaccount.com --role='roles/aiplatform.user' --project=$PROJECT_ID --quiet

```



**Technologies**

* **Programming language:** Python
* **Framework:** Flask

**Before you start :** Ensure all variables in your config.ini file are correct, especially those for your Postgres instance and BigQuery dataset. If you need to change the Postgres instance or BigQuery dataset values, update the config.ini file before proceeding.   


   The endpoints deployed here are completely customized for the UI built in this demo solution. Feel free to customize the endpoint if needed for different UI/frontend. The gcloud run deploy command create a cloud build that uses the Dockerfile in the OpenDataQnA folder
    
  ***Deploy endpoints to Cloud Run***

```
export PROJECT_ID=<Enter your Project ID>
 ```
 ```
export SERVICE_NAME=opendataqna #change the name if needed 
export DEPLOY_REGION=us-central1 #change the cloud run deployment region if needed 
```
```
 cd applied-ai-engineering-samples
 git checkout opendataqna

 gcloud beta run deploy $SERVICE_NAME --region $DEPLOY_REGION --source . --service-account=opendataqna@$PROJECT_ID.iam.gserviceaccount.com --service-min-instances=1  --allow-unauthenticated --project=$PROJECT_ID 
 
 #if you are deploying cloud run application for the first time in the project you will be prompted for a couple of settings. Go ahead and type Yes.


```

   Once the deployment is done successfully you should be able to see the Service URL (endpoint point) link as shown below. Please keep this handy to add this in the frontend or you can get this uri from the cloud run page in the GCP Console. e.g. *https://OpenDataQnA-aeiouAEI-uc.a.run.app*

   Test if the endpoints are working with below command. This should return the dataset your created in the source env setup notebook.
```
 curl <URI of the end point>/available_databases

```



<p align="center">
    <a href="../utilities/imgs/Cloud Run Deploy.png">
        <img src="../utilities/imgs/Cloud Run Deploy.png" alt="aaie image">
    </a>
</p>


  Delete the Org Policy on the Project that's created above. Do not run this if you haven’t created the org policy above

```
gcloud resource-manager org-policies delete iam.allowedPolicyMemberDomains --project=$PROJECT_ID
```



**API Details**

   All the payloads are in JSON format

1. List Databases : Get the available databases in the vector store that solution can run against

    URI: {Service URL}/available_databases 
    Complete URL Sample : https://OpenDataQnA-aeiouAEI-uc.a.run.app/available_databases

    Method: GET

    Request Payload : NONE

    Request response:
    ```
    {
    "Error": "",
    "KnownDB": "[{\"table_schema\":\"imdb-postgres\"},{\"table_schema\":\"retail-postgres\"}]",
    "ResponseCode": 200
    }
    ```

2. Known SQL : Get suggestive questions (previously asked/examples added) for selected database

    URI: /get_known_sql
    Complete URL Sample : https://OpenDataQnA-aeiouAEI-uc.a.run.app/get_known_sql   

    Method: POST

    Request Payload :

    ```
    {
    "user_database":"retail"
    }
    ```

    Request response:

    ```
    {
    "Error": "",
    "KnownSQL": "[{\"example_user_question\":\"Which city had maximum number of sales and what was the count?\",\"example_generated_sql\":\"select st.city_id, count(st.city_id) as city_sales_count from retail.sales as s join retail.stores as st on s.id_store = st.id_store group by st.city_id order by city_sales_count desc limit 1;\"}]",
    "ResponseCode": 200
    }
    ```


3. SQL Generation : Generate the SQL for the input question asked aganist a database

    URI: /generate_sql


    Method: POST

    Complete URL Sample : https://OpenDataQnA-aeiouAEI-uc.a.run.app/get_known_sql


    Request payload:

    ```
    {
    "user_question":"Which city had maximum number of sales?",
    "user_database":"retail"
    }
    ```


    Request response:
    ```
    {
    "Error": "",
    "GeneratedSQL": " select st.city_id from retail.sales as s join retail.stores as st on s.id_store = st.id_store group by st.city_id order by count(*) desc limit 1;",
    "ResponseCode": 200
    }
    ```


4. Execute SQL : Run the SQL statement against provided database source

    URI:/run_query
    Complete URL Sample : https://OpenDataQnA-aeiouAEI-uc.a.run.app/run_query

    Method: POST

    Request payload:
    ```
    { "user_database": "retail",
    "generated_sql":"select st.city_id from retail.sales as s join retail.stores as st on s.id_store = st.id_store group by st.city_id order by count(*) desc limit 1;"
    }
    ```

    Request response:
    ```
    {
    "Error": "",
    "KnownDB": "[{\"city_id\":\"C014\"}]",
    "ResponseCode": 200
    }
    ```
5. Embedd SQL : To embed known good SQLs to your example embeddings

    URI:/embed_sql
    Complete URL Sample : https://OpenDataQnA-aeiouAEI-uc.a.run.app/embed_sql

    METHOD: POST

    Request Payload:

    ```
    {
    "user_question":"Which city had maximum number of sales?",
    "generated_sql":"select st.city_id from retail.sales as s join retail.stores as st on s.id_store = st.id_store group by st.city_id order by count(*) desc limit 1;",
    "user_database":"retail"
    }
    ```

    Request response:
    ```
    {
    "ResponseCode" : 201, 
    "Message" : "Example SQL has been accepted for embedding",
    "Error":""
    }
    ```
6. Generate Visualization Code : To generated javascript Google Charts code based on the SQL Results and display them on the UI

    As per design we have two visualizations suggested showing up when the user clicks the visualize button. Hence two divs are send as part of the response “chart_div”, “chart_div_1” to bind them to that element in the UI
        

    If you are only looking to setup enpoint you can stop here. In case you require the demo app (frontend UI) built in the solution, proceed to the next step.

    URI:/generate_viz
    Complete URL Sample : https://OpenDataQnA-aeiouAEI-uc.a.run.app/generate_viz
    
    METHOD: POST

    Request Payload:
    ```
      {
      "user_question": "What are top 5 product skus that are ordered?",
      "sql_generated": "SELECT productSKU as ProductSKUCode, sum(total_ordered) as TotalOrderedItems FROM `inbq1-joonix.demo.sales_sku` group by productSKU order by sum(total_ordered) desc limit 5",
      "sql_results": [
        {
          "ProductSKUCode": "GGOEGOAQ012899",
          "TotalOrderedItems": 456
        },
        {
          "ProductSKUCode": "GGOEGDHC074099",
          "TotalOrderedItems": 334
        },
        {
          "ProductSKUCode": "GGOEGOCB017499",
          "TotalOrderedItems": 319
        },
        {
          "ProductSKUCode": "GGOEGOCC077999",
          "TotalOrderedItems": 290
        },
        {
          "ProductSKUCode": "GGOEGFYQ016599",
          "TotalOrderedItems": 253
        }
      ]
    }
    
    ```

    Request response:
    ```
    {
    "Error": "",
    "GeneratedChartjs": {
        "chart_div": "google.charts.load('current', {\n  packages: ['corechart']\n});\ngoogle.charts.setOnLoadCallback(drawChart);\n\nfunction drawChart() {\n  var data = google.visualization.arrayToDataTable([\n    ['Product SKU', 'Total Ordered Items'],\n    ['GGOEGOAQ012899', 456],\n    ['GGOEGDHC074099', 334],\n    ['GGOEGOCB017499', 319],\n    ['GGOEGOCC077999', 290],\n    ['GGOEGFYQ016599', 253],\n  ]);\n\n  var options = {\n    title: 'Top 5 Product SKUs Ordered',\n    width: 600,\n    height: 300,\n    hAxis: {\n      textStyle: {\n        fontSize: 12\n      }\n    },\n    vAxis: {\n      textStyle: {\n        fontSize: 12\n      }\n    },\n    legend: {\n      textStyle: {\n        fontSize: 12\n      }\n    },\n    bar: {\n      groupWidth: '50%'\n    }\n  };\n\n  var chart = new google.visualization.BarChart(document.getElementById('chart_div'));\n\n  chart.draw(data, options);\n}\n",
        
        "chart_div_1": "google.charts.load('current', {'packages':['corechart']});\ngoogle.charts.setOnLoadCallback(drawChart);\nfunction drawChart() {\n  var data = google.visualization.arrayToDataTable([\n    ['ProductSKUCode', 'TotalOrderedItems'],\n    ['GGOEGOAQ012899', 456],\n    ['GGOEGDHC074099', 334],\n    ['GGOEGOCB017499', 319],\n    ['GGOEGOCC077999', 290],\n    ['GGOEGFYQ016599', 253]\n  ]);\n\n  var options = {\n    title: 'Top 5 Product SKUs that are Ordered',\n    width: 600,\n    height: 300,\n    hAxis: {\n      textStyle: {\n        fontSize: 5\n      }\n    },\n    vAxis: {\n      textStyle: {\n        fontSize: 5\n      }\n    },\n    legend: {\n      textStyle: {\n        fontSize: 10\n      }\n    },\n    bar: {\n      groupWidth: \"60%\"\n    }\n  };\n\n  var chart = new google.visualization.ColumnChart(document.getElementById('chart_div_1'));\n\n  chart.draw(data, options);\n}\n"
    },
    "ResponseCode": 200
    }

    ```


### For setting up the demo UI with these endpoints please refer to README.md under [`/frontend`](/frontend/)
