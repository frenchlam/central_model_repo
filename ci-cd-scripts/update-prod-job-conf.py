from argparse import ArgumentParser
import json
import os
import requests


parser = ArgumentParser(description="Workspace conf")

parser.add_argument("--url", default=None, type=str, help="Workspace URL")
parser.add_argument("--pat", default=None, type=str, help="Personal Access Token")
parser.add_argument("--path", default=None, type=str, help="Absolute path to the distribution directory")

args = parser.parse_args()


worskpace_url = args.url.strip("/")
submit_url = f"{worskpace_url}/api/2.0/jobs/update"
headers = {"Authorization": f"Bearer {args.pat}"}

whl_file_name = [x for x in os.listdir(args.path) if x.endswith(".whl")][0]

data = {
  "job_id": 1,
  "new_settings": {
    "libraries": [
    	{
    		"whl": f"dbfs:/projects/Central-Model-Registry/versions/{whl_file_name}"
		}
	]
  },
}

# TODO: raise error if not 200, or check that new wheel file has been used
requests.post(submit_url, data=json.dumps(data), headers=headers)
