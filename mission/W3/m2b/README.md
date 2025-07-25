## W3M2 실행

1. 디렉토리 구조
    ```
        .
        ├── docker-compose.yaml
        ├── README.md
        ├── data
        │   ├── modification.py
        │   └── verification.py
        └── config
            ├── log4j.properties
            ├── capacity-scheduler.xml
            ├── core-site.xml
            ├── hdfs-site.xml
            ├── mapred-site.xml
            └── yarn-site.xml
    ```

2. 아래 명령어를 통해 Hadoop multi-node cluster를 실행.

        $ docker-compose up -d

3. 아래 명령어를 통해 모든 컨테이너가 실행 중인지 확인.

        $ docker ps

4. 아래 명령어를 통해 namenode 컨테이너에 연결.

        $ docker exec -it namenode bash

5. http://localhost:9870/ 에서 하둡 클러스터의 상태를 Web UI로 확인.

6. 아래와 같은 명령어를 통해 하둡 명령어의 동작 확인.

        # hdfs dfs -mkdir temp
        
        # hdfs dfs -ls /
