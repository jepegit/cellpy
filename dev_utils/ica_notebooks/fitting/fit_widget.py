import logging

import ipywidgets as widgets
from IPython.display import display

import holoviews as hv


class SiliconPeaksFitWidget(widgets.VBox):
    def __init__(self, silicon_peaks, x, y, name=None):
        """ """
        #    [ ]             jitter
        #    [x] |-----o--|  scale
        #    [x] |-----o--|  shift
        #    [x] |-----o--|  sigma_p1
        #    [x] |-----o--|  max_point
        # TODO:
        # Need to implement result (and parameters) and update (as default) + button for reset
        # Need to make this work for CompositeEnsamble

        self.peaks_object = silicon_peaks
        self.x = x
        self.y = y
        self.invert_res = False
        self.invert_dq = False

        self.result = None

        if name is None:
            name = self.peaks_object.name

        jitter = self.peaks_object.jitter
        scale = self.peaks_object.scale
        offset = self.peaks_object.offset
        offset_vary = self.peaks_object.params["SiOffsetc"].vary
        shift = self.peaks_object.shift
        sigma_p1 = self.peaks_object.sigma_p1
        max_point = self.peaks_object.max_point
        crystalline = self.peaks_object.crystalline
        compress = self.peaks_object._compress
        expand = self.peaks_object._expand

        self.plot_output = widgets.Output()
        self.log_output = widgets.Output()
        self.output_to_log = False
        self.plot_fixed = False
        self.auto_clear_log = True

        self.w_name = widgets.Label(f"{name}")

        self.w_jitter = widgets.Checkbox(value=jitter, description="jitter")
        self.w_crystalline = widgets.Checkbox(
            value=crystalline, description="crystalline"
        )

        self.w_scale = widgets.FloatSlider(
            value=scale,
            min=0.00001,
            max=100 * scale,
            continuous_update=False,
            description="scale",  # Currently using the description to link up to params (so you have to live with the bad names)
        )

        self.w_offset = widgets.FloatSlider(
            value=offset,
            min=0.0,
            max=max_point,
            continuous_update=False,
            description="offset",  # Currently using the description to link up to params (so you have to live with the bad names)
        )
        self.w_offset_vary = widgets.Checkbox(
            value=offset_vary, description="offset_vary"
        )

        self.w_shift = widgets.FloatSlider(
            value=shift,
            min=-1,
            max=1,
            step=0.01,
            continuous_update=False,
            description="shift",
        )

        self.w_sigma_p1 = widgets.FloatSlider(
            value=sigma_p1,
            min=0.000000001,
            max=10 * sigma_p1,
            step=0.01,
            continuous_update=False,
            description="sigma_p1",
        )

        self.w_max_point = widgets.FloatSlider(
            value=max_point,
            min=0.00001,
            max=10 * max_point,
            continuous_update=False,
            description="max_point",
        )

        self.w_fit = widgets.Button(description="Fit!")

        self.clear = widgets.Button(description="Clear!")

        self.w_fit.on_click(self.fit)
        self.clear.on_click(self.clear_log)
        self.w_jitter.observe(self.on_w_change, "value")
        self.w_scale.observe(self.on_w_change, "value")
        self.w_offset_vary.observe(self.on_w_change, "value")
        self.w_offset.observe(self.on_w_change, "value")
        self.w_shift.observe(self.on_w_change, "value")
        self.w_sigma_p1.observe(self.on_w_change, "value")
        self.w_max_point.observe(self.on_w_change, "value")
        self.w_crystalline.observe(self.on_w_change, "value")

        self.widget_ids = [
            "scale",
            "offset",
            "shift",
            "sigma_p1",
            "max_point",
            "crystalline",
        ]

        super(SiliconPeaksFitWidget, self).__init__()

        widget_box = widgets.VBox(
            [
                self.w_name,
                self.w_crystalline,
                self.w_jitter,
                self.w_offset_vary,
                self.w_scale,
                self.w_offset,
                self.w_shift,
                self.w_sigma_p1,
                self.w_max_point,
                widgets.HBox([self.w_fit, self.clear]),
            ]
        )

        row_1 = widgets.HBox([widget_box, self.plot_output])
        row_2 = self.log_output

        self.children = [row_1, row_2]

        self.update_plot("initial")

    def fit(self, change=None, y=None, x=None):
        # TODO: need to implement turning off y and x

        _old_shift = self.peaks_object.shift
        _old_max_point = self.peaks_object.max_point
        _old_scale = self.peaks_object.scale

        if y is None:
            y = self.y

        if x is None:
            x = self.x

        if self.invert_dq:
            y = -y

        self.result = self.peaks_object.fit(y, x=x)
        if self.output_to_log:
            with self.log_output:
                if self.auto_clear_log:
                    self.log_output.clear_output()
                display(self.result)
                print(self.peaks_object)

        logging.info(f"auto update: {self.peaks_object.auto_update_from_fit}")
        _new_shift = self.peaks_object.shift
        _new_max_point = self.peaks_object.max_point
        _new_scale = self.peaks_object.scale
        logging.info(f"shift from {_old_shift} to {_new_shift}")
        logging.info(f"max_point from {_old_max_point} to {_new_max_point}")
        logging.info(f"scale from {_old_scale} to {_new_scale}")

        self.update_plot("new_fit")

        self.plot_fixed = True
        for what in self.widget_ids:
            value = getattr(self.peaks_object, what)
            logging.info(f" -> update widget. widget: {what} value: {value}")
            w = "w_" + what
            getattr(self, w).value = value
        self.plot_fixed = False

    def on_w_change(self, change):

        name = change.owner.description
        value = change.new
        logging.info(f"change observed name: {name} value: {value}")

        if name == "offset_vary":
            logging.info(
                f"old: {self.peaks_object.params['SiOffsetc'].vary} new: {value}"
            )
            self.peaks_object.params["SiOffsetc"].vary = value
        elif name == "jitter":
            setattr(self.peaks_object, name, value)
        else:
            setattr(self.peaks_object, name, value)
            self.peaks_object.init()  # This removes the link to from the parameters to the widgets :-(

        self.update_plot(name)

    def _create_plot_object(
        self,
        components=None,
        group_title="fit",
        invert_dq=False,
        invert_res=False,
        width=500,
        height=500,
        size=8,
    ):

        if self.invert_dq:
            y = -self.y
        else:
            y = self.y

        i = 1
        if self.invert_res:
            i = -1
        logging.info("-> creating plot object")
        raw = hv.Points((self.x, y), label="raw", group=group_title).opts(
            width=width,
            height=height,
            size=size,
            alpha=0.3,
            xlabel="Voltage",
            ylabel="dQ/dv",
        )
        if components is not None:
            logging.info("-> components are not None")
            prt = {}
            for key in components:
                if not key.endswith("Scale"):
                    prt[key] = hv.Curve(
                        (self.x, i * components[key]), group=group_title
                    )
            return raw * hv.NdOverlay(prt)

        prt = {
            "init": hv.Curve(
                (self.x, i * self.result.init_fit), group=group_title
            ).opts(alpha=0.5, tools=["hover"]),
            "best": hv.Curve(
                (self.x, i * self.result.best_fit), group=group_title
            ).opts(tools=["hover"]),
        }

        parts = self.result.eval_components(x=self.x)
        if not parts:
            logging.info("-> no parts extracted")

        s = (
            self.peaks_object.scale
        )  # set this to 1 if you dont want to use the scale factor when plotting
        for key in parts:
            if not key.endswith("Scale"):
                logging.info(f"-> adding {key} to the plot (scaled)")
                prt[key] = hv.Curve(
                    (self.x, i * s * parts[key]), group=group_title
                ).opts(tools=["hover"])

        return raw * hv.NdOverlay(prt)

    def update_plot(self, name):
        if self.plot_fixed:
            logging.info("sorry, plot is fixed")
            return

        if name in [
            "scale",
            "shift",
            "offset",
            "sigma_p1",
            "max_point",
            "initial",
            "crystalline",
            "new_fit",
        ]:

            with self.plot_output:
                if name == "new_fit":
                    logging.info("-------new-fit-------")
                    plotwindow = self._create_plot_object()
                else:
                    component = self.peaks_object.peaks.eval(
                        self.peaks_object.params, x=self.x
                    )
                    components = {"Init": component}
                    plotwindow = self._create_plot_object(components=components)
                self.plot_output.clear_output(wait=True)
                display(plotwindow)

    def clear_log(self, change=None):
        self.log_output.clear_output()

    def experimental(self, change=None):
        with self.log_output:
            print(self.peaks_object)

    def set_min(self, what, value):
        w = "w_" + what
        getattr(self, w).min = value

    def set_max(self, what, value):
        w = "w_" + what
        getattr(self, w).max = value

    def set_value(self, what, value):
        logging.info(f"setting value ({value}) to widget (w_{what})")
        w = "w_" + what
        getattr(self, w).value = value

    def set_step(self, what, value):
        w = "w_" + what
        getattr(self, w).step = value
