from argparse import ArgumentParser
import requests
import json
import sys


parser = ArgumentParser(
    description='Parameters used to compute most frequent pages per subdomain',
)

parser.add_argument("--url", default=None, type=str, help="Workspace URL")
parser.add_argument("--pat", default=None, type=str, help="Personal Access Token")
parser.add_argument("--path", default=None, type=str, help="Absolute path to model metadata json file")

args = parser.parse_args()

worskpace_url = args.url.strip("/")

headers = {"Authorization": f"Bearer {args.pat}"}


# load model version to test
with open(args.path) as json_file:
    model_metadata = json.load(json_file)


# Check current stage before transitioning
model_name_and_version = {
    "name": model_metadata["model_name"],
    "version": model_metadata["model_version"],
}

current_stage_req = requests.get(f"{worskpace_url}/api/2.0/mlflow/model-versions/get", data=json.dumps(model_name_and_version), headers=headers)
current_stage = current_stage_req.json()["model_version"]["current_stage"]

if current_stage != "None":
    print(f"Model stage is '{current_stage}' != 'None' which means no new model was created. Skipping transition to Staging.")
    sys.exit()

# transition staging model to prod
new_model_to_staging_data = {
    "name": model_metadata["model_name"],
    "version": model_metadata["model_version"],
    "stage": "Staging",
    "archive_existing_versions": "False",
}

new_model_to_staging_req = requests.post(f"{worskpace_url}/api/2.0/mlflow/model-versions/transition-stage", data=json.dumps(new_model_to_staging_data), headers=headers)
print("Moved new model to staging")
