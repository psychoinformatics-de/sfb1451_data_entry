#!/usr/bin/env bash

set -x -e

git checkout deploy

mkdir -p www

git cat-file blob master:entry.html >www/entry.html
cp -r css js www

git cat-file blob master:entry.html >entry.html

git add www
git add www/entry.html
git add entry.html

git commit -m "pre-deploy commit"

git push

git checkout master
