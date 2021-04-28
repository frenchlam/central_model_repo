# Databricks notebook source
dbutils.widgets.text("input_path", "dbfs:/databricks-datasets/wine-quality/winequality-red.csv", "input_path")
dbutils.widgets.text("output_path", "dbfs:/project/central_model_registry/predictions", "output_path")

# COMMAND ----------

import mlflow
from mlflow.tracking import MlflowClient
from pyspark.sql import functions as F

from central_model_registry.feature_engineering import engineer_features, rename_columns


# use central model registry
scope = "demo-cmr"
key = "cmr"
registry_uri = 'databricks://' + scope + ':' + key
mlflow.set_registry_uri(registry_uri)

model_name = "demo-cmr"
input_path = dbutils.widgets.get("input_path")
output_path = dbutils.widgets.get("output_path")

# COMMAND ----------

client = MlflowClient()
model_udf = mlflow.pyfunc.spark_udf(spark, f"models:/{model_name}/Production")
model_version = client.get_latest_versions(model_name, stages=["Production"])[0].version

raw_data = spark.read.format("csv").option("header", "true").option("sep", ";").load(input_path).drop("quality")
features = engineer_features(raw_data)
data = rename_columns(features)

preds = (
  data
    .withColumn("prediction", model_udf(*data.columns))
    .withColumn("model_version", F.lit(model_version))
)

preds.write.format("delta").mode("overwrite").save(output_path)

# COMMAND ----------
