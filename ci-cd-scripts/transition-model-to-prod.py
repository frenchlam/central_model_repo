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

workspace_url = args.url.strip("/")

headers = {"Authorization": f"Bearer {args.pat}"}


# load model version to test
with open(args.path) as json_file:
    model_metadata = json.load(json_file)

# check that new model version's stage is Staging
new_model_data = {
    "name": model_metadata["model_name"],
    "version": model_metadata["model_version"],
}

new_model_resp = requests.get(
    f"{workspace_url}/api/2.0/mlflow/model-versions/get",
    data=json.dumps(new_model_data),
    headers=headers,
)

new_model_current_stage = new_model_resp.json()["model_version"]["current_stage"]
# NB: this we will have to proceed differently when we allow automatic retraining
if new_model_current_stage == "Production":
    print(f'Model {model_metadata["model_name"]} version {model_metadata["model_version"]} is already in Production: no new model was created.')
    print("Skipping any transition.")
    sys.exit()

# retrieve current prod model version
old_prod_model_data = {
    "name": model_metadata["model_name"],
    "stages": ["Production"],
}

old_prod_model_resp = requests.get(
    f"{workspace_url}/api/2.0/mlflow/registered-models/get-latest-versions",
    data=json.dumps(old_prod_model_data),
    headers=headers,
)

# transition staging model to prod
new_model_to_prod_data = {
    "name": model_metadata["model_name"],
    "version": model_metadata["model_version"],
    "stage": "Production",
    "archive_existing_versions": "False",
}

new_model_to_prod_resp = requests.post(
    f"{workspace_url}/api/2.0/mlflow/model-versions/transition-stage",
    data=json.dumps(new_model_to_prod_data),
    headers=headers,
)
print(f'Transitioned model {model_metadata["model_name"]} version {model_metadata["model_version"]} from {new_model_current_stage} to Production')

if not old_prod_model_resp.json():
    print(f'There was no model {model_metadata["model_name"]} in Production before, no need to archive it then.')
else:
    # transition old prod model to archived
    # NB: this assumes we have only one model in production at any given time
    old_prod_model_version = old_prod_model_resp.json()["model_versions"][0]["version"]

    old_prod_model_to_archived_data = {
        "name": model_metadata["model_name"],
        "version": old_prod_model_version,
        "stage": "Archived",
        "archive_existing_versions": "False",
    }

    old_prod_model_to_archived_resp = requests.post(
        f"{workspace_url}/api/2.0/mlflow/model-versions/transition-stage",
        data=json.dumps(old_prod_model_to_archived_data),
        headers=headers,
    )
    print(f'Transitioned old Production model {model_metadata["model_name"]} version {old_prod_model_version} to Archived')
