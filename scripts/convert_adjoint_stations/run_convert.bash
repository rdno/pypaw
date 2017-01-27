#!/bin/bash

#PBS -A GEO111
#PBS -N convert_adjoint_sta
#PBS -j oe
#PBS -l walltime=1:00:00
#PBS -l nodes=1

cd $PBS_O_WORKDIR
echo "pwd: `pwd`"
echo "start at `date`"

eventfile="../eventlist.wenjie"

idx=0
for event in `cat $eventfile`
do
  idx=$(( $idx + 1 ))
  echo "======================================"
  echo "[$idx]$event"
  path=paths/$event.adjoint_stations.path.json
  if [ ! -f $path ]; then
    echo "Path not exists: $path"
    exit
  fi
  pypaw-generate_adjoint_stations -f $path
  echo "Time: `date`"

done

echo
echo "job done at `date`"
