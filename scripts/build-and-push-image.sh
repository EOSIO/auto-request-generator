set -e

IMAGE_NAME=$1
SOURCE_PATH=$2
BRANCH=$3

echo "building $IMAGE_NAME from SOURCE_PATH $SOURCE_PATH.  branch: $BRANCH"
docker --version
docker build --rm -t "$IMAGE_NAME:latest" $SOURCE_PATH

docker tag "$IMAGE_NAME:latest" "registry.devel.b1ops.net/automation-tools/$IMAGE_NAME:latest"

if [ "$BRANCH" == "master" ] ; then
  echo "pushing $IMAGE_NAME image"
  docker push "registry.devel.b1ops.net/automation-tools/$IMAGE_NAME:latest"
else
  echo "branch $BRANCH specified.  skipping push"
fi

docker rmi "$IMAGE_NAME:latest" --force
docker rmi "registry.devel.b1ops.net/automation-tools/$IMAGE_NAME:latest" --force
