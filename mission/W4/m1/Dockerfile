FROM spark

USER root

RUN apt-get update && apt-get install -y sudo wget && \
    apt-get clean

RUN usermod -aG sudo spark && \
    echo "spark ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

RUN pip install pyspark pandas

WORKDIR /opt/spark

USER spark