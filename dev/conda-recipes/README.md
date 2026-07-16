# Conda-forge recipe drafts (1.1.0.post1)

`cellpycore` is **not** on conda-forge yet. Order of operations:

1. Submit `cellpycore/` to [conda-forge/staged-recipes](https://github.com/conda-forge/staged-recipes)
   (new package). Wait until `conda-forge/cellpycore-feedstock` exists and `0.2.1` builds.
2. Open/merge the `cellpy` feedstock PR that bumps to `1.1.0.post1` and depends on
   `cellpycore ==0.2.1`.

Drafts here match PyPI `cellpy==1.1.0.post1` / `cellpycore==0.2.1`.
