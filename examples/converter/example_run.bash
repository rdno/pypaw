#!/bin/bash

echo "Running examples..."

# #############################
# convert together using combined json file
#echo "+++++++++++++++"
#echo "Convert obsd and synt into asdf"
#python convert_asdf.py -p ./parfile/convert.par.json -v

# #############################
# convert seperately
# convert observed mseed files into hdf5 file
echo "++++++++++"
echo "Convert obsd files into asdf..."
python convert_to_asdf.py -f ./parfile/convert.obsd.json -v -s

# convert synthetic mseed files into hdf5 file
echo "+++++++++"
echo "Convert synt files into hdf5"
python convert_to_asdf.py -f ./parfile/convert.synt.json -v -s



