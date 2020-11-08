FROM centos:7
MAINTAINER Matthew Horwood <matt@horwood.biz>

RUN yum -y update; \
    yum -y install git vim; \
    mkdir git && cd git; \
    git clone https://github.com/NagiosEnterprises/ncpa.git;
    cd build; \
    pip install -r resources/require.txt; \
    yes | ./build.sh;
    
