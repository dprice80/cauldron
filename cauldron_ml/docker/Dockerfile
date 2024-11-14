# Needs a default to get rid of warning
ARG DOCKER_REPO=None
ARG PROJECT_NAME=None
ARG USER_PREFIX=None

FROM ${DOCKER_REPO}/${PROJECT_NAME}_component:${USER_PREFIX}_base

SHELL ["/bin/bash", "-c"]

WORKDIR /usr/local/src/kfp/components

# Need to rerun the ARG command due to a quirk of docker that clears the ARGs after the FROM command
ARG PROJECT_NAME
ARG IMAGE_TAG
ARG USER_PREFIX
ARG DOCKER_REPO
ARG PRODUCTION_SERVICE_ACCOUNT
ARG SANDBOX_SERVICE_ACCOUNT

# For protobuf
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

COPY pipelines/${PROJECT_NAME} pipelines/${PROJECT_NAME}

RUN echo "docker-repo: ${DOCKER_REPO}" >> ~/.caulprofile && \
    echo "user-prefix: ${USER_PREFIX}" >> ~/.caulprofile && \
    echo "production-project-name: msmg-datascience-prod" >> ~/.caulprofile && \
    echo "sandbox-project-name: msmg-datascience-explore" >> ~/.caulprofile && \
    echo "production-service-account: ${PRODUCTION_SERVICE_ACCOUNT}" >> ~/.caulprofile && \
    echo "sandbox-service-account: ${SANDBOX_SERVICE_ACCOUNT}" >> ~/.caulprofile

RUN set -e && \
    caul activate ${PROJECT_NAME_ENV} --version-tag=${IMAGE_TAG} && \
    caul build --no-use-docker && \
    cp -r vdist/* .
