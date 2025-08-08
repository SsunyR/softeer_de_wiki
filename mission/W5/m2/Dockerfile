# 
FROM spark

USER root

RUN apt-get update && apt-get install -y sudo wget && \
    apt-get clean

RUN usermod -aG sudo spark && \
    echo "spark ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# jupyter를 설치 목록에 추가합니다.
RUN pip install pyspark pandas pyarrow matplotlib seaborn

WORKDIR /opt/spark

ENV PATH="/opt/spark/bin:$PATH"

USER spark