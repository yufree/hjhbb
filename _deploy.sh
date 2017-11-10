#!/bin/sh

set -e

[ -z "${GITHUB_PAT}" ] && exit 0
[ "${TRAVIS_BRANCH}" != "master" ] && exit 0

git config --global user.email "yufree@live.cn"
git config --global user.name "yufree"

# clone the repository to the book-output directory
cd docs
git rm -rf *
cp -r ../_book/* ./
git add --all *
git commit -m "Update the book"
git push -q origin gh-pages