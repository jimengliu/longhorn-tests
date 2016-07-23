#!/usr/bin/env python

import os
import logging
import tarfile
import urllib
import subprocess
import time
import getpass


logging.basicConfig(level=logging.INFO)
log = logging.getLogger("common")

packet_rancher_auth_token = os.environ["PACKET_RANCHER_AUTH_TOKEN"]
packet_rancher_project_id = os.environ["PACKET_RANCHER_PROJECT_ID"]

gce_key_file_content = os.environ["GCE_SERVICE_KEY_JSON"]
gce_key_file = "servicekey.json"
gce_rancher_project_name = os.environ["GCE_RANCHER_PROJECT_NAME"]
gce_rancher_project_zone = os.environ["GCE_RANCHER_PROJECT_ZONE"]

gce_nfs_server_name = os.environ["GCE_NFS_SERVER_NAME"]
gce_rancher_server_name = os.environ["GCE_RANCHER_SERVER_NAME"]
packet_host_names = os.environ["PACKET_HOST_NAMES"].split(",")


def untar(fname):
    tar = tarfile.open(fname)
    tar.extractall()
    tar.close()
    log.info("Extracted to Current Directory")


def install_gcloud(gcloud_sdk_url, gcloud_sdk_file_name):
    urllib.urlretrieve(gcloud_sdk_url, gcloud_sdk_file_name)

    # unzip it
    untar(gcloud_sdk_file_name)

    # set env to disable the prompt and run installation script
    os.environ["CLOUDSDK_CORE_DISABLE_PROMPTS"] = "1"
    retCode = subprocess.call("./google-cloud-sdk/install.sh", shell=True)
    if retCode != 0:
        raise Exception("failed to google-cloud-sdk/install.sh")
    retCode = subprocess.call(
        "./google-cloud-sdk/bin/gcloud auth activate-service-account \
        --key-file " + gce_key_file,
        shell=True)
    if retCode != 0:
        raise Exception("failed to gcloud auth activate-service-account")
    retCode = subprocess.call(
        "./google-cloud-sdk/bin/gcloud config set project " +
        gce_rancher_project_name,
        shell=True)
    if retCode != 0:
        raise Exception("failed to gcloud config set project")
    retCode = subprocess.call(
        "./google-cloud-sdk/bin/gcloud components update",
        shell=True)
    if retCode != 0:
        raise Exception("failed to gcloud components update")


def gce_wait_for_operation(compute, operation):
    log.info('Waiting for GCE operation to finish...')
    while True:
        result = compute.zoneOperations().get(
            project=gce_rancher_project_name,
            zone=gce_rancher_project_zone,
            operation=operation).execute()

        if result['status'] == 'DONE':
            if 'error' in result:
                raise Exception(result['error'])
            return result

        time.sleep(10)


def install_python_client(python_client):
    # install pip first, must be root
    user = getpass.getuser()
    sudo = ""
    if user != "root":
        sudo = "sudo "
    retCode = subprocess.call(sudo + "apt-get update", shell=True)
    if retCode != 0:
        raise Exception("failed to apt-get update")
    retCode = subprocess.call(
        sudo +
        "apt-get install -y python-pip",
        shell=True)
    if retCode != 0:
        raise Exception("failed to apt-get install -y python-pip")
    retCode = subprocess.call(sudo + "pip install --upgrade pip", shell=True)
    if retCode != 0:
        raise Exception("failed to pip install --upgrade pip")
    retCode = subprocess.call(
        sudo +
        "pip install --upgrade " +
        python_client,
        shell=True)
    if retCode != 0:
        raise Exception("failed to pip install python client")
    time.sleep(10)


def initialize_gcloud():
    # generate a gce_key_file from environment variable text(multi-line string)
    servicekey_file = open(
        os.path.join(
            os.path.dirname(__file__),
            gce_key_file),
        'w')
    servicekey_file.write(gce_key_file_content)
    servicekey_file.close()

    # install gcloud on this machine
    gcloud_sdk_url = \
        "https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/"
    gcloud_sdk_file_name = "google-cloud-sdk-119.0.0-linux-x86_64.tar.gz"
    log.info("install gcloud ...")
    install_gcloud(gcloud_sdk_url + gcloud_sdk_file_name, gcloud_sdk_file_name)

    # install gcloud python client
    log.info("install google-api-python-client ...")
    install_python_client("google-api-python-client")

    # before making any python client lib call, enable oauth
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gce_key_file

    from oauth2client.client import GoogleCredentials
    credentials = GoogleCredentials.get_application_default()

    # initialize an instance of the Google Compute Engine service, it may
    # takes a while
    from googleapiclient import discovery
    log.info("getting gce compute service ...")
    compute = discovery.build('compute', 'v1', credentials=credentials)
    return compute
