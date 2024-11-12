# needs a default to get rid of warning
ARG PROJECT_NAME=default
ARG USER_PREFIX=prod

FROM europe-west2-docker.pkg.dev/msm-groupdata-sharedresources/data-science-ml-pipelines/${PROJECT_NAME}_component:${USER_PREFIX}_base

SHELL ["/bin/bash", "-c"]

WORKDIR /usr/local/src/kfp/components

# Need to rerun the ARG command due to a quirk of docker that clears the ARGs after the FROM command
ARG PROJECT_NAME
ARG IMAGE_TAG
ARG USER_PREFIX

ENV PROJECT_NAME_ENV=$PROJECT_NAME
ENV IMAGE_TAG_ENV=$IMAGE_TAG
ENV USER_PREFIX_ENV=$USER_PREFIX
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

COPY pipelines/${PROJECT_NAME} pipelines/${PROJECT_NAME}

RUN echo "docker-repo: europe-west2-docker.pkg.dev/msm-groupdata-sharedresources/data-science-ml-pipelines" >> ~/.caulprofile && \
    echo "user-prefix: ${USER_PREFIX_ENV}" >> ~/.caulprofile && \
    echo "production-project-name: msmg-datascience-prod" >> ~/.caulprofile && \
    echo "production-project-numeric-id: '612279675388'" >> ~/.caulprofile && \
    echo "sandbox-project-name: msmg-datascience-explore" >> ~/.caulprofile && \
    echo "sandbox-project-numeric-id: '243205181736'" >> ~/.caulprofile

RUN set -e && \
    caul activate ${PROJECT_NAME_ENV} --version-tag=${IMAGE_TAG_ENV} && \
    caul build --no-use-docker && \
    cp -r vdist/* .

# In case you need to debug use 
# docker run -it europe-west2-docker.pkg.dev/msm-groupdata-sharedresources/data-science-ml-pipelines/<project_name>_component:latest bash
