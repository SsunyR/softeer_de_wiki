FROM apache/hadoop:3.4.1

RUN sudo sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*
RUN sudo sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*

RUN sudo yum update -y
RUN sudo yum install -y centos-release-scl
RUN sudo sed -i 's|# baseurl=http://mirror.centos.org/centos/7/sclo/$basearch/sclo/|baseurl=http://vault.centos.org/centos/7/sclo/$basearch/sclo/|g' /etc/yum.repos.d/CentOS-SCLo-scl.repo
RUN sudo sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*
RUN sudo sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*

RUN sudo yum install -y rh-python38
RUN sudo yum install -y openssh-server openssh-clients
RUN sudo yum install -y java-1.8.0-openjdk-devel
RUN sudo yum clean all

USER root

RUN ln -s /opt/rh/rh-python38/root/usr/bin/python /usr/bin/python3 && \
    ln -s /opt/rh/rh-python38/root/usr/bin/pip /usr/bin/pip3

ENV PATH=$PATH:/opt/hadoop/sbin
ENV JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk
RUN echo "export JAVA_HOME=${JAVA_HOME}" >> /opt/hadoop/etc/hadoop/hadoop-env.sh


RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -N '' && \
    ssh-keygen -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -N '' && \
    ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N '' && \
    ssh-keygen -t rsa -P '' -f /root/.ssh/id_rsa && \
    cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys && \
    chmod 0600 /root/.ssh/authorized_keys

RUN systemctl enable sshd

EXPOSE 22 9870 9864 8088 8042