# Databricks notebook source
# MAGIC %md # Test model performance
# MAGIC 
# MAGIC The goal of this notebook is to make sure the performance of the new model is better than the performance of the current model in production.

# COMMAND ----------

# MAGIC %md ## Setup

# COMMAND ----------

dbutils.widgets.text("model_version", "", "model_version")

# COMMAND ----------

NOTEBOOK_VERSION = "0.0.3"

import mlflow
from mlflow.tracking.client import MlflowClient
from sklearn.metrics import mean_squared_error

from central_model_registry.feature_engineering import engineer_features, rename_columns

model_name = "demo-cmr"
model_version = dbutils.widgets.get("model_version")

test_data_path = "dbfs:/databricks-datasets/wine-quality/winequality-red.csv"

# use central model registry
scope = "demo-cmr"
key = "cmr"
registry_uri = 'databricks://' + scope + ':' + key
mlflow.set_registry_uri(registry_uri)

# COMMAND ----------

# MAGIC %md ## Read new model version

# COMMAND ----------

client = MlflowClient()

model_udf = mlflow.pyfunc.spark_udf(spark, f"models:/{model_name}/{model_version}")

# COMMAND ----------

# MAGIC %md ## Model's stage should be None, if not then we're using the wrong model version

# COMMAND ----------

current_stage = client.get_model_version(model_name, model_version).current_stage
if current_stage != "None":
  raise Exception(f"Bad current stage '{current_stage}' for model version {model_version}. Should be None.")

# COMMAND ----------

# MAGIC %md ## Make predictions on test data

# COMMAND ----------

test_data = spark.read.format("csv").option("header", "true").option("sep", ";").load(test_data_path)
features = engineer_features(test_data)
data = rename_columns(features)

preds = data.withColumn("prediction", model_udf(*data.drop("quality").columns)).select("quality", "prediction").toPandas() # it's okay since dataframe is small
mse = mean_squared_error(preds["quality"], preds["prediction"])
print(f"MSE: {mse}")

# COMMAND ----------
