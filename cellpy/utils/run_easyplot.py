# This is a test file and will be replaced by a jupyter notebook example in the tutorial section when easyplot functionality is done.

if __name__ == "__main__":
    import cellpy
    from cellpy.utils import easyplot

    files = ["./data/raw/20160805_test001_45_cc_01.res"]

    easyplot.plot(files)