FROM eclipse-temurin:8-jdk-focal

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        sudo \
        curl \
        ssh \
    && apt-get clean

RUN useradd -m hduser && echo "hduser:supergroup" | chpasswd && adduser hduser sudo && echo "hduser     ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && cd /usr/bin/ && sudo ln -s python3 python
COPY ssh_config /etc/ssh/ssh_config

WORKDIR /home/hduser
USER hduser

RUN ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa && cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys && chmod 0600 ~/.ssh/authorized_keys
ENV HADOOP_HOME=/home/hduser/hadoop
ENV PATH=$PATH:${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin

RUN curl -O https://dlcdn.apache.org/hadoop/common/hadoop-3.4.1/hadoop-3.4.1.tar.gz
RUN tar -xzf hadoop-3.4.1.tar.gz \
    && mv hadoop-3.4.1  /home/hduser/hadoop \
    && rm hadoop-3.4.1.tar.gz \
    && rm -rf ${HADOOP_HOME}/share/doc

ENV HDFS_NAMENODE_USER=hduser
ENV HDFS_DATANODE_USER=hduser
ENV HDFS_SECONDARYNAMENODE_USER=hduser

RUN echo "export JAVA_HOME=/opt/java/openjdk/" >> $HADOOP_HOME/etc/hadoop/hadoop-env.sh

COPY core-site.xml ${HADOOP_HOME}/etc/hadoop/
COPY hdfs-site.xml ${HADOOP_HOME}/etc/hadoop/

COPY docker-entrypoint.sh ${HADOOP_HOME}/etc/hadoop/
RUN sudo chmod +x ${HADOOP_HOME}/etc/hadoop/docker-entrypoint.sh

EXPOSE 9000 9864 9870 8088

WORKDIR /usr/local/bin
RUN sudo ln -s ${HADOOP_HOME}/etc/hadoop/docker-entrypoint.sh .
WORKDIR /home/hduser

VOLUME [ "/tmp/hadoop-hduser/dfs/data" ]

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]