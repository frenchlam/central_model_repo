from pyspark.sql import SparkSession
from central_model_registry.feature_engineering import engineer_features


def test_preprocess():
    spark = SparkSession.builder.getOrCreate()

    df = spark.createDataFrame([[2.8, 3.1], [0.0, 20.2]]).toDF("fixed acidity", "volatile acidity")
    actual_df = df.transform(engineer_features)

    expected_df = spark.createDataFrame(
        [
            [2.8, 3.1, 5.9],
            [0.0, 20.2, 20.2],
        ]
    ).toDF("fixed acidity", "volatile acidity", "total_acidity")

    assert actual_df.collect() == expected_df.collect()
