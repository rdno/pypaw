#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Methods that contains utils for adjoint sources

:copyright:
    Wenjie Lei (lei@princeton.edu), 2016
:license:
    GNU General Public License, Version 3
    (http://www.gnu.org/copyleft/gpl.html)
"""
from __future__ import (absolute_import, division, print_function)
import numpy as np
from pyadjoint import AdjointSource
from pytomo3d.window.write_window import get_json_content
from pyflex.window import Window


def smart_transform_window(windows):
    """
    Smart tranfer window object to dict if it is type of pyflex.Window

    :param windows:
    :return:
    """
    if isinstance(windows[0][0], dict):
        all_windows = windows
    elif isinstance(windows[0][0], Window):
        all_windows = []
        for chan_win in windows:
            _chan_win_list = [get_json_content(i) for i in chan_win]
            all_windows.append(_chan_win_list)
    else:
        raise ValueError("Not recgonized type of window")

    return all_windows


def ensemble_fake_adj(stream, time_offset=0.0):
    """
    Ensemble fake adjoint sources from stream, for test purpose
    """

    adjsrc_dict = dict()
    comps = ["Z", "R", "T"]
    nwin_dict = dict()
    for comp in comps:
        tr = stream.select(channel="*%s" % comp)[0]
        adj = AdjointSource("waveform_misfit", misfit=0.0, dt=tr.stats.delta,
                            min_period=50.0, max_period=100.0,
                            component=tr.stats.channel[-1],
                            adjoint_source=tr.data, network=tr.stats.network,
                            station=tr.stats.station)
        adjsrc_dict[tr.id] = adj
        nwin_dict[tr.id] = 1

    return adjsrc_dict, nwin_dict


def change_channel_name(adjsrcs, channel):
    """
    Change adjoint source channel name
    """
    for adj in adjsrcs:
        adj.component = channel + adj.component[-1]


def check_multiple_instruments(adjsrcs):
    """
    Check if there are mutiple instruments for one component
    This is very important because if there is only one instrument
    for one component, we can define the path shorter and change
    channel name to "MX" to follow the specfem style
    """
    name_list = []
    adj_dict = {}
    for adj in adjsrcs:
        cat = adj.component[-1]
        if cat not in adj_dict:
            adj_dict[cat] = []
        adj_id = "%s.%s.%s.%s" % (adj.network, adj.station,
                                  adj.location, adj.component)
        adj_dict[cat].append(adj_id)
        name_list.append(adj_id)

    if len(set(name_list)) != len(name_list):
        raise ValueError("Error on adjoint source(%s.%s) since it has"
                         "duplicate name on adjoint source: %s"
                         % (adj.network, adj.station, name_list))

    _flag = False
    for cat_info in adj_dict.itervalues():
        if len(cat_info) > 1:
            _flag = True
            break
    return _flag


def reshape_adj(adjsrcs, time_offset, staxml, dtype=np.float32,
                default_specfem_channel="MX"):
    """
    Reshape adjsrcs to a certain structure required by pyasdf writer
    """
    if not isinstance(adjsrcs, list):
        raise ValueError("Input ajdsrcs must be a list of adjoint sources")

    vtype = "AuxiliaryData"
    reshape_list = []
    tag_list = []

    # extract station information
    sta_lat = staxml[0][0].latitude
    sta_lon = staxml[0][0].longitude
    sta_ele = staxml[0][0].elevation
    sta_dep = staxml[0][0][0].depth

    # sanity check to see if there are multiple instruments
    _multiple_flag = check_multiple_instruments(adjsrcs)

    if not _multiple_flag:
        change_channel_name(adjsrcs, default_specfem_channel)

    for adj in adjsrcs:
        adj_array = np.asarray(adj.adjoint_source, dtype=dtype)

        station_id = "%s.%s" % (adj.network, adj.station)

        parameters = {"dt": adj.dt, "time_offset": time_offset,
                      "misfit": adj.misfit,
                      "adjoint_source_type": adj.adj_src_type,
                      "min_period": adj.min_period,
                      "max_period": adj.max_period,
                      "latitude": sta_lat, "longitude": sta_lon,
                      "elevation_in_m": sta_ele, "depth_in_m": sta_dep,
                      "station_id": station_id, "component": adj.component,
                      "location": adj.location,
                      "units": "m"}

        if _multiple_flag:
            tag = "%s_%s_%s_%s" % (adj.network, adj.station,
                                   adj.location, adj.component)
        else:
            tag = "%s_%s_%s" % (adj.network, adj.station, adj.component)

        tag_list.append(tag)

        dataset_path = "AdjointSources/%s" % tag

        _reshape = {"object": adj_array, "type": vtype,
                    "path": dataset_path, "parameters": parameters}

        reshape_list.append(_reshape)

    # check if there are different adjoint sources with the same tag. If so,
    # the writer won't be able to write out because of the same dataset path
    if len(set(tag_list)) != len(tag_list):
        raise ValueError("Duplicate tag in adjoint sources list: %s" %
                         tag_list)

    return reshape_list


def _stats_channel_window(adjsrcs, windows):
    """
    Determine number of windows on each channel of each component.
    """
    adj_dict = {}
    for idx, adj in enumerate(adjsrcs):
        adj_id = "%s.%s.%s.%s" % (adj.network, adj.station, adj.location,
                                  adj.component)
        adj_dict[adj_id] = idx

    adj_win_dict = {}
    for chan_win in windows.itervalues():
        if len(chan_win) == 0:
            continue
        chan_id = chan_win[0]["channel_id"]
        adj_win_dict[chan_id] = len(chan_win)

    new_win_dict = {}
    for key in adj_win_dict:
        if key in adj_dict:
            new_win_dict[key] = adj_win_dict[key]

    return adj_dict, new_win_dict


def calculate_chan_weight(adjsrcs, windows_sta):
    """
    Calcualte window weights based on adjoint sources and windows

    :param adjsrcs:
    :param windows_sta:
    :return:
    """

    _, adj_win_dict = _stats_channel_window(adjsrcs, windows_sta)

    comp_dict = {}
    for tr_id, nwins in adj_win_dict.iteritems():
        comp = "MX%s" % tr_id.split(".")[-1][-1]
        if comp not in comp_dict:
            comp_dict[comp] = {}
        comp_dict[comp][tr_id] = nwins

    for comp, comp_wins in comp_dict.iteritems():
        ntotal = 0
        for chan_id, chan_win in comp_wins.iteritems():
            ntotal += chan_win
        for chan_id, chan_win in comp_wins.iteritems():
            comp_dict[comp][chan_id] = chan_win / ntotal

    return comp_dict
