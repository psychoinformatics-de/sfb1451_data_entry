#!/usr/bin/env bash

set -x -e


local_part=z03
local_part=""


if [ "X${local_part}" != "X"]; then
  destination_dir="www/${local_part}"
else
  destination_dir="www"
fi


suffix=""
if [ "$#" -gt "0" ]; then
  if [ "$1" == "test" ]; then
    suffix="-test"
  fi
fi


git checkout deploy

master_version_file=master-version${suffix}
touch ${master_version_file}
new_master=$(git rev-parse master)
current_master=$(cat ${master_version_file})


if [ "${new_master}" == "${current_master}" ]; then
  echo "latest master version already deployed"
  git checkout master
  exit 0
fi

echo "${new_master}" > ${master_version_file}
git add ${master_version_file}


# Generate document root
html_file=index${suffix}.html

mkdir -p "${destination_dir}"

git cat-file blob master:entry.html >"${destination_dir}/${html_file}"


git add "${destination_dir}"
git add "${destination_dir}/${html_file}"


# Generate WSGI directory
mkdir -p wsgi-scripts
git cat-file blob master:server/store_data.py >wsgi-scripts/store_data.wsgi
git add wsgi-scripts
git add wsgi-scripts/store_data.wsgi

mkdir -p templates
git cat-file blob master:templates/success.html.jinja2 >templates/success.html.jinja2
git add templates
git add templates/success.html.jinja2


git commit -m "pre-deploy${suffix} commit "

git push

git checkout master
