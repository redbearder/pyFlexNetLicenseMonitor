FROM centos:7

RUN yum install -y epel-release \
    redhat-lsb.i686\
    && yum clean all

RUN yum install -y \
    cargo \
    freetype-devel \
    gcc \
    ghostscript \
    lcms2-devel \
    libffi-devel \
    libjpeg-devel \
    libraqm-devel \
    libtiff-devel \
    libwebp-devel \
    make \
    openjpeg2-devel \
    openssl-devel \
    sqlite-devel \
    sudo \
    tcl-devel \
    tk-devel \
    tkinter \
    wget \
    which \
    xorg-x11-server-Xvfb \
    zlib-devel \
    && yum clean all

RUN wget https://www.python.org/ftp/python/3.9.16/Python-3.9.16.tgz \
    && tar xzf Python-3.9.16.tgz \
    && cd Python-3.9.16 \
    && ./configure \
    && make altinstall \
    && cd .. \
    && rm -r Python-3.9.16 Python-3.9.16.tgz


WORKDIR /opt/monitor
COPY . /opt/monitor/

RUN python3.9 -m venv venv
RUN venv/bin/pip install -r requirements.txt

EXPOSE 27777

#CMD venv/bin/gunicorn -b :27777 main:app -k uvicorn.workers.UvicornWorker
CMD venv/bin/python3.9 main.py
