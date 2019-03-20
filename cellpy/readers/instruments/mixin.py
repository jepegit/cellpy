"""
Contains classes that are sub-classed by the different loaders
(for future development, not used very efficiently yet).
"""

import abc

# Just for self-studying and fun at the moment...
# Note to myself: use Abstract Base Classes.


class AtomicLoad(object):
    """Atomic loading class"""
    pass


class Loader(AtomicLoad, metaclass=abc.ABCMeta):
    """Main loading class"""

    @staticmethod
    @abc.abstractmethod
    def get_raw_units():
        """Include the settings for the units used by the instrument.

        The units are defined w.r.t. the SI units ('unit-fractions'; currently only units that are multiples of
        Si units can be used). For example, for current defined in mA, the value for the
        current unit-fraction will be 0.001.

        Returns: dictionary containing the unit-fractions for current, charge, and mass

        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_raw_limits(self):
        """Include the settings for how to decide what kind of step you are examining here.

        The raw limits are 'epsilons' used to check if the current and/or voltage is stable (for example
        for galvanostatic steps, one would expect that the current is stable (constant) and non-zero).
        It is expected that different instruments (with different resolution etc.) have different
        'epsilons'.

        Returns: the raw limits (dict)

        """
        raise NotImplementedError

    @abc.abstractmethod
    def loader(self, *args, **kwargs):
        """Loads data into a DataSet object and returns it"""
        pass


