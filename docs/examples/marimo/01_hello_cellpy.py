import marimo

__generated_with = "0.23.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(
        r"""
        # Hello cellpy (marimo)

        Tiny spike showing that [marimo](https://marimo.io) notebooks can appear
        in the cellpy docs. The page you are reading was exported with
        [`marimo-md-export`](https://jmarshrossney.github.io/marimo-md-export/)
        — static markdown plus embedded outputs, no Pyodide in the site.

        Source:
        [`01_hello_cellpy.py`](https://github.com/jepegit/cellpy/blob/master/docs/examples/marimo/01_hello_cellpy.py)
        — run locally with `marimo edit docs/examples/marimo/01_hello_cellpy.py`.
        """
    )
    return


@app.cell
def _():
    import matplotlib.pyplot as plt

    from cellpy.utils import example_data

    return example_data, plt


@app.cell
def _(example_data, mo):
    c = example_data.cellpy_file()
    n_cycles = c.get_number_of_cycles()
    mo.md(f"Loaded the bundled example cellpy file — **{n_cycles}** cycles.")
    return (c,)


@app.cell
def _(c, plt):
    # Keep the figure light: a few summary points, PNG-friendly matplotlib.
    summary = c.data.summary
    cycles = summary[c.schema.summary.cycle_num]
    charge = summary[c.schema.summary.charge_capacity]

    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.plot(cycles, charge, marker="o", markersize=3, linewidth=1)
    ax.set_xlabel("Cycle")
    ax.set_ylabel("Charge capacity")
    ax.set_title("Example cell — charge capacity vs cycle")
    fig.tight_layout()
    fig
    return


if __name__ == "__main__":
    app.run()
