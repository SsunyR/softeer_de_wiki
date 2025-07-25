## W3M2 실행

1. 디렉토리 구조
    ```
        .
        ├── docker-compose.yaml
        ├── README.md
        ├── data
        │   └── test.txt
        └── config
            ├── log4j.properties
            ├── capacity-scheduler.xml
            ├── core-site.xml
            ├── hdfs-site.xml
            ├── mapred-site.xml
            └── yarn-site.xml
    ```

2. 아래 명령어를 통해 Hadoop multi-node cluster를 실행.

        $ docker-compose up --build -d

3. 아래 명령어를 통해 모든 컨테이너가 실행 중인지 확인.

        $ docker ps

4. 아래 명령어를 통해 namenode 컨테이너에 연결.

        $ docker exec -it namenode bash

5. http://localhost:9870/ 에서 하둡 클러스터의 상태를 Web UI로 확인.

6. 아래와 같은 명령어를 통해 하둡 명령어의 동작 확인.

        # hdfs dfs -mkdir temp
        
        # hdfs dfs -ls /

7. 아래 명령어를 통해 로컬 데이터를 하둡 클러스터에 업로드.

        # hdfs dfs -put local_data/test.txt /temp

8. 아래 명령어를 통해 클러스터에 업로드한 파일의 복제 상태를 확인.

        # hdfs fsck /temp/test.txt -files -blocks -locations

9. 아래 명령어를 통해 업로드한 파일의 mapreduce 작업 수행.

        # hadoop jar /opt/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-3.4.1.jar wordcount \
        /temp/test.txt /output

10. http://localhost:8088/ 에서 실행한 작업의 정보 확인.

11. 아래 명령어를 통해 작업을 통해 생성된 결과 파일 확인.

        # hsfs dfs -ls /output

12. 아래 명령어를 통해 실행한 mapreduce 결과 확인.

        # hdfs dfs -cat /output/part-r-00000

13. Ctrl+D로 namenode 컨테이너에서 빠져나와 아래 명령어 통해 하둡 클러스터 종료 및 볼륨 정보 지우기.

        $ docker-compose down -v
