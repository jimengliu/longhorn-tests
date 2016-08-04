FROM ubuntu:16.04

ADD *.py ./
RUN apt-get update
RUN apt-get install -y openssh-client
RUN apt-get install -y python
RUN apt-get install -y curl
RUN apt-get install -y python-pip
RUN pip install --upgrade pip

RUN pip install --upgrade google-api-python-client
RUN pip install --upgrade packet-python

RUN curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-119.0.0-linux-x86_64.tar.gz
RUN tar zxvf google-cloud-sdk-119.0.0-linux-x86_64.tar.gz
ENV CLOUDSDK_CORE_DISABLE_PROMPTS="1"
RUN ./google-cloud-sdk/install.sh
RUN ./google-cloud-sdk/bin/gcloud components update

ENTRYPOINT ["python"]

