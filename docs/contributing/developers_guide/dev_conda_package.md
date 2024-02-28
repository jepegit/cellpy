# Create conda package

This is a short description on how to update the conda-forge recipe for `cellpy`.

## Fork

If not already done, make a fork of
[the feedstock](https://github.com/conda-forge/cellpy-feedstock) on GitHub.

## Clone

If not already done, clone the repo (your-name/cellpy-feedstock)

```shell
git clone https://github.com/your-name/cellpy-feedstok.git
git remote add upstream https://github.com/conda-forge/cellpy-feedstock
```

## Get recent changes

```shell
git fetch upstream
git rebase upstream/main
```

This can also be done via the web interface by navigating to
your fork and clicking the button "Sync fork".

## Make a new branch in your local clone

```shell
 git checkout -b update_x_x_x
```
## Edit
  - hash (look in PyPI, release history, Download files)
  - version (use normalized format *e.g.* `0.5.2a3` not `0.5.2.a3`!)
  - build number (should be 0 for new versions)

## Add and commit

*e.g.* "updated feedstock to version 1.0.1"

## Push

```shell
 git push origin <branch-name>
```
## Re-render if needed

This is only needed of you change to different requirements, platforms or experience
other problems. If you are unsure, just do it.

```shell
 conda install -c conda-forge conda-smithy
 conda smithy rerender -c auto
```

This can also be done via adding a special comment during the pull request/merging on GitHub.

## Pull request and merge

- Create a pull request via the web interface by navigating to your fork of the feedstock
  `github.com/your-name/cellpy-feedstok.git` with your web browser
  and clicking the button create pull request.
- Wait until the automatic checks have complete (takes several minutes)
- Merge pull request (big green button).

## Wrap up

- Drink a cup of coffee or walk the dog
- Check if the new version is there:
```shell
 conda search -f cellpy
```
- Now you can delete the branch (if you want)
