## W3M2b 실행

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
            ├── yarn-site.xml
            └── backup
                ├── core-site.backup.xml
                ├── hdfs-site.backup.xml
                ├── mapred-site.backup.xml
                └── yarn-site.backup.xml
    ```

2. 아래 명령어를 통해 Hadoop multi-node cluster를 실행.

        $ docker-compose up --build -d

3. 아래 명령어를 통해 모든 컨테이너가 실행 중인지 확인.

        $ docker ps

4. 아래 명령어를 통해 namenode 컨테이너에 연결.

        $ docker exec -it namenode bash

5. http://localhost:9870/ 에서 하둡 클러스터의 상태를 Web UI로 확인.

6. 아래와 같은 명령어를 통해 하둡 명령어의 동작 확인.

        # hdfs dfs -mkdir /test
        
        # hdfs dfs -ls /

7. 아래와 같은 명령어를 통해 configuration 변경 스크립트 실행.

        # python3 local_data/modification.py

8. 아래와 같은 명령어를 통해 verification 스크립트 실행.

        # python3 local_data/verification.py

9. Ctrl+D로 namenode 컨테이너에서 빠져나와 아래 명령어 통해 하둡 클러스터 종료 및 볼륨 정보 지우기.

        $ docker-compose down -v