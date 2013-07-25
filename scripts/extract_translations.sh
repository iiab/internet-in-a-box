#!/bin/bash

base_dir=$(dirname $0)/../iiab
po_dir=$(dirname $0)/../po

version=$(cat $base_dir/__init__.py | cut -d '=' -f 2 | sed "s/[ ']//g")

pybabel extract -F ${base_dir}/babel.cfg \
    --project="Internet in a Box" \
    --version=${version} \
    --msgid-bugs-address="internet-in-a-box@noreply.github.com" \
    --copyright-holder="Humane Informatics, LLC." \
    -o ${po_dir}/iiab.pot ${base_dir} 
