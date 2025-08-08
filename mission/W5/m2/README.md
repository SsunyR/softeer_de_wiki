# W4M2 실행

## Files

- 디렉토리 구조

        .
        ├── docker-compose.yaml
        ├── Dockerfile
        ├── README.md
        ├── data/
        │   ├── csv/
        │   ├── parquet/
        │   ├── 2024_weather/
        │   │   ├── 01.csv
        │   │   ├── 02.csv
        │   │   ├── 07.csv
        │   │   └── 08.csv
        │   ├── (fhv_tripdata_2024_1278/)
        │   │   ├── (fhvhv_tripdata_2024-01.parquet)
        │   │   ├── (fhvhv_tripdata_2024-02.parquet)
        │   │   ├── (fhvhv_tripdata_2024-03.parquet)
        │   │   └── (fhvhv_tripdata_2024-04.parquet)
        │   └── scripts/
        │       ├── analyze_NYC_TLC.py
        │       ├── make_csv.py
        │       ├── run_pipiline.sh
        │       └── visualize_distance_analysis.py
        ├── conf/
        │   └── spark-defaults.conf
        ├── logs/
        │   ├── master/
        │   ├── worker1/
        │   └── worker2/
        ├── distance_analysis.png
        ├── location_analysis.png
        ├── metrics.png
        ├── peak_hours.png
        ├── weather_analysis.png
        └── report.md

- NYC TLC Trip Record from <https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page>
  - High Volume FHV Trips Data 2024 JAN, FEB, JUL, AUG
- NY weather data from <https://www.ncdc.noaa.gov/cdo-web/datasets/GHCND/stations/GHCND:USW00094728/detail>

- run_pipeline.sh 의 실행 순서.

        analyze_NYC_TLC.py (spark-submit)
                |
        make_csv.py (python3)
                |
        visualize_distance_analysis.py (python3)

## Step-By-Step Execution

1. 아래 명령어를 통해 Spark standalone cluster를 실행.

        user$ docker-compose up --build -d

2. 아래 명령어를 통해 모든 컨테이너가 실행 중인지 확인.

        user$ spark$ docker ps

3. 아래 명령어를 통해 spark-master 컨테이너에 연결.

        user$ docker exec -it spark-master bash

4. <http://localhost:8080/> 에서 Spark 클러스터의 상태를 Web UI로 확인.

5. 아래와 같은 명령어를 통해 pi 계산 spark 작업 수행.

        spark$ . local/scripts/run_pipeline.sh

6. <http://localhost:8080/> 에서 실행한 작업의 상태 확인.

7. report.md를 통해 시각화 정보 확인 가능.

8. Ctrl+D로 master-node 컨테이너에서 빠져나와 아래 명령어 통해 spark 클러스터 종료.

        user$ docker-compose down
