# -*- coding: utf-8 -*-
"""
Created on Tue Mar 05 16:15:14 2013

@author: jepe
"""

import copy
import itertools
import collections


class Linestyle:
    def __init__(self):
        # ----------------overall-vars------------
        self.style_label = "",
        self.style_description = "no description"
        self.overall_linewidth = 1.0
        self.overall_linestyle = "-"
        self.overall_markersize = self.overall_linewidth * 3.0 + 2.0
        self.overall_markeredgewidth = self.overall_linewidth / 2.0
        self.overall_markevery = 1
        # ----------------plot-variables----------
        self.linestyle = "-"
        self.linewidth = self.overall_linewidth
        self.color = None
        self.dashes = (6, 6)
        self.marker = "c"
        self.markeredgecolor = None
        self.markeredgewidth = 0.5
        self.markerfacecolor = None
        self.markersize = self.overall_markersize
        self.markevery = 1
        # ------------------colors-----------------
        self.color_Linen = self.make_rgb([240, 240, 230])
        self.color_One = self.make_rgb([61, 89, 171])  # cobalt
        self.color_Two = self.make_rgb([240, 143, 230])  # pinkish
        self.color_Three = self.make_rgb([64, 224, 208])  # turquoise
        self.color_Four = self.make_rgb([220, 20, 60])  # crimson
        self.color_Five = self.make_rgb([139, 69, 19])  # chocolate 4 (saddlebrown)
        self.color_Six = self.make_rgb([240, 240, 60])
        self.color_Seven = self.make_rgb([60, 240, 188])
        self.color_Eight = self.make_rgb([240, 60, 188])
        # ---sea-green-colors--------------------
        self.color_DarkSeaGreen = self.make_rgb([143, 188, 143])
        self.color_SeaGreen = self.make_rgb([46, 139, 87])
        self.color_MediumSeaGreen = self.make_rgb([60, 179, 113])
        self.color_LightSeaGreen = self.make_rgb([32, 178, 170])
        # ---grays-------------------------------
        self.color_Black = self.make_rgb([30, 30, 30])
        self.color_DimGray = self.make_rgb([105, 105, 105])
        self.color_SlateGray = self.make_rgb([112, 138, 144])
        self.color_LightSlateGray = self.make_rgb([119, 136, 153])
        self.color_Gray = self.make_rgb([190, 190, 190])
        self.color_LightGray = self.make_rgb([211, 211, 211])
        # ---orange------------------------------
        self.color_DarkOrange = self.make_rgb([255, 140, 0])
        # ------------------Line-marker-sequence----------------
        self.line_marker_sequence = [
            's',  # square
            'o',  # circle
            'v',  # triangle_down
            '^',  # triangle_up
            '<',  # triangle_left
            '>',  # triangle_right
            'D',  # diamond
            'p',  # pentagon
            'h',  # hexagon1
            '8',  # octagon
        ]

    def __str__(self):
        txt = 70 * "=" + "\n"
        txt += "    cellpy.utils.plotutils.Styles\n"
        txt += 70 * "=" + "\n"
        if self.style_label:
            txt += "style_label: %s\n" % self.style_label
            txt += "style_description: %s\n" % self.style_description
            txt += "linestyle: %s\n" % self.linestyle
            txt += "color: %s\n" % self.color
            txt += "dashes: %s\n" % (self.dashes,)
            txt += "marker: %s\n" % self.marker
            txt += "markeredgecolor: %s\n" % self.markeredgecolor
            txt += "markeredgewidth: %s\n" % self.markeredgewidth
            txt += "markerfacecolor: %s\n" % self.markerfacecolor
            txt += "markersize: %s\n" % self.markersize
            txt += "markevery: %s\n" % self.markevery

        return txt

    @staticmethod
    def make_rgb(c):
        return np.array(c, dtype="float") / 255.0

    @staticmethod
    def info_marker_types():
        all_marker_codes = [0,  # tickleft
                            1,  # tickright
                            2,  # tickup
                            3,  # tickdown
                            4,  # caretleft
                            5,  # caretright
                            6,  # caretup
                            7,  # caretdown
                            '',  # nothing
                            '*',  # star
                            ',',  # pixel
                            '.',  # point
                            '^',  # triangle_up
                            '_',  # hline
                            '|',  # vline
                            '+',  # plus
                            '<',  # triangle_left
                            '>',  # triangle_right
                            '1',  # tri_down
                            '2',  # tri_up
                            '3',  # tri_left
                            '4',  # tri_right
                            '8',  # octagon
                            'D',  # diamond
                            'd',  # thin_diamond
                            'h',  # hexagon1
                            'H',  # hexagon2
                            'o',  # circle
                            'p',  # pentagon
                            's',  # square
                            'v',  # triangle_down
                            'x',  # x
                            '$JPM$',  # render the string using mathtext
                            ]
        return all_marker_codes


class Styles:
    def __init__(self):
        style_zero = Linestyle()
        style_zero.linestyle = "-"
        self.style_zero = style_zero
        self.overall_linestyle = style_zero.overall_linestyle
        self.overall_linewidth = style_zero.overall_linewidth
        self.overall_markeredgewidth = style_zero.overall_markeredgewidth
        self.overall_markersize = style_zero.overall_markersize
        self.overall_markevery = style_zero.overall_markevery
        self.line_marker_sequence = style_zero.line_marker_sequence
        self.number_of_styles = 0
        self._generate()

    @staticmethod
    def dcopy(c):
        return copy.deepcopy(c)

    @staticmethod
    def set_one_color(styleset, color):
        styleset.color = color
        styleset.markeredgecolor = color
        styleset.markerfacecolor = color
        return styleset

    @staticmethod
    def set_marker_sequence(styleset, n):
        if n > (len(styleset.line_marker_sequence) - 1):
            n = -1  # could insert itertool here
        styleset.marker = styleset.line_marker_sequence[n]
        return styleset

    def set_overall(self, styleset):
        styleset.linestyle = self.style_zero.overall_linestyle
        styleset.linewidth = self.style_zero.overall_linewidth
        styleset.markeredgewidth = self.style_zero.overall_markeredgewidth
        styleset.markersize = self.style_zero.overall_markersize
        styleset.markevery = self.style_zero.overall_markevery
        return styleset

    def get(self, style_type, style_number):
        if style_type == "black":
            s = self.style_black[style_number]
        elif style_type == "black_open":
            s = self.style_black_open[style_number]
        elif style_type == "sea_green":
            s = self.style_sea_green[style_number]
        elif style_type == "orange":
            s = self.style_orange[style_number]

        elif style_type == "one":
            s = self.style_one[style_number]
        elif style_type == "two":
            s = self.style_two[style_number]
        elif style_type == "three":
            s = self.style_three[style_number]
        elif style_type == "four":
            s = self.style_four[style_number]
        elif style_type == "five":
            s = self.style_five[style_number]
        elif style_type == "six":
            s = self.style_six[style_number]
        elif style_type == "seven":
            s = self.style_seven[style_number]
        elif style_type == "eight":
            s = self.style_eight[style_number]

        else:
            s = self.style_black[style_number]
        return s

    def get_set(self, set_list):
        # count number of plots in each set
        style_counter = collections.OrderedDict()
        for g in set_list:
            if g in style_counter:
                style_counter[g] += 1
            else:
                style_counter[g] = 1
                # make the list of styles
                # if max_set_number > number_of_styles:
                # itertool it
        style_sets = []
        main_set_numbers = itertools.cycle(range(len(self.styles)))
        for g, count in style_counter.items():
            if g > len(self.styles):
                st = self.styles[main_set_numbers.next()]
            else:
                st = self.styles[g - 1]
            sub_set_numbers = itertools.cycle(range(len(st)))
            # generating sets for style
            for j in range(count):
                i = sub_set_numbers.next() + 1
                style_sets.append(st[i])
        return style_sets

    def initiate_style(self):
        s = self.dcopy(self.style_zero)
        s = self.set_overall(s)
        s = self.set_one_color(s, "k")
        return s

    def _generate(self):
        self.styles = []
        style_black = {}
        s = self.initiate_style()
        s = self.set_one_color(s, self.style_zero.color_Black)
        for j in range(6):
            s = self.set_marker_sequence(s, j)
            style_black[j + 1] = s
            s = self.dcopy(s)
        self.styles.append(style_black)

        style_orange = {}
        s = self.initiate_style()
        s = self.set_one_color(s, self.style_zero.color_DarkOrange)
        for j in range(6):
            s = self.set_marker_sequence(s, j)
            style_orange[j + 1] = s
            s = self.dcopy(s)
        self.styles.append(style_orange)

        style_sea_green = {}
        s = self.initiate_style()
        s = self.set_one_color(s, self.style_zero.color_SeaGreen)
        for j in range(6):
            s = self.set_marker_sequence(s, j)
            style_sea_green[j + 1] = s
            s = self.dcopy(s)
        self.styles.append(style_sea_green)

        style_one = {}
        s = self.initiate_style()
        s = self.set_one_color(s, self.style_zero.color_One)
        for j in range(6):
            s = self.set_marker_sequence(s, j)
            style_one[j + 1] = s
            s = self.dcopy(s)
        self.styles.append(style_one)

        style_two = {}
        s = self.initiate_style()
        s = self.set_one_color(s, self.style_zero.color_Two)
        for j in range(6):
            s = self.set_marker_sequence(s, j)
            style_two[j + 1] = s
            s = self.dcopy(s)
        self.styles.append(style_two)

        style_three = {}
        s = self.initiate_style()
        s = self.set_one_color(s, self.style_zero.color_Three)
        for j in range(6):
            s = self.set_marker_sequence(s, j)
            style_three[j + 1] = s
            s = self.dcopy(s)
        self.styles.append(style_three)

        style_linen = {}
        s = self.initiate_style()
        s = self.set_one_color(s, self.style_zero.color_Linen)
        for j in range(6):
            s = self.set_marker_sequence(s, j)
            style_linen[j + 1] = s
            s = self.dcopy(s)
        self.styles.append(style_linen)

        style_four = {}
        s = self.initiate_style()
        s = self.set_one_color(s, self.style_zero.color_Four)
        for j in range(6):
            s = self.set_marker_sequence(s, j)
            style_four[j + 1] = s
            s = self.dcopy(s)
        self.styles.append(style_four)

        style_five = {}
        s = self.initiate_style()
        s = self.set_one_color(s, self.style_zero.color_Five)
        for j in range(6):
            s = self.set_marker_sequence(s, j)
            style_five[j + 1] = s
            s = self.dcopy(s)
        self.styles.append(style_five)

        style_six = {}
        s = self.initiate_style()
        s = self.set_one_color(s, self.style_zero.color_Six)
        for j in range(6):
            s = self.set_marker_sequence(s, j)
            style_six[j + 1] = s
            s = self.dcopy(s)
        self.styles.append(style_six)

        style_seven = {}
        s = self.initiate_style()
        s = self.set_one_color(s, self.style_zero.color_Seven)
        for j in range(6):
            s = self.set_marker_sequence(s, j)
            style_seven[j + 1] = s
            s = self.dcopy(s)
        self.styles.append(style_seven)

        style_eight = {}
        s = self.initiate_style()
        s = self.set_one_color(s, self.style_zero.color_Eight)
        for j in range(6):
            s = self.set_marker_sequence(s, j)
            style_eight[j + 1] = s
            s = self.dcopy(s)
        self.styles.append(style_eight)

        style_black_open = {}
        s = self.initiate_style()
        s = self.set_one_color(s, "k")
        s.markerfacecolor = self.style_zero.color_LightGray
        for j in range(6):
            s = self.set_marker_sequence(s, j)
            style_black_open[j + 1] = s
            s = self.dcopy(s)
        self.styles.append(style_black_open)

        self.style_black = style_black
        self.style_orange = style_orange
        self.style_sea_green = style_sea_green
        self.style_linen = style_linen
        self.style_black_open = style_black_open
        self.style_one = style_one
        self.style_two = style_two
        self.style_three = style_three
        self.style_four = style_four
        self.style_five = style_five
        self.style_six = style_six
        self.style_seven = style_seven
        self.style_eight = style_eight

        self.number_of_styles = len(self.styles)


if __name__ == "__main__":
    import numpy as np
    import matplotlib.pyplot as plt

    _visible = True
    _label = ""
    x = np.arange(1, 10, 0.1)
    y = x ** 2
    my_styles = Styles()
    t1 = "sea_green"
    t2 = "black"
    t3 = "orange"
    t4 = "black_open"
    style_list = [t2, t2, t2, t2, t2]
    a = my_styles.get_set([1, 1, 1, 1, 1, 1, 1, 1])
    for xx in range(5):
        line_style = my_styles.get(style_list[xx], xx + 1)
        line_style = a[xx]
        print line_style
        plt.plot(x, y + 10 * xx,
                 visible=_visible,
                 label=_label,
                 linestyle=line_style.linestyle,
                 linewidth=line_style.linewidth,
                 color=line_style.color,
                 dashes=line_style.dashes,  # on, off, on, off, etc
                 marker=line_style.marker,
                 markeredgecolor=line_style.markeredgecolor,
                 markeredgewidth=line_style.markeredgewidth,
                 markerfacecolor=line_style.markerfacecolor,
                 markersize=line_style.markersize,
                 markevery=5,
                 # markevery = line_style.markevery, # 1 for all, 2 for each second, etc
                 )

    print "So-long...."
    print

    plt.ylabel("y-label")
    plt.xlabel("x-label")
    plt.show()
    print "...and thank you for the fish"
