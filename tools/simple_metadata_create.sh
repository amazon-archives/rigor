#! /bin/bash

# trivial usage to create a metadata.json with no annotations and leaving files local:

#     find directoryyoucareabout -type f -name \*.jpg > files.txt
#     sh tools/simple_metadata_create < files.txt > metadata.json
#     ./runpy bin/import.py -n ~/test.db metadata.json

SOURCE=`whoami`
TFILE="/tmp/$(basename $0).$$.tmp"
echo "[" >> $TFILE
while read line
do
	echo "{"
	echo "  \"source\" : \"file://$line\","
	echo "  \"locator\" : \"file://$line\","
	echo "  \"format\" : \"image/jpeg\","
	echo "  \"properties\"  : {"
	echo "     \"source\": \"${SOURCE}\""
	echo "    },"
	width=`convert $line -format "%w" info:`
	height=`convert $line -format "%h" info:`
	echo "   \"x_size\" : $width,"
	echo "   \"y_size\" : $height"
	echo "},"
done >> $TFILE
sed -e '$d' $TFILE
echo "}"
echo "]"
rm $TFILE
