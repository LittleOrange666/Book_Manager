#!/bin/bash
if [ -z $1 ]; then
  echo "version is required for the release build"
  echo "Usage: $0 <version>"
else
  echo "Building version $1"
  docker build . -t littleorange666/book_manager:$1 | exit 1
  echo "Pushing version $1"
  docker push littleorange666/book_manager:$1
fi