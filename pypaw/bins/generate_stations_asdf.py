#!/usr/bin/env python
"""
Scripts that generate stations file from asdf file. If
there are stations in waveforms, then a file `STATIONS_waveform`
will be generated. Or if there are stations in AuxlilaryData,
then a file `STATIONS_ADJOINT` will be generated.

:copyright:
    Wenjie Lei (lei@princeton.edu), 2016
:license:
    GNU General Public License, Version 3
    (http://www.gnu.org/copyleft/gpl.html)
"""
from __future__ import (print_function, division)

import argparse
import collections
import os

import pyasdf

from pypaw.stations import extract_adjoint_stations
from pypaw.stations import extract_waveform_stations
from pypaw.stations import write_stations_file


def generate_waveform_stations(asdf, outputfn):
    print("Input asdf: %s" % asdf)
    sta_dict = extract_waveform_stations(asdf)

    print("Output file: %s" % outputfn)
    print("Number of stations: %d" % len(sta_dict))
    if len(sta_dict) > 0:
        write_stations_file(sta_dict, outputfn)


def generate_adjoint_stations(asdf, outputfn):
    print("Input asdf: %s" % asdf)
    sta_dict = extract_adjoint_stations(asdf)

    print("Output file: %s" % outputfn)
    print("Number of stations: %d" % len(sta_dict))
    if len(sta_dict) > 0:
        write_stations_file(sta_dict, outputfn)


def main():
    parser = argparse.ArgumentParser(
        description="Generate SPECFEM-like STATION file")
    parser.add_argument('-o', action='store', dest="outputfn",
                        default="STATIONS",
                        help="output station filename prefix")
    parser.add_argument('filename', help="Input ASDF filename")

    args = parser.parse_args()
    if not os.path.exists(args.filename):
        raise ValueError("Input file not exists: %s" % args.filename)

    ds = pyasdf.ASDFDataSet(args.filename, mode='r')
    generate_waveform_stations(ds, args.outputfn)

    adjoint_fn = args.outputfn + ".ADJOINT"
    generate_adjoint_stations(ds, adjoint_fn)


if __name__ == '__main__':
    main()
