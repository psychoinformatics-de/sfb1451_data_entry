#!/usr/bin/env bash

set -x -e

git checkout deploy

mkdir -p www

git cat-file blob master:entry.html >www/entry-test.html
cp -r css js www

git cat-file blob master:entry.html >entry-test.html

git add www
git add www/entry-test.html
git add entry-test.html

git commit -m "pre-deploy-test commit"

git push

git checkout master
