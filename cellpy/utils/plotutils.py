# -*- coding: utf-8 -*-
"""
Utilities for helping to plot cellpy-data.
"""

import os
import warnings
import logging
import itertools

logger = logging.getLogger(__name__)
logging.captureWarnings(True)

SYMBOL_DICT = {"all": ['s', 'o', 'v', '^', '<', '>', 'D', 'p', '*', '1', '2', '.', ',',
                       '3', '4', '8', 'p', 'd', 'h', 'H', '+', 'x', 'X', '|', '_'],
               "simple": ['s', 'o', 'v', '^', '<', '>', '*', 'd'],
               }

# noinspection SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection
COLOR_DICT = {'classic': [u'b', u'g', u'r', u'c', u'm', u'y', u'k'],
              'grayscale': [u'0.00', u'0.40', u'0.60', u'0.70'],
              'bmh': [u'#348ABD', u'#A60628', u'#7A68A6', u'#467821', u'#D55E00', u'#CC79A7', u'#56B4E9',
                      u'#009E73', u'#F0E442', u'#0072B2'],
              'dark_background': [u'#8dd3c7', u'#feffb3', u'#bfbbd9', u'#fa8174', u'#81b1d2', u'#fdb462',
                                  u'#b3de69', u'#bc82bd', u'#ccebc4', u'#ffed6f'],
              'ggplot': [u'#E24A33', u'#348ABD', u'#988ED5', u'#777777', u'#FBC15E', u'#8EBA42', u'#FFB5B8'],
              'fivethirtyeight': [u'#30a2da', u'#fc4f30', u'#e5ae38', u'#6d904f', u'#8b8b8b'],
              'seaborn-colorblind': [u'#0072B2', u'#009E73', u'#D55E00', u'#CC79A7', u'#F0E442', u'#56B4E9'],
              'seaborn-deep': [u'#4C72B0', u'#55A868', u'#C44E52', u'#8172B2', u'#CCB974', u'#64B5CD'],
              'seaborn-bright': [u'#003FFF', u'#03ED3A', u'#E8000B', u'#8A2BE2', u'#FFC400', u'#00D7FF'],
              'seaborn-muted': [u'#4878CF', u'#6ACC65', u'#D65F5F', u'#B47CC7', u'#C4AD66', u'#77BEDB'],
              'seaborn-pastel': [u'#92C6FF', u'#97F0AA', u'#FF9F9A', u'#D0BBFF', u'#FFFEA3', u'#B0E0E6'],
              'seaborn-dark-palette': [u'#001C7F', u'#017517', u'#8C0900', u'#7600A1', u'#B8860B', u'#006374'],
              }


def create_colormarkerlist_for_info_df(info_df, symbol_label="all", color_style_label="seaborn-colorblind"):
    logger.debug("symbol_label: " + symbol_label)
    logger.debug("color_style_label: " + color_style_label)
    groups = info_df.groups.unique()
    sub_groups = info_df.sub_groups.unique()
    return create_colormarkerlist(groups, sub_groups, symbol_label, color_style_label)


def create_colormarkerlist(groups, sub_groups, symbol_label="all", color_style_label="seaborn-colorblind"):
    symbol_list = SYMBOL_DICT[symbol_label]
    color_list = COLOR_DICT[color_style_label]

    # checking that we have enough colors and symbols (if not, then use cycler (e.g. reset))
    color_cycler = itertools.cycle(color_list)
    symbol_cycler = itertools.cycle(symbol_list)
    _color_list = []
    _symbol_list = []
    for i in groups:
        _color_list.append(next(color_cycler))
    for i in sub_groups:
        _symbol_list.append(next(symbol_cycler))
    return _color_list, _symbol_list


if __name__ == "__main__":
    pass
