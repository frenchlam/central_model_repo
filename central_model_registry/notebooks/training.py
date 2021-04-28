# Databricks notebook source
from datetime import datetime

import hyperopt as hp
from hyperopt import fmin, tpe, hp, SparkTrials, STATUS_OK
import mlflow
import mlflow.sklearn
from pyspark.sql import functions as F
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from central_model_registry.feature_engineering import engineer_features, rename_columns
from central_model_registry.mlflow_utils import register_best_model


experiment_name = "/experiments/central-model-registry-v1/"
model_name = "demo-cmr"
input_data_path = "dbfs:/databricks-datasets/wine-quality/winequality-red.csv"

now = datetime.now()
parent_run_name = now.strftime("%Y%m%d-%H%M")

# use central model registry
scope = "demo-cmr"
key = "cmr"
registry_uri = "databricks://" + scope + ":" + key
mlflow.set_registry_uri(registry_uri)

# COMMAND ----------

import mlflow
mlflow.get_registry_uri()

# COMMAND ----------

def evaluate_hyperparams_wrapper(X_train, X_test, y_train, y_test):
    def evaluate_hyperparams(params):
        min_samples_leaf = int(params['min_samples_leaf'])
        max_depth = params['max_depth']
        n_estimators = int(params['n_estimators'])

        rf = RandomForestRegressor(
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
            n_estimators=n_estimators,
        )
        rf.fit(X_train, y_train)

        mlflow.sklearn.log_model(rf, "model")

        predictions = rf.predict(X_test)
        mse = mean_squared_error(y_test, predictions)
        mae = mean_absolute_error(y_test, predictions)
        r2 = r2_score(y_test, predictions)

        mlflow.log_metric("mse", mse)
        mlflow.log_metric("mae", mae)
        mlflow.log_metric("r2", r2)

        return {'loss': mse, 'status': STATUS_OK}
  
    return evaluate_hyperparams

# COMMAND ----------

# MAGIC %md ## Train new model

# COMMAND ----------

mlflow.set_experiment(experiment_name)

# COMMAND ----------

raw_data = spark.read.format("csv").option("header", "true").option("sep", ";").load(input_data_path)
features = engineer_features(raw_data)
data = rename_columns(features).toPandas()

X_train, X_test, y_train, y_test = train_test_split(data.drop(["quality"], axis=1), data[["quality"]].values.ravel(), random_state=42)

search_space = {
    "n_estimators": hp.uniform("n_estimators", 20, 500),
    "min_samples_leaf": hp.uniform("min_samples_leaf", 1, 20),
    "max_depth": hp.uniform("max_depth", 2, 10),
}

spark_trials = SparkTrials(parallelism=4)

with mlflow.start_run(run_name=parent_run_name):
    fmin(
        fn=evaluate_hyperparams_wrapper(X_train, X_test, y_train, y_test),
        space=search_space,
        algo=tpe.suggest,
        max_evals=10,
        trials=spark_trials,
    )

# COMMAND ----------

# MAGIC %md ## Register new model version

# COMMAND ----------

model_details = register_best_model(model_name, experiment_name, parent_run_name, metric="mse")

# COMMAND ----------

print(f"New version: {model_details.version}")

# COMMAND ----------


