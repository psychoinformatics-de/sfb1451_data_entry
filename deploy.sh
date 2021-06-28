#!/usr/bin/env bash

set -x -e

suffix=""
if [ "$#" -gt "0" ]; then
  if [ "$1" == "test" ]; then
    suffix="-test"
  fi
fi


git checkout deploy

master-version-file=master-version${suffix}
touch master-version-file
new_master=$(git rev-parse master)
current_master=$(cat master-version-file)


if [ "${new_master}" == "${current_master}" ]; then
  echo "latest master version already deployed"
  exit 0
fi

echo "${new_master}" > master-version-file
git add master-version-file


# Generate document root
html-file=entry${suffix}.html

mkdir -p www

git cat-file blob master:entry.html >"www/${html-file}"
cp -r css js www

git add www
git add "www/${html-file}"


# Generate WSGI directory
mkdir -p wsgi-scripts
git cat-file blob master:server/store_data.py >wsgi-scripts/store_data.wsgi
git add wsgi-scripts
git add wsgi-scripts/store_data.wsgi

git commit -m "pre-deploy${suffix} commit "

git push

git checkout master
