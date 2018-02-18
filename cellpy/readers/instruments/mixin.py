"""
Contains classes that are sub-classed by the different loaders
(for future development, not used very efficiently yet).
"""

# Just for self-studying and fun at the moment...
# Note to myself: use Abstract Base Classes.


class AtomicLoad(object):
    """Atomic loading class"""
    pass


class Loader(AtomicLoad):
    """Main loading class"""

    @staticmethod
    def get_raw_units():
        """Include the settings for the units used by the instrument.

        The units are defined w.r.t. the SI units ('unit-fractions'; currently only units that are multiples of
        Si units can be used). For example, for current defined in mA, the value for the
        current unit-fraction will be 0.001.

        Returns: dictionary containing the unit-fractions for current, charge, and mass

        """
        raise NotImplementedError

