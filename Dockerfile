FROM centos:7
MAINTAINER Matthew Horwood <matt@horwood.biz>

RUN yum install epel-release -y; \
    yum -y update; \
    yum -y install git vim; \
    mkdir git && cd git; \
    git clone https://github.com/NagiosEnterprises/ncpa.git; \
    cd ncpa && git checkout v2.2.2;
