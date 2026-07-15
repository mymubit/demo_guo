#!/bin/sh
set -eu

PROJECT_NAME="scriptforge-integration"

cleanup() {
  docker compose -p "$PROJECT_NAME" -f docker-compose.test.yml down -v --remove-orphans
}
trap cleanup EXIT INT TERM

docker compose -p "$PROJECT_NAME" -f docker-compose.test.yml up \
  --build \
  --abort-on-container-exit \
  --exit-code-from integration-test
