#!/bin/bash

trans_dir=$(dirname $0)/../iiab/translations
po_dir=$(dirname $0)/../po

for po_file in $(ls $po_dir/*.po); do
    locale_name=$(echo $(basename $po_file) | sed 's/\.po$//')
    dest_fn=$trans_dir/$locale_name/LC_MESSAGES/messages.mo
    mkdir -p $(dirname $dest_fn)
    pybabel compile -i $po_file -o $dest_fn
done
