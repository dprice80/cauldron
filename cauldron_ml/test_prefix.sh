#!/bin/bash
set -e

# Check if PROJECT_NAME is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <project_name> <root_path>"
  exit 1
fi

if [ -z "$2" ]; then
  echo "Usage: $0 <project_name> <root_path>"
  exit 1
fi

DOCKER_REPO=europe-west2-docker.pkg.dev/msm-groupdata-sharedresources/data-science-ml-pipelines
PROJECT_NAME=$1
PREFIX=prefix
IMAGE_NAME="${DOCKER_REPO}/${PROJECT_NAME}_component"
VERSION_TAG=tagtest

rm ~/.caulprofile
echo "docker-repo: $DOCKER_REPO" >> ~/.caulprofile && \
echo "user-prefix: $PREFIX" >> ~/.caulprofile && \
echo "production-project-name: msmg-datascience-prod" >> ~/.caulprofile && \
echo "production-project-numeric-id: '612279675388'" >> ~/.caulprofile && \
echo "sandbox-project-name: msmg-datascience-explore" >> ~/.caulprofile && \
echo "sandbox-project-numeric-id: '243205181736'" >> ~/.caulprofile

if [ -d $2/pipelines/$1 ]; then
    rm -rfv $2/pipelines/$1
fi 

caul create --name=$1

# Define a function to delete images
delete_images() {
    local IMAGE_NAME=$1
    local PREFIX=$2
    local VERSION_TAG=$3

    if docker rmi -f "${IMAGE_NAME}:${PREFIX}_${VERSION_TAG}" 2>/dev/null; then
        echo "[TEST] Latest image ${IMAGE_NAME}:${PREFIX}_${VERSION_TAG} was deleted."
    else
        echo "[TEST] Latest image ${IMAGE_NAME}:${PREFIX}_${VERSION_TAG} does not exist or could not be deleted."
    fi
}

caul activate $PROJECT_NAME --version-tag=$VERSION_TAG
caul build --base --no-push

# Check if the latest image exists
if docker images | grep -q "${IMAGE_NAME}[[:space:]]*${PREFIX}_base"; then
    echo "[TEST] Base image ${IMAGE_NAME}:${PREFIX}_base exists."
else
    echo "[TEST] Base image ${IMAGE_NAME}:${PREFIX}_base does not exist."
    exit 1
fi

caul build --no-push

# Check if the latest image exists
if docker images | grep -q "${IMAGE_NAME}[[:space:]]*${PREFIX}_${VERSION_TAG}"; then
    echo "[TEST] Latest image ${IMAGE_NAME}:${PREFIX}_${VERSION_TAG} exists."
else
    echo "[TEST] Latest image ${IMAGE_NAME}:${PREFIX}_${VERSION_TAG} does not exist."
    exit 1
fi

# Create a container from the image
container_id=$(docker run -d "${IMAGE_NAME}:${PREFIX}_${VERSION_TAG}" tail -f /dev/null) 

# Allow the container to start
sleep 10

# Check if the container was created successfully
if [ -z "$container_id" ]; then
    echo "[TEST] Failed to create the container."
    exit 1
fi

# Check if the container is running
if ! docker ps | grep -q "${container_id:0:12}"; then
    echo "[TEST] Container $container_id is not running."
    docker rm "$container_id"
    exit 1
fi

echo "Container $container_id is running."

# Test python version
python_version_installed=$(docker exec "${container_id}" python -V 2>&1)
export $(docker exec "${container_id}" echo $(grep -v '^#' pipelines/${PROJECT_NAME}/build/ci_workflow.env | xargs) 2>&1)
if [ "$python_version_installed" = "Python ${PYENV_VERSION}" ]; then
    echo "[TEST] Python version is ${PYENV_VERSION}."
else
    echo "[TEST] Python version is not ${PYENV_VERSION}. Found: $python_version_installed"
    docker rm "${container_id}"
    exit 1
fi

caul_installed_location=$(docker exec "${container_id}" which caul 2>&1)
if [ -z "$caul_installed_location" ]; then
    echo "[TEST] caul not found in image"
    docker rm "${container_id}"
    exit 1
fi

# Read the contents of load_data.yaml inside the container
if docker cp "${container_id}:/usr/local/src/kfp/components/load_data.yaml" /tmp/load_data.yaml; then
    echo "[TEST] Successfully copied load_data.yaml from the container."

    # Check if the specific line exists in the file
    if grep -q "${IMAGE_NAME}:${PREFIX}_${VERSION_TAG}" /tmp/load_data.yaml; then
        echo "[TEST] The specific line exists in /tmp/load_data.yaml."
    else
        echo "[TEST] The specific line does not exist in /tmp/load_data.yaml."
        exit 1
    fi

    # Clean up the copied file
    rm /tmp/load_data.yaml
else
    echo "[TEST] Failed to copy load_data.yaml from the container."
    exit 1
fi

caul deploy --images base
caul deploy --images pipeline
caul deploy --images "base, pipeline"
caul build-deploy

# Clean up the container
docker rm -f "${container_id}"
delete_images "$IMAGE_NAME" "$PREFIX" "base"
delete_images "$IMAGE_NAME" "$PREFIX" "$VERSION_TAG"

echo "[TEST] ALL PREFIX TESTS PASSED"

caul run