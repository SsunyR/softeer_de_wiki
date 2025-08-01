FROM spark

USER root

RUN apt-get update && apt-get install -y sudo wget && \
    apt-get clean

RUN usermod -aG sudo spark && \
    echo "spark ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

RUN pip install pyspark pandas pyarrow matplotlib seaborn

WORKDIR /opt/spark

ENV PATH="/opt/spark/bin:$PATH"

USER spark