import os
import logging
import warnings
from pprint import pprint
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from cellpy import cellreader, log
from cellpy.utils import ica

from lmfit import Parameters
from lmfit.models import (
    GaussianModel,
    PseudoVoigtModel,
    ExponentialGaussianModel,
    SkewedGaussianModel,
    LorentzianModel,
    SkewedVoigtModel,
    ConstantModel,
)
from lmfit import CompositeModel

# TODO: move to utils
# TODO: backprop for CompositeEnsemble [x]
# TODO: implement shift as a ConstantModel or expression
# TODO: make tests
# TODO: methods for collecting results from multiple fits
# TODO: method for reading yaml files (or similar) with peak definitions
# TODO: method for saving peak fits and definitions (picle?)
# TODO: check if updating and reseting parameters after fitting is sensible


class PeakEnsemble:
    """A PeakEnsemble consists of a scale , an offset, and a set of peaks.

    v.0.0.2

    The PeakEnsemble can be fitted with all the internal parameters fixed while only
    the scale parameter is varied (jitter=False), or the scale parameter is fixed while
    the internal parameters (individual peak heights etc) varied.

    Example:
        class SiliconPeak(PeakEnsemble):
            def __init__():
                super().__init__()
                self.name = name  # Set a prefix name
                self.prefixes = [self.name + "Scale", self.name + "01"]]
                self.peak_types = [ConstantModel, SkewedGaussianModel]
                self.a_new_variable = 12.0
                self._read_peak_definitions()
                self._init_peaks()

            def _read_peak_definitions(self):
                self._peak_definitions = {
                ....

            def _init_peaks(self):
                self._peaks = self._create_ensemble()
                self._set_hints()
                self._set_custom_hints()

            def _set_custom_hints(self):
                ....

    Attributes:
        shift (float): A common shift for all peaks in the ensemble. Should be able to
           fit this if jitter is False. TODO: check this up.
        name (str): Identification label that will be put in front of all peak parameter
           names.
        fixed (bool):
        jitter (bool): Allow for individual fitting of the peaks in the ensemble
            (defaults to False).
        max_point (float): The max point of the principal peak.
        scale (float): An overall scaling parameter (fitted if jitter=False).
        sigma_p1 (float): Sigma value for the principal peak (usually the first peak).
            When creating the peak
            ensemble, parameters for the principal peak is set based on absolute values,
            while the other
            peak parameters are set based on relative values to the principal peak.
        prefixes (list): Must be set in the subclass.

    Notes:
        The function ``_read_peak_definitions`` should store the peak definitions in the
        attribute ``_peak_definitions``.

        The ``_peak_definitions`` should be a dictionary with peak properties as keys
        (e.g. "amplitude", "sigma").
        Each dictionary value is a (nested) list where the first item is the value for
        the principal peak, the
        second item is a tuple describing how to set the limits (min, max) for the peak.
        Later items corresponds
        to new peaks where the values are given relative to the principal peak:

        "key": [
            v, ((f_min, s_min), (f_max, s_max)),   # principal peak
            (f_v, s_v),                            # next peak
            .....
        ]

        where, for the principal peak we have:

            v is the value,
            f_min * (v + s_min) is the min limit
            f_max * (v + s_max) is the max limit

        for subsequent peaks, replace v with the f_v * (v + s_v)

    Edits:
        1. It seems now more clear to me that one should use the parameter class
        directly to tweak the actual
           individual parameters. Currently, I have been using the Model class and used
           parameter hints to
           change limits and values etc. I don't think I will have to remove this option
           yet, but use parameter in addition.

    """

    def __init__(
        self,
        fixed=True,
        name=None,
        max_point=1.0,
        shift=0.0,
        sigma_p1=0.01,
        scale=1.0,
        offset=0.0,
        jitter=False,
        debug=False,
        sync_model_hints=False,
        auto_update_from_fit=True,
    ):
        logging.debug("-init-")
        self.shift = shift
        self.offset = offset
        self.name = name
        self.fixed = fixed  # not in use at the moment
        self.max_point = max_point
        self.jitter = jitter  # vary only shift, scale and offset if True
        self.scale = scale
        self.sigma_p1 = sigma_p1

        self.debug = debug
        self.auto_update_from_fit = auto_update_from_fit

        self.sync_model_hints = sync_model_hints
        self.peak_info = dict()
        self.peak_types = None  # this needs to defined in the child-class
        self.prefixes = None  # this needs to defined in the child-class

        self._peaks = None  # this is the Model object
        self._params = None  # this is the Parameter object
        self._result = None  # this is the fit result object

        # this is the original peak definitions
        # (needs to be provided/generated in the sub-class):
        self._peak_definitions = None

        # this will be populated in the initialisation process
        # from the peak_definitions:
        self._peak_definition_dict = None

        # parameter name as defined by LMFIT for ConstantModel
        self._var_name_scale = "c"
        self._var_name_offset = "c"
        self._var_name_shift = "Shift"

        self._index_scale = 0
        self._index_offset = 1
        self._index_primary_peak = 2

    def __str__(self):

        return "\n".join(
            [
                f"name:      {self.name}",
                f"shift:     {self.shift}",
                f"offset:    {self.offset}",
                f"max_point: {self.max_point}",
                f"jitter:    {self.jitter}",
                f"scale:     {self.scale}",
                f"sigma_p1:  {self.sigma_p1}",
            ]
        )

    def _back_propagation_from_params(self):
        principal_prefix = self.prefixes[2]

        # shift
        old_center = self._peak_definitions["center"][0]
        old_center_b = self.shift
        old_center_a = old_center - old_center_b
        new_center = self.params[principal_prefix + "center"].value
        new_shift = new_center - old_center_a

        # scale
        new_scale = self.params[self.name + "Scale" + self._var_name_scale].value

        # offset
        new_offset = self.params[self.name + "Offset" + self._var_name_offset].value

        # sigma_p1
        old_sigma_p1 = self.sigma_p1
        new_sigma_p1 = self.params[principal_prefix + "sigma"].value

        # max_point
        old_amplitude_a = self._peak_definitions["amplitude"][0]
        old_amplitude_b = (self.sigma_p1 * self.max_point) / old_amplitude_a

        new_amplitude = self.params[principal_prefix + "amplitude"].value
        new_max_point = new_amplitude * old_amplitude_b / old_sigma_p1

        self.scale = new_scale
        self.offset = new_offset
        self.shift = new_shift
        self.sigma_p1 = new_sigma_p1
        self.max_point = new_max_point
        self._custom_back_propagation_from_params()

    def _custom_back_propagation_from_params(self):
        pass

    def create_hints_from_parameters(self, prm=None):
        logging.debug(
            "   *PeakEnsemble: create_hints_from_parameters "
            "SHOULD ONLY BE A CONVENIENCE FUNC"
        )
        logging.debug(
            "  ->creating param_hints so that "
            "they are in-line with the current params"
        )

        if prm is not None:
            p = self.params[prm]
            self._peaks.set_param_hint(
                prm, min=p.min, max=p.max, value=p.value, vary=p.vary
            )
            return

        for prm in self.params:
            logging.debug(f"prm: {prm}")
            p = self.params[prm]
            self._peaks.set_param_hint(
                prm, min=p.min, max=p.max, value=p.value, vary=p.vary
            )

    def reset_peaks(self):
        logging.debug("   *PeakEnsemble: reset_peaks")
        self._init_peaks()
        self._custom_init_peaks()

    def init(self):
        logging.debug("-[PeakEnsemble.init()-]->")
        self._read_peak_definitions()
        self.reset_peaks()
        logging.debug("<-[PeakEnsemble.init()]")

    @property
    def peaks(self):
        """lmfit.CompositeModel"""
        return self._peaks

    def guess(self, y, x, **kwargs):
        """guess parameters"""
        print("2019.11.07: not implemented yet in LMFIT")
        return self._peaks.guess(y, x=x, **kwargs)

    @property
    def widgets(self):
        """ipywidgets for controlling peak variables"""
        raise NotImplementedError("This method is not ready to be used yet")

    @property
    def params(self):
        """lmfit.Parameters (OrderedDict)"""
        if self._params is None:
            self._params = self._peaks.make_params()
        return self._params

    @params.setter
    def params(self, new_params):
        # could be that I have to set each individual prm attribute
        self._params = new_params

    def make_params(self):
        return self._peaks.make_params()

    def _read_peak_definitions(self, *args, **kwargs):
        """Load peak definitions.
        The method must assign a peak definition dictionary to the
        self._peak_definitions attribute. The dictionary must have the keys
        'center', 'sigma', 'amplitude', 'gamma', with value of
           [value_P1,  bounds_P1, (fraction, distance) wrt P1 for P2, ...
            (fraction, distance) wrt P1 for Pn]

        Examples
            self._peak_definitions = {
            "center": [ 0.25 + self.shift,
                ((1.0, -0.1), (1.0, 0.1)),
                (1.0, 0.21 + self._custom_shift_p2),
            ],
            "sigma": [
                self.sigma_p1,
                ((0.5 * self._expand, 0.0), (2.0 * self._compress, 0.0)),
                (1.0, 0.0),
            ],
            "amplitude": [
                self.sigma_p1 * self.max_point / 0.4,
                ((0.001, 0.0), (100.0, 0.0)),
                (1.0, 0.0),
            ],
            "gamma": [
                1.0,  # value
                ((0.001, 0.0), (2.0, 0.0)),
                (1.0, 0.0),
            ],
        }

        Notes
           If you implement custom meta parameters (e.g. like self._custom_shift_p2 in
           the example above) you will have to implement a method for back-propagation
           if you need that in the _custom_back_propagation_from_params method.
        """
        raise NotImplementedError("This method must be implemented when sub-classing")

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, res):
        self._result = res

    @property
    def peak_definitions(self):
        return self._peak_definitions

    def _init_peaks(self):
        self._peaks = self._create_initial_ensemble()
        self._create_initial_params()

    def _custom_init_peaks(self):
        pass

    def _create_initial_ensemble(self):
        # create an ensemble of LMFIT models (scale, offset and peaks)
        logging.debug("   *PeakEnsemble: _create_ensemble")

        try:
            logging.debug(f"  - prefixes: {self.prefixes}")

            # scale
            self.peak_info[self.prefixes[self._index_scale]] = self.peak_types[
                self._index_scale
            ](prefix=self.prefixes[self._index_scale])

            # offset
            self.peak_info[self.prefixes[self._index_offset]] = self.peak_types[
                self._index_offset
            ](prefix=self.prefixes[self._index_offset])

            # first peak
            self.peak_info[self.prefixes[self._index_primary_peak]] = self.peak_types[
                self._index_primary_peak
            ](prefix=self.prefixes[self._index_primary_peak])
            logging.debug(f"  - peak_info (scale and principal peak): {self.peak_info}")

        except AttributeError:
            logging.warning("you are missing peak info")
            return

        # first peak
        p = self.peak_info[self.prefixes[self._index_primary_peak]]

        # additional peaks
        for prfx, ptype in zip(
            self.prefixes[self._index_primary_peak + 1 :],
            self.peak_types[self._index_primary_peak + 1 :],
        ):
            logging.debug(f"   peak gen: {prfx} of type {ptype}")
            self.peak_info[prfx] = ptype(prefix=prfx)
            p += self.peak_info[prfx]

        # scale
        p *= self.peak_info[self.prefixes[self._index_scale]]

        # offset
        p += self.peak_info[self.prefixes[self._index_offset]]

        logging.debug(f"  - created the following ensemble:")
        logging.debug(f"    {p}")
        return p

    def _create_default_peak_definition_dict(self):
        logging.debug("   *PeakEnsemble: _create_default_peak_definition_dict")
        value_dict = dict()
        peak_definitions = self.peak_definitions
        prefix_peak_1 = self.prefixes[self._index_primary_peak]
        for var_stub in peak_definitions:
            dd = peak_definitions[var_stub]
            val_1, ((frac_min, shift_min), (frac_max, shift_max)) = dd[0:2]

            v_dict = dict()
            v_dict[prefix_peak_1] = [
                val_1,
                frac_min * (val_1 + shift_min),
                frac_max * (val_1 + shift_max),
            ]
            for prfx, (fact, step) in zip(
                self.prefixes[self._index_primary_peak + 1 :], dd[2:]
            ):
                v_dict[prfx] = [fact * (x + step) for x in v_dict[prefix_peak_1]]

            value_dict[var_stub] = v_dict

        logging.debug("created default peak definitions")
        self._peak_definition_dict = value_dict

    def _create_initial_params(self):
        logging.debug("   *PeakEnsemble: _set_params")
        self._create_default_peak_definition_dict()
        value_dict = self._peak_definition_dict

        if self.jitter:
            vary_scale = False
            vary_offset = False
            vary_shift = False
        else:
            vary_scale = True
            vary_offset = True
            vary_shift = True

        scale = self.scale
        offset = self.offset
        shift = self.shift

        # need to add the shift variable
        shift_key = self.name + self._var_name_shift
        self.params.add(shift_key, value=shift, vary=vary_shift)
        self.params.move_to_end(shift_key, last=False)

        # setting all vars except the center of the peaks
        for prm in value_dict:
            if prm != "center":
                for peak_label in value_dict[prm]:
                    self._set_one_param(prm, peak_label)

        # setting the centers of the peaks
        self._set_center()

        prefix_scale = self.prefixes[self._index_scale]
        prefix_offset = self.prefixes[self._index_offset]
        scale_key = "".join((prefix_scale, "c"))
        offset_key = "".join((prefix_offset, "c"))

        self.params[scale_key].value = scale
        self.params[scale_key].min = 0.1 * scale
        self.params[scale_key].max = 10.0 * scale
        self.params[scale_key].vary = vary_scale

        self.params[offset_key].value = offset
        self.params[offset_key].min = offset - 100
        self.params[offset_key].max = offset + 100
        self.params[offset_key].vary = vary_offset

        if self.sync_model_hints:
            self._peaks.set_param_hint(
                scale_key, value=scale, min=0.1 * scale, max=10 * scale, vary=vary_scale
            )
            self._peaks.set_param_hint(
                offset_key,
                value=offset,
                min=offset - 100,
                max=offset + 100,
                vary=vary_offset,
            )

    def _set_center(self):
        d = self._peak_definition_dict["center"]
        shift = self.shift
        for key in d:
            if self.jitter:
                vary = True
            else:
                vary = False

            _vary = vary
            _value, _min, _max = d[key]
            _v = d[key]
            k = "".join((key, "center"))

            shift_key = self.name + self._var_name_shift
            expression = f"{_value} + {shift_key}"

            if k not in self.params.keys():
                if self.debug:
                    warnings.warn(f"{k} MISSING!")
            else:
                self.params[k].min = _min + shift
                self.params[k].max = _max + shift
                self.params[k].vary = _vary
                if _vary:
                    self.params[k].expr = None
                else:
                    self.params[k].expr = expression

                if self.sync_model_hints:
                    self._peaks.set_param_hint(
                        k, value=_value, min=_min, max=_max, vary=_vary, expr=expression
                    )

    def _set_one_param(self, key1, key2):
        logging.debug(f"setting one param ({key1}:{key2})")
        if self.jitter:
            vary = True
        else:
            vary = False

        value_dict = self._peak_definition_dict
        _vary = vary
        _value, _min, _max = value_dict[key1][key2]
        _v = value_dict[key1][key2]
        k = "".join((key2, key1))

        if k not in self.params.keys():
            if self.debug:
                warnings.warn(f"{k} MISSING!")
        else:
            self.params[k].value = _value
            self.params[k].min = _min
            self.params[k].max = _max
            self.params[k].vary = _vary

            if self.sync_model_hints:
                self._peaks.set_param_hint(
                    k, value=_value, min=_min, max=_max, vary=_vary
                )

    def set_param(self, key, value=None, minimum=None, maximum=None, vary=None):
        if key not in self.params.keys():
            if self.debug:
                warnings.warn(f"Trying to set missing parameter: {key}")
            return

        if self.sync_model_hints:
            self._peaks.set_param_hint(
                key, value=value, min=minimum, max=maximum, vary=vary
            )
        if value is not None:
            self.params[key].value = value

        if minimum is not None:
            self.params[key].min = minimum

        if maximum is not None:
            self.params[key].max = maximum

        if vary is not None:
            self.params[key].vary = vary

    def _fix_full(self, prefix):
        """fixes all variables (but only for this ensemble)"""
        for k in self.params:
            if k.startswith(prefix):
                self.params[k].vary = False

    def fit(self, y, **kwargs):
        params = kwargs.pop("params", self.params)
        res = self.peaks.fit(y, params=params, **kwargs)
        self.result = res

        if self.auto_update_from_fit:
            logging.debug("updating params from fit")
            self.params = self.result.params
            self._back_propagation_from_params()
        else:
            logging.debug("not updating params from fit")
        return res


class Silicon(PeakEnsemble):
    """Peak ensemble for silicon.

    This class is a sub-class of PeakEnsemble. Some new attributes are defined
    (in addition to the inherited attributes).

    Attributes:
        prefixes (list): A list of peak names used as the prefix when creating
            the peaks. The firs prefix
            should always be for the scale parameter. It is recommended not to play
            with this attribute.
            This attribute is required when subclassing PeakEnsemble
        peak_types (list of lmfit peak models): The length of this list must be the
            same as the length of the
            prefixes. It should start with a ConstantModel. This attribute is required
            when subclassing PeakEnsemble.
        crystalline (bool): Set to true if the Li3.75Si phase exists.

    """

    def __init__(
        self,
        scale=1.0,
        offset=0.0,
        crystalline=False,
        name="Si",
        max_point=1000,
        jitter=False,
        crystalline_hysteresis=0.0,
        compress=1.0,
        expand=1.0,
        **kwargs,
    ):
        """
        Parameters:
            scale (float): overall scaling of the peak ensemble
            offset (float): overall offset of the peak ensemble
            shift (float): overall shift of the peak ensemble
            crystalline (bool): set to True if the crystalline peak should be included
            name (str): pre-name that will all parameter names will start with
            max_point (float): max point of intensity
            jitter (bool): allow for individual changes between the peaks if True, fix
                all individual inter-peak prms if False.
            crystalline_hysteresis (float): additional hysteresis for crystalline peak
        """
        sigma_p1 = kwargs.pop("sigma_p1", 0.01)
        shift = kwargs.pop("shift", 0.0)
        super().__init__(
            sigma_p1=sigma_p1,
            jitter=jitter,
            scale=scale,
            max_point=max_point,
            shift=shift,
            offset=offset,
            **kwargs,
        )
        logging.debug("-[silicon -init-]->")
        self.name = name
        self.prefixes = [
            self.name + x for x in ["Scale", "Offset", "01", "02", "03"]
        ]  # Always start with scale and offset
        self.peak_types = [
            ConstantModel,  # for scaling
            ConstantModel,  # for offset
            GaussianModel,
            PseudoVoigtModel,
            PseudoVoigtModel,
        ]
        self._crystalline_prefix = self.prefixes[4]
        self._crystalline = crystalline
        self._crystalline_hysteresis = crystalline_hysteresis
        self._compress = compress
        self._expand = expand
        logging.debug("<-[silicon -init-] -> PeakEnsemble.init()")
        self.init()

    def __str__(self):
        txt = super().__str__()
        txt += "\nAdditional prms for Silicon peaks:\n"
        txt += f"crystalline:  {self._crystalline}\n"
        txt += f"c-hysteresis: {self._crystalline_hysteresis}\n"
        txt += f"compress:     {self._compress}\n"
        txt += f"expand:       {self._expand}\n"
        return txt

    def _read_peak_definitions(self):
        # Should include options to read a file her
        logging.debug("-reading peak definitions for Si")
        self._peak_definitions = {
            "center": [
                # value
                0.25,
                
                # bounds (frac-min, shift-min), (frac-max, shift-max):
                ((1.0, -0.1), (1.0, 0.1)),
                
                # value (fraction, distance) between peak 1 and peak 2:
                #   i.e. value_P2 = f * (value_P1 + d)
                (1.0, 0.21),
                
                # value (fraction, distance) between peak 1 and peak 3:
                (1.0, 0.20 + self._crystalline_hysteresis),
            ],
            "sigma": [
                self.sigma_p1,
                ((0.5 * self._expand, 0.0), (2.0 * self._compress, 0.0)),
                (1.0, 0.0),
                (0.3, 0.0),
            ],
            "amplitude": [
                self.sigma_p1 * self.max_point / 0.4,
                ((0.001, 0.0), (100.0, 0.0)),
                (1.0, 0.0),
                (1.0, 0.0),
            ],
            "gamma": [
                1.0,  # value
                ((0.001, 0.0), (2.0, 0.0)),
                (1.0, 0.0),  # does not matter (gamma is not defined for Si02)
                (1.0, 0.0),  # does not matter (gamma is not defined for Si03)
            ],
            "fraction": [
                0.5,  # value
                ((0.001, 0.0), (2.0, 0.0)),
                (1.0, 0.0),  # does not matter (fraction is not defined for Si02)
                (1.0, 0.0),  # does not matter (fraction is not defined for Si03)
            ],
        }

    def _custom_back_propagation_from_params(self):
        # _crystalline_hysterersis
        old_center = self._peak_definitions["center"][0]
        old_crystalline_hysteresis = self._crystalline_hysteresis
        old_center_crystalline = self._peak_definitions["center"][3][1]
        old_center_crystalline_b = old_center_crystalline - old_crystalline_hysteresis
        new_center_crystalline = self.params[self.prefixes[-1] + "center"].value
        new_crystalline_hysteresis = (
            new_center_crystalline - old_center_crystalline_b - old_center
        )
        self._crystalline_hysteresis = new_crystalline_hysteresis

    def _custom_init_peaks(self):
        logging.debug("-custom peak init")
        self._set_custom_params()

    def _set_custom_params(self):
        logging.debug("-setting custom param for crystalline peak")
        if not self._crystalline:
            self._unset_crystalline()

    def _unset_crystalline(self):
        logging.debug("-removing crystalline peak from fit")

        prefix_p3 = self._crystalline_prefix
        k = "".join([prefix_p3, "amplitude"])
        self.set_param(k, value=0.00001, minimum=0.000001, vary=False)
        k = "".join([prefix_p3, "fraction"])
        self.set_param(k, value=0.00001, minimum=0.000001, vary=False)
        for n in ["center", "sigma"]:
            k = "".join([prefix_p3, n])
            self.set_param(k, vary=False)

    def _set_crystalline(self):
        logging.debug("-including crystalline peak for fit")
        prefix_p3 = self._crystalline_prefix
        self._set_one_param("amplitude", prefix_p3)
        self._set_one_param("center", prefix_p3)
        self._set_one_param("sigma", prefix_p3)
        k = "".join([prefix_p3, "fraction"])
        self.set_param(k, value=1.0000, minimum=0.001, vary=True)

    @property
    def crystalline(self):
        return self._crystalline

    @crystalline.setter
    def crystalline(self, value):
        if not value and self._crystalline:
            self._unset_crystalline()
        if not self._crystalline and value:
            self._set_crystalline()

        self._crystalline = value

    @property
    def widgets(self):
        print("overrides PeakEnsemble.widgets property")
        print(
            "because it is easier to develop this here and "
            "then copy it back to the subclass"
        )


class Graphite(PeakEnsemble):
    def __init__(self, scale=1.0, name="G", jitter=False, **kwargs):
        super().__init__(max_point=10000.0, jitter=jitter, **kwargs)
        self.name = name
        self.sigma_p1 = 0.01
        self.vary = False
        self.vary_scale = True
        self.prefixes = [
            self.name + x for x in ["Scale", "Offset", "01"]
        ]  # Always start with scale, offset and shift
        self.peak_types = [ConstantModel, ConstantModel, LorentzianModel]
        self.init()

    def _read_peak_definitions(self):
        # This is a very simplified version including only one single peak.
        self._peak_definitions = {
            "center": [
                # value
                0.16,
                # bounds (frac-min, shift-min), (frac-max, shift-max)
                ((1.0, -0.05), (1.0, 0.05)),
            ],
            "sigma": [self.sigma_p1, ((0.4, 0.0), (5.0, 0.0))],
            "amplitude": [
                self.sigma_p1 * self.max_point / 0.4,
                ((0.2, 0.0), (2.0, 0.0)),
            ],
        }


class CompositeEnsemble:
    """ A collection of PeakEnsembles.

    Note! All ensembles must have unique names.

    """

    def __init__(self, *ensembles, **kwargs):
        self.ensemble = list(ensembles)
        self._peaks = None
        self._params = None
        self._result = None
        self.prefixes = None
        self.auto_update_from_fit = True
        self._join()

    def __str__(self):
        txt = " CompositeEnsemble ".center(80, "=")
        txt += "\n"
        for i, pe in enumerate(self.ensemble):
            txt += f" PeakEnsemble {i} ".center(80, "-")
            txt += "\n"
            txt += str(pe)
        txt += "\n"
        txt += 80 * "="
        return txt

    def _join(self):
        if len(self.ensemble) > 0:
            peaks_left = self.ensemble[0].peaks
            prefixes_left = self.ensemble[0].prefixes
            params_left = self.ensemble[0].params
            result_left = self.ensemble[0].result

            if len(self.ensemble) > 1:
                for ens in self.ensemble[1:]:
                    peaks_left += ens.peaks
                    prefixes_left += ens.prefixes
                    params_left += ens.params
                    if (result_left is not None) and (ens.result is not None):
                        result_left += ens.result
                    else:
                        # fallback to None if not all PeakEnsembles have a result
                        result_left = None

            self._peaks = peaks_left
            self._params = params_left
            self._result = result_left
            self.prefixes = prefixes_left

    def __add__(self, ensemble):
        self.add(ensemble)
        return self

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.add(other)

    def add(self, ensembles):
        if isinstance(ensembles, (list, tuple)):
            for e in ensembles:
                self.ensemble.append(e)
        else:
            self.ensemble.append(ensembles)
        self._join()

    @property
    def peaks(self):
        return self._peaks

    def set_param(self, name, **kwargs):
        for ens in self.ensemble:
            ens.set_param(name, **kwargs)
        self._join()

    def create_hints_from_parameters(self, prm=None):
        logging.debug(
            "creating param_hints so that they are in-line with the current params"
        )
        if prm is not None:
            p = self.params[prm]
            self._peaks.set_param_hint(
                prm, min=p.min, max=p.max, value=p.value, vary=p.vary
            )
            return

        for prm in self.params:
            p = self.params[prm]
            self._peaks.set_param_hint(
                prm, min=p.min, max=p.max, value=p.value, vary=p.vary
            )

    def reset_peaks(self):
        for ens in self.ensemble:
            ens.reset_peaks()
        self._join()

    def fit(self, y, **kwargs):
        params = kwargs.pop("params", self.params)
        res = self.peaks.fit(y, params=params, **kwargs)
        self.result = res
        if self.auto_update_from_fit:
            self._params = self.result.params
            self.back_propagation()
        return res

    def back_propagation(self):
        for ens in self.ensemble:
            ens._back_propagation_from_params()

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, res):
        self._result = res

    @property
    def params(self):
        return self._params

    @property
    def param_names(self):
        return self._peaks.param_names

    @property
    def param_hints(self):
        return self._peaks.param_hints

    @property
    def names(self):
        n = None
        if self.ensemble:
            n = [x.name for x in self.ensemble]
        return n

    @property
    def selector(self):
        n = None
        if self.ensemble:
            n = {x.name: x for x in self.ensemble}
        return n


class FitCollection:
    """Collection / iterable of Ensembles for controlling a set of fits.

    This object is used to interact with several fits facilitating easy extraction
    of key values from the fits. Typically, an experiment consists of several
    subsequent measurement series (i.e. cycles). xxx

    Objectives:

        Create a DataFrame with cycle number as one of the columns or as the index and
           the fit values as columns.

        Make it easy to use the results from fit of cycle n as starting point for
           cycle n+1.

        Save the fit(s) and load previously saved fits / collections

    """

    def __init__(self):
        self.name = None


def check_silicon():
    log.setup_logging(default_level=logging.INFO)
    my_data = cellreader.CellpyData()
    filename = "../../../testdata/hdf5/20160805_test001_45_cc.h5"
    assert os.path.isfile(filename)
    my_data.load(filename)
    my_data.set_mass(0.1)
    cha, volt = my_data.get_ccap(2)
    v, dq = ica.dqdv(volt, cha)

    # log.setup_logging(default_level=logging.DEBUG)
    print("* creating a silicon peak ensemble:")
    silicon = Silicon(shift=-0.1, max_point=dq.max(), sigma_p1=0.06)
    print(
        f"hint: {silicon.peaks.param_hints['Si02sigma']}\n"
        f"val: {silicon.params['Si02sigma']}"
    )

    print("* syncing hints:")
    silicon.create_hints_from_parameters()
    print(
        f"hint: {silicon.peaks.param_hints['Si02sigma']}\n"
        f"val: {silicon.params['Si02sigma']}"
    )

    print("* updating the Si02sigma parameter:")
    silicon.set_param("Si02sigma", minimum=0.02, vary=False)
    print(
        f"hint: {silicon.peaks.param_hints['Si02sigma']}\n"
        f"val: {silicon.params['Si02sigma']}"
    )

    print("* reset peaks:")
    silicon.reset_peaks()
    print(
        f"hint: {silicon.peaks.param_hints['Si02sigma']}\n"
        f"val: {silicon.params['Si02sigma']}"
    )

    print("WITH AUTO SYNC")
    print("* creating a silicon peak ensemble:")
    silicon = Silicon(
        shift=-0.1, max_point=dq.max(), sigma_p1=0.06, sync_model_hints=True
    )
    print(
        f"hint: {silicon.peaks.param_hints['Si02sigma']}\n"
        f"val: {silicon.params['Si02sigma']}"
    )

    print("* syncing hints:")
    silicon.create_hints_from_parameters()
    print(
        f"hint: {silicon.peaks.param_hints['Si02sigma']}\n"
        f"val: {silicon.params['Si02sigma']}"
    )

    print("* updating the Si02sigma parameter:")
    silicon.set_param("Si02sigma", minimum=0.02, vary=False)
    print(
        f"hint: {silicon.peaks.param_hints['Si02sigma']}\n"
        f"val: {silicon.params['Si02sigma']}"
    )

    print("* reset peaks:")
    silicon.reset_peaks()
    print(
        f"hint: {silicon.peaks.param_hints['Si02sigma']}\n"
        f"val: {silicon.params['Si02sigma']}"
    )

    print()
    print(" Fitting ".center(80, "-"))
    silicon = Silicon(shift=-0.1, max_point=dq.max(), sigma_p1=0.06)
    print(silicon)
    res1 = silicon.fit(-dq, x=v)
    print(res1.fit_report())
    print()
    print("New meta params")
    print(silicon)

    print("Setting crystalline")
    silicon.crystalline = True


def check_silicon_2():
    log.setup_logging(default_level=logging.INFO)
    my_data = cellreader.CellpyData()
    filename = "../../../testdata/hdf5/20160805_test001_45_cc.h5"
    assert os.path.isfile(filename)
    my_data.load(filename)
    my_data.set_mass(0.1)
    cha, volt = my_data.get_ccap(2)
    v, dq = ica.dqdv(volt, cha)

    # log.setup_logging(default_level=logging.DEBUG)
    print("* creating a silicon peak ensemble:")
    silicon = Silicon(shift=-0.1, max_point=dq.max(), sigma_p1=0.06)
    print(
        f"hint: {silicon.peaks.param_hints['Si02sigma']}\n"
        f"val: {silicon.params['Si02sigma']}"
    )

    print("Setting crystalline")
    silicon.crystalline = True
    print("Is jitter?", end=" ")
    print(silicon.jitter)
    print(silicon)

    res1 = silicon.fit(-dq, x=v)
    print(silicon)
    print(res1.fit_report())


def check_graphite():
    log.setup_logging(default_level=logging.INFO)
    my_data = cellreader.CellpyData()
    filename = "../../../testdata/hdf5/20160805_test001_45_cc.h5"
    assert os.path.isfile(filename)
    my_data.load(filename)
    my_data.set_mass(0.1)
    cha, volt = my_data.get_ccap(2)
    v, dq = ica.dqdv(volt, cha)

    # log.setup_logging(default_level=logging.DEBUG)
    print("* creating a silicon peak ensemble:")
    graphite = Graphite(shift=-0.1)

    print("Is jitter?", end=" ")
    print(graphite.jitter)
    print(graphite)

    res1 = graphite.fit(-dq, x=v)
    print(graphite)
    print(res1.fit_report())


def check_composite():
    log.setup_logging(default_level=logging.INFO)
    my_data = cellreader.CellpyData()
    filename = "../../../testdata/hdf5/20160805_test001_45_cc.h5"
    assert os.path.isfile(filename)
    my_data.load(filename)
    my_data.set_mass(0.1)
    cha, volt = my_data.get_ccap(2)
    v, dq = ica.dqdv(volt, cha)

    # log.setup_logging(default_level=logging.DEBUG)
    print("* creating a silicon peak ensemble:")
    silicon = CompositeEnsemble(Silicon(shift=-0.1), Graphite())
    print(
        f"hint: {silicon.peaks.param_hints['Si02sigma']}\n"
        f"val: {silicon.params['Si02sigma']}"
    )

    print("* syncing hints:")
    silicon.create_hints_from_parameters()
    print(
        f"hint: {silicon.peaks.param_hints['Si02sigma']}\n"
        f"val: {silicon.params['Si02sigma']}"
    )

    print("* updating the Si02sigma parameter:")
    silicon.set_param("Si02sigma", minimum=0.02, vary=False)
    print(
        f"hint: {silicon.peaks.param_hints['Si02sigma']}\n"
        f"val: {silicon.params['Si02sigma']}"
    )

    print("* reset peaks:")
    silicon.reset_peaks()
    print(
        f"hint: {silicon.peaks.param_hints['Si02sigma']}\n"
        f"val: {silicon.params['Si02sigma']}"
    )

    print("WITH AUTO SYNC")
    print("* creating a silicon peak ensemble:")
    silicon = CompositeEnsemble(
        Silicon(shift=-0.1, sync_model_hints=True), Graphite(shift=-0.03)
    )
    print(
        f"hint: {silicon.peaks.param_hints['Si02sigma']}\n"
        f"val: {silicon.params['Si02sigma']}"
    )

    print("* syncing hints:")
    silicon.create_hints_from_parameters()
    print(
        f"hint: {silicon.peaks.param_hints['Si02sigma']}\n"
        f"val: {silicon.params['Si02sigma']}"
    )

    print("* updating the Si02sigma parameter:")
    silicon.set_param("Si02sigma", minimum=0.02, vary=False)
    print(
        f"hint: {silicon.peaks.param_hints['Si02sigma']}\n"
        f"val: {silicon.params['Si02sigma']}"
    )

    print("* reset peaks:")
    silicon.reset_peaks()
    print(
        f"hint: {silicon.peaks.param_hints['Si02sigma']}\n"
        f"val: {silicon.params['Si02sigma']}"
    )

    print(" Set crystalline ".center(80, "-"))
    peaks = CompositeEnsemble(Silicon(shift=-0.1), Graphite(shift=-0.03))
    print(peaks.ensemble[0])
    log.setup_logging(default_level=logging.DEBUG)
    print(peaks.ensemble[0])
    peaks.ensemble[0].crystalline = True

    peaks.ensemble[0].crystalline = False
    print(peaks.ensemble[0])

    print()
    print(" Fitting ".center(80, "-"))
    silicon = CompositeEnsemble(Silicon(shift=-0.1), Graphite(shift=-0.03))
    print(silicon)
    res1 = silicon.fit(-dq, x=v)
    print(res1.fit_report())
    print()
    print("New meta params")
    print(silicon)


def check_backprop_composite():
    print("Checking back prop for composite ensamble")
    log.setup_logging(default_level=logging.INFO)
    my_data = cellreader.CellpyData()
    filename = "../../../testdata/hdf5/20160805_test001_45_cc.h5"
    assert os.path.isfile(filename)
    my_data.load(filename)
    my_data.set_mass(0.1)
    cha, volt = my_data.get_ccap(2)
    v, dq = ica.dqdv(volt, cha)

    # log.setup_logging(default_level=logging.DEBUG)
    print("* creating a silicon peak ensemble:")
    si_g_composite = CompositeEnsemble(
        Silicon(shift=-0.1, max_point=dq.max(), sigma_p1=0.06), Graphite(shift=-0.03)
    )

    print(si_g_composite)

    print("peak values:")

    print(f"val: {si_g_composite.params['Si01sigma']}")  # sigma_p1
    print(f"val: {si_g_composite.params['Si01center']}")  # center - b
    print(f"val: {si_g_composite.params['G01center']}")  # center - graphite

    print("\nsetting some new values:")

    si_g_composite.set_param("Si01center", value=0.18)
    si_g_composite.set_param("G01center", value=0.14)
    print(f"val: {si_g_composite.params['Si01sigma']}")
    print(f"val: {si_g_composite.params['Si01center']}")
    print(f"val: {si_g_composite.params['G01center']}")  # center - graphite

    print("BACK PROPAGATION")
    si_g_composite.back_propagation()

    # select by order
    si_ensemble = si_g_composite.ensemble[0]
    g_ensemble = si_g_composite.ensemble[1]

    # select by name
    si_ensemble = si_g_composite.selector["Si"]
    g_ensemble = si_g_composite.selector["G"]

    si_new_shift = si_ensemble.shift
    si_new_max_point = si_ensemble.max_point
    si_new_sigma_p1 = si_ensemble.sigma_p1
    g_new_shift = g_ensemble.shift

    print("- calculated back prop gives the following updated values")
    print(si_g_composite)

    print("- setting the values to a new object")
    another_si_g_composite = CompositeEnsemble(
        Silicon(
            shift=si_new_shift,
            max_point=si_new_max_point,
            sigma_p1=si_new_sigma_p1,
            compress=1.0,
            expand=1.0,
        ),
        Graphite(shift=g_new_shift),
    )

    print(another_si_g_composite)
    print(f"val: {another_si_g_composite.params['Si01sigma']}")
    print(f"val: {another_si_g_composite.params['Si01center']}")
    print(f"val: {another_si_g_composite.params['G01center']}")

    print(another_si_g_composite.prefixes)
    print("PARAM NAMES")
    print(another_si_g_composite.param_names)
    print("NAMES")
    print(another_si_g_composite.names)
    print("SELECTED Si")
    print(another_si_g_composite.selector["Si"])


def check_backprop():
    print("Checking back prop")
    log.setup_logging(default_level=logging.INFO)
    my_data = cellreader.CellpyData()
    filename = "../../../testdata/hdf5/20160805_test001_45_cc.h5"
    assert os.path.isfile(filename)
    my_data.load(filename)
    my_data.set_mass(0.1)
    cha, volt = my_data.get_ccap(2)
    v, dq = ica.dqdv(volt, cha)

    # log.setup_logging(default_level=logging.DEBUG)
    print("* creating a silicon peak ensemble:")
    silicon = Silicon(shift=-0.1, max_point=dq.max(), sigma_p1=0.06)
    print(silicon)

    print("- peak values -")

    print(f"val: {silicon.params['Si01sigma']}")  # sigma_p1
    print(f"val: {silicon.params['Si01center']}")  # center - b

    print("- setting some new values -")

    silicon.set_param("Si01center", value=0.18)
    print(f"val: {silicon.params['Si01sigma']}")
    print(f"val: {silicon.params['Si01center']}")

    silicon._back_propagation_from_params()
    new_shift = silicon.shift
    new_max_point = silicon.max_point
    new_sigma_p1 = silicon.sigma_p1

    print("- calculated back prop gives the following updated values")
    print(silicon)

    print("- setting the values to a new object")
    another_silicon = Silicon(
        shift=new_shift,
        max_point=new_max_point,
        sigma_p1=new_sigma_p1,
        compress=1.0,
        expand=1.0,
    )
    print(another_silicon)
    print(f"val: {another_silicon.params['Si01sigma']}")
    print(f"val: {another_silicon.params['Si01center']}")


if __name__ == "__main__":
    print()
    check_composite()
