# Databricks notebook source
# MAGIC %md # Test model integration
# MAGIC 
# MAGIC The goal of this notebook is to make sure the end-to-end process doesn't break.

# COMMAND ----------

# MAGIC %md ## Setup

# COMMAND ----------

dbutils.widgets.text("model_version", "", "model_version")

# COMMAND ----------

NOTEBOOK_VERSION = "0.0.3"

import mlflow
from mlflow.tracking.client import MlflowClient
from pyspark.sql import functions as F

from central_model_registry.feature_engineering import engineer_features, rename_columns

model_name = "demo-cmr"
model_version = dbutils.widgets.get("model_version")

input_path = "dbfs:/databricks-datasets/wine-quality/winequality-red.csv"
output_path = "dbfs:/project/central_model_registry/predictions"

# use central model registry
scope = "demo-cmr"
key = "cmr"
registry_uri = 'databricks://' + scope + ':' + key
mlflow.set_registry_uri(registry_uri)

# COMMAND ----------

# clean environment
dbutils.fs.rm(output_path, True)

# COMMAND ----------

# MAGIC %md ## Read new model version

# COMMAND ----------

client = MlflowClient()
model_udf = mlflow.pyfunc.spark_udf(spark, f"models:/{model_name}/{model_version}")

# COMMAND ----------

# MAGIC %md ## Make predictions on test data

# COMMAND ----------

test_data = spark.read.format("csv").option("header", "true").option("sep", ";").load(input_path).drop("quality")
features = engineer_features(test_data)
data = rename_columns(features)

preds = (
  data
    .withColumn("prediction", model_udf(*data.columns))
    .withColumn("model_version", F.lit(model_version))
)

preds.write.format("delta").mode("overwrite").save(output_path)
