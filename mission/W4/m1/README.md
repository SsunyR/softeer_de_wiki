# W4M1 실행

## Files

- 디렉토리 구조

        .
        ├── docker-compose.yaml
        ├── Dockerfile
        ├── README.md
        ├── data/
        │   ├── spark-example.py
        │   ├── csv/
        │   └── scripts/
        │       ├── spark_pi.sh
        │       └── spark_example.sh
        ├── conf/
        │   └── spark-defaults.conf
        └── logs/
            ├── master/
            ├── worker1/
            └── worker2/

- spark-example.py

        from pyspark.sql import SparkSession

        spark = SparkSession.builder \
            .appName("PySparkBasicExample") \
            .getOrCreate()

        data = [("Alice", 1, "New York"),
                ("Bob", 2, "London"),
                ("Charlie", 3, "Paris"),
                ("David", 1, "New York")]
        columns = ["Name", "ID", "City"]

        df = spark.createDataFrame(data, schema=columns)

        print("DataFrame Schema:")
        df.printSchema()

        print("\nOriginal DataFrame:")
        df.show()

        filtered_df = df.filter(df["City"] == "New York")

        print("\nFiltered DataFrame (City = 'New York'):")
        filtered_df.show()

        filtered_df.repartition(1) \
        .write \
        .format("csv") \
        .option("header", "true") \
        .mode("overwrite") \
        .save("/opt/spark/local/csv")

        spark.stop()

## Step-By-Step Execution

1. 아래 명령어를 통해 Spark standalone cluster를 실행.

        user$ docker-compose up --build -d

2. 아래 명령어를 통해 모든 컨테이너가 실행 중인지 확인.

        user$ spark$ docker ps

3. 아래 명령어를 통해 spark-master 컨테이너에 연결.

        user$ docker exec -it spark-master bash

4. <http://localhost:8080/> 에서 Spark 클러스터의 상태를 Web UI로 확인.

5. 아래와 같은 명령어를 통해 pi 계산 spark 작업 수행.

        spark$ . local/scripts/spark_pi.sh

6. <http://localhost:8080/> 에서 실행한 작업의 상태 확인.

7. 아래와 같은 명령어를 통해 예시 spark 작업 수행.

        spark$ . local/scripts/spark_example.sh

8. 아래와 같은 명령어를 통해 spark 작업으로 생성된 파일 확인.

        spark$ cat local/csv/part*.csv

9. Ctrl+D로 master-node 컨테이너에서 빠져나와 아래 명령어 통해 spark 클러스터 종료.

        user$ docker-compose down
