#!/bin/bash
TEMP=`tempfile`
if [ ! -x modules ]; then
    echo "Must run from /knowledge directory"
    exit -1
fi

find modules/openstreetmap/mod_tile64/default/{0,1,2,3,4,5,6,7,8} >>$TEMP
find modules/gutenberg >>$TEMP
find modules/wikipedia-zim/wikipedia_gn_all_01_2013.zim >>$TEMP
find "modules/khanacademy/webm/Art History/01 Introduction to Art History - 02 Media"* >>$TEMP
find "modules/khanacademy/h264/Art History/01 Introduction to Art History - 02 Media"* >>$TEMP
find modules/wikipedia-kiwix/library.xml >>$TEMP
find modules/wikipedia-kiwix/index/wikipedia_gn_all_01_2013/ >>$TEMP
find modules/INFO.json modules/*/INFO.json >>$TEMP

# Moby Dick
find modules/gutenberg-mirror/data/2/7/0/2701 >>$TEMP
find modules/gutenberg-htmlz/01/pg2701.htmlz >>$TEMP
find modules/gutenberg-epub/01/pg2701.epub >>$TEMP

# Alice in Wonderland Illustrated
find modules/gutenberg-htmlz-images/33/pg19033.htmlz >>$TEMP
find modules/gutenberg-epub-images/33/pg19033.epub >>$TEMP

# Wikipedia title search index
find modules/wikipedia-index >>$TEMP
find modules/wikipedia-index.titles_only/wikipedia_gn_all_01_2013 >>$TEMP

# Map city name search
find modules/geonames_index >>$TEMP

# Bash software
find modules/ubuntu/12.04/mirror/archive.ubuntu.com/ubuntu/pool/main/b/bash >>$TEMP

if [ -x sampler/knowledge ]; then
    echo "Deleting existing sampler/knowledge directory..."
    rm -rf sampler/knowledge
fi
mkdir -p sampler/knowledge

echo "Copying files to sampler/..."
tar cBf - -T $TEMP |(cd sampler/knowledge; tar xBf -)

grep -e '<library' -e '<?xml' -e wikipedia_gn_all_01_2013 -e '</library>' modules/wikipedia-kiwix/library.xml >sampler/knowledge/modules/wikipedia-kiwix/library.xml

NAME=IIAB_QuickStart_Sampler_`date +%Y%m%d`.tgz
echo "Creating tarball $NAME..."
tar czf "$NAME" -C sampler knowledge
echo "Complete"
