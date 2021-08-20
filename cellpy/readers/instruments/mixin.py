"""
When you make a new loader you have to subclass the Loader class.
Remember also to register it in cellpy.cellreader.

(for future development, not used very efficiently yet).
(and if you figure out a better name for this module, please let me know).
"""

import abc

import cellpy.readers.core as core

MINIMUM_SELECTION = [
    "Data_Point",
    "Test_Time",
    "Step_Time",
    "DateTime",
    "Step_Index",
    "Cycle_Index",
    "Current",
    "Voltage",
    "Charge_Capacity",
    "Discharge_Capacity",
    "Internal_Resistance",
]


class AtomicLoad(object):
    """Atomic loading class"""

    pass


class Loader(AtomicLoad, metaclass=abc.ABCMeta):
    """Main loading class"""

    # TODO: should also include the functions for getting cellpy headers etc here

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
        """Loads data into a Cell object and returns it"""
        pass

    def identify_last_data_point(self, data):
        return core.identify_last_data_point(data)
