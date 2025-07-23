## W3M1 실행
1. 디렉토리 구조
    ```
    .
    ├── docker-compose.yaml
    ├── README.md
    └── config/
        ├── core-site.xml
        ├── hdfs-site.xml
        └── mapred-site.xml
    ```

2. 아래 명령어를 통해 Hadoop single-node cluster를 실행.

        $ docker-compose up -d

3. 아래 명령어를 통해 namenode와 datanode 두 컨테이너가 실행 중인지 확인.

        $ docker ps

4. 아래 명령어를 통해 namenode 컨테이너에 연결.

        $ docker exec -it namenode bash

5. http://localhost:9870 에서 하둡 클러스터의 상태를 Web UI로 확인.

6. 아래와 같은 명령어를 통해 하둡 명령어의 동작 확인.

        # hdfs dfs -mkdir temp
        
        # hdfs dfs -ls /

7. 아래 명령어를 통해 로컬 데이터를 하둡 클러스터에 업로드.

        # hdfs dfs -put local_data/test.txt /temp

8. 아래 명령어를 통해 하둡 클러스터의 데이터 다운로드.

        # hdfs dfs -get /temp/test.txt .

9. Ctrl+D로 namenode 컨테이너에서 빠져나와 아래 명령어 통해 하둡 클러스터 종료 및 볼륨 정보 지우기.

        $ docker-compose down -v