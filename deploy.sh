#!/usr/bin/env bash

git checkout master

mkdir -p www

cp entry.html www
cp -r css js www

git add www
git commit -m "pre-deploy commitment"

git checkout deploy
git merge master -m "deploy merge"
git push

git checkout master
