# Central Model Registry

While using this project, you need Python 3.X and `pip` or `conda` for package management.

## Installing project requirements

```bash
pip install -r unit-requirements.txt
```

## Unit testing

For local unit testing, please use `pytest`:
```
pytest tests/unit
```

## CI/CD pipeline settings

Please set the following secrets or environment variables. 
Follow the documentation for [GitHub Actions](https://docs.github.com/en/actions/reference) or for [Azure DevOps Pipelines](https://docs.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops&tabs=yaml%2Cbatch):
- `QA_HOST`
- `QA_TOKEN`

## Creating the distribution

To create the distribution:
```bash
python setup.py sdist bdist_wheel
```

## Saving the distribution to DBFS

With the databricks CLI:
```bash
databricks fs cp /local/path/to/your/wheel dbfs:/path/to/your/wheel --profile <dev-workspace-profile-name>
```

You can then install that wheel on your cluster by specifying path *dbfs:/path/to/your/wheel* in the Libraries tab of your cluster.

## Secret scopes 

According to the [documentation](https://docs.databricks.com/applications/machine-learning/manage-model-lifecycle/multiple-workspaces.html), a personal access token must be created in the central model registry and secrets must be created for each dev/qa/prod workspace to access the central model registry. Example with the databricks cli:
```bash
databricks secrets create-scope --scope <scope> --initial-manage-principal users --profile <my_env_profile>
databricks secrets put --scope <scope> --key <key>-host --string-value <workspace_url> --profile <my_env_profile>
databricks secrets put --scope <scope> --key <key>-token --string-value <personal_access_token> --profile <my_env_profile>
databricks secrets put --scope <scope> --key <key>-workspace-id --string-value <workspace_id> --profile <my_env_profile>
```

## Training and tracking a new model

Here is the process to train and track a new model version:
- if it's the first time you're training a model for this project or you made some modifications to the module that are taken into account in the training pipeline:
	- update the module's version in `central_model_registry/__init__.py`
	- rebuild the distribution via `python setup.py sdist bdist_wheel`
	- copy the wheel to DBFS in the dev environment (replace the paths): `databricks fs cp /path/to/new_wheel_version dbfs:/your/user/path/new_wheel_version --profile <dev-workspace-profile>`
- import training notebook from `central_model_registry/notebooks/training.py` to your dev environment
- if it's the first time you're training a model for this project, create the parent experiment directory in the dev environment: `/experiments/central-model-registry`
- use an interactive cluster and attach the training notebook
- install the wheel on the cluster, either as a cluster library or as a notebook-scoped library. If you're using a cluster library, make sure you remove existing (previous) versions of your wheel
- train models as you which (this is the part you can modify)
- register the best one if the performance is good enough
- check the new model version at the end of the notebook
- update the model version in file `model.json` with that new version


