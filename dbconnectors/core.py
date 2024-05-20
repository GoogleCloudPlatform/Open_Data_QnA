# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



"""
Provides the base class for all Connectors 
"""


from abc import ABC


class DBConnector(ABC):
    """
    The core class for all Connectors
    """

    connectorType: str = "Base"

    def __init__(self,
                project_id:str, 
                region:str, 
                instance_name:str,
                database_name:str, 
                database_user:str, 
                database_password:str,
                dataset_name:str):
        """
        Args:
            project_id (str | None): GCP Project Id.
            dataset_name (str): 
            TODO
        """
        self.project_id = project_id
        self.region = region 
        self.instance_name = instance_name 
        self.database_name = database_name
        self.database_user = database_user
        self.database_password = database_password
        self.dataset_name = dataset_name
    