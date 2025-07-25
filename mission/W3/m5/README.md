## W3M5 실행

- 디렉토리 구조
    ```
        .
        ├── docker-compose.yaml
        ├── Dockerfile
        ├── README.md
        ├── mapred.txt          # Command for Mapreduce job
        ├── data
        │   ├── tweet.csv
        │   ├── reducer.py
        │   └── mapper.py
        └── config
            ├── log4j.properties
            ├── capacity-scheduler.xml
            ├── core-site.xml
            ├── hdfs-site.xml
            ├── mapred-site.xml
            ├── yarn-site.xml
            └── workers
    ```
    
- mapper.py

        ```
        #!/usr/bin/env python3

        import sys

        for line in sys.stdin:
        line = line.strip()
        if line.startswith('userId'):
                continue

        fields = line.split(sep=',')
        movie_id = fields[1].strip().zfill(6)
        rating = fields[2].strip()

        print('{}\t{}'.format(movie_id, rating))
        ```
- reducer.py
        ```
        #!/usr/bin/env python3

        import sys

        current_movie = None
        current_count = 0
        current_rating = 0
        movie_id = None
        rating = None

        for line in sys.stdin:
        line = line.strip()
        movie_id, rating = line.split('\t',1)

        try:
                rating = float(rating)
        except ValueError:
                continue

        if current_movie == movie_id:
                current_count += 1
                current_rating += rating
        else:
                if current_movie:
                        print('{}\t{}'.format(current_movie.lstrip('0'),round(current_rating/current_count, 1)))
                current_movie = movie_id
                current_count = 1
                current_rating = rating


        if current_movie == movie_id:
                print('{}\t{}'.format(current_movie,current_rating))
        ```

1. 아래 명령어를 통해 Hadoop cluster를 실행.

        $ docker-compose up --build -d

2. 아래 명령어를 통해 모든 컨테이너가 실행 중인지 확인.

        $ docker ps

3. 아래 명령어를 통해 namenode 컨테이너에 연결.

        $ docker exec -it namenode bash

4. http://localhost:9870/ 에서 하둡 클러스터의 상태를 Web UI로 확인.

5. 아래와 같은 명령어를 통해 hdfs에 ml 디렉토리를 만들고 확인.

        # hdfs dfs -mkdir /ml
        
        # hdfs dfs -ls /

6. 아래 명령어를 통해 로컬 데이터를 하둡 클러스터에 업로드.

        # docker cp /my/movielens/data/path namenode:/opt/hadoop/

        # hdfs dfs -put /opt/hadoop/ratings.csv /ml

7. 아래 명령어를 통해 클러스터에 업로드한 파일의 상태를 확인.

        # hdfs dfs -ls /ml

8. 아래 명령어를 통해 업로드한 파일의 mapreduce 작업 수행.

        # mapred streaming -files /opt/hadoop/local_data/mapper.py,/opt/hadoop/local_data/reducer.py -input /ml/ratings.csv -output /output -mapper mapper.py -reducer reducer.py

9. http://localhost:8088/ 에서 실행한 작업의 정보 확인.

10. 아래 명령어를 통해 mapreduce를 통해 생성된 결과 파일 확인.

        # hsfs dfs -ls /output

11. 아래 명령어를 통해 실행한 mapreduce 결과 확인. (space bar로 넘기며 확인, q를 통해 종료)

        # hdfs dfs -cat /output/part-00000 | more

12. Ctrl+D로 namenode 컨테이너에서 빠져나와 아래 명령어 통해 하둡 클러스터 종료 및 볼륨 정보 지우기.

        $ docker-compose down -v