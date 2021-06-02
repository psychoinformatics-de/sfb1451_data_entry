#!/usr/bin/env bash

git checkout master

mkdir -p www

cp entry.html www
cp -r css js www

git add -r www
git commit -m "pre-deploy commitment"

git checkout deploy
git merge master -m "deploy merge"

git checkout master