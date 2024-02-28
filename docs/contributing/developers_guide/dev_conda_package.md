# Create `conda` package

This is a short description on how to update the conda-forge recipe for `cellpy`:

- Fork
  : If not already done, make a fork of <https://github.com/conda-forge/cellpy-feedstock>
- Clone
  : If not already done, clone the repo (your-name/cellpy-feedstock)

    ```pycon
    >>> git clone https://github.com/your-name/cellpy-feedstok.git
    >>> git remote add upstream https://github.com/conda-forge/cellpy-feedstock
    ```
- Get recent changes
  : ```pycon
    >>> git fetch upstream
    >>> git rebase upstream/main
    ```

    This can also be done (I think) via the web interface by navigating to
    your fork and clicking the button "Sync fork".
- Make a new branch in your local clone
  : ```pycon
    >>> git checkout -b update_x_x_x
    ```
- Edit
  : - hash (`pypi` - `release history` - `Download files`)
    - version (use normalized format *e.g.* `0.5.2a3` not `0.5.2.a3`!)
    - build number (should be 0 for new versions)
- Add and commit
  : e.g. "updated feedstock to version 1.0.1"
- Push
  : ```pycon
    >>> git push origin <branch-name>
    ```
- Re-render if needed (different requirements, platforms, issues)
  : ```pycon
    >>> conda install -c conda-forge conda-smithy
    >>> conda smithy rerender -c auto
    ```

    This can also be done (I think) via adding a special
    comment during the pull request/merging on github.
- Create a pull request via the web interface by navigating to
  <https://github.com/your-name/cellpy-feedstok.git> with your web browser
  and clicking the button create pull request.
- Wait until the automatic checks have complete (takes several minutes)
- Merge pull request (big green button)
- Drink a cup of coffee or walk the dog
- Check if the new version is there:
  : ```pycon
    >>> conda search -f cellpy
    ```
- Now you can delete the branch (if you want)
