current_branch=$(git rev-parse --abbrev-ref HEAD)

make html

rm -rf /tmp/ncpa-doc-building
mkdir /tmp/ncpa-doc-building

cp _build/html/* /tmp/ncpa-doc-building/ -r

cd ..
git checkout gh-pages
/bin/cp -rf /tmp/ncpa-doc-building/* .
git commit -am "Adding newer docs to gh-pages -Nick's Servbot"
git push

git checkout "$current_branch"
