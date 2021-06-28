#!/usr/bin/env bash

set -x -e

git checkout deploy

# Generate document root
mkdir -p www

git cat-file blob master:entry.html >www/entry-test.html
cp -r css js www

git add www
git add www/entry-test.html

# Generate WSGI directory
mkdir -p wsgi-scripts
git cat-file blob master:server/store_data.py >wsgi-scripts/store_data.wsgi
git add wsgi-scripts
git add wsgi-scripts/store_data.wsgi

git commit -m "pre-deploy-test commit"

git push

git checkout master
