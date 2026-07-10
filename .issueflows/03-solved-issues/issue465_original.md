# Issue #465: conda pytest windows failed

Source: https://github.com/jepegit/cellpy/issues/465

## Original issue text

Ci schedueled failed:


Info from agent:

## Issue Analysis

The job failed during the conda environment setup step due to a **502 Bad Gateway error** when trying to download package metadata from the conda-forge repository:

```
requests.exceptions.HTTPError: 502 Server Error: Bad Gateway for url: 
https://conda.anaconda.org/conda-forge/linux-64/1bde174b2b1b538da03d3e12ddb119cf61030b0cd0b41f7f3ea4d998ab916a9b.msgpack.zst
```

This is a **transient network/service issue**, not a code problem. The conda-forge server was temporarily unavailable when the job tried to fetch package metadata.

## Solution

This type of failure is intermittent and typically resolves itself. Here are your options:

1. **Rerun the job** - The simplest solution. Click "Re-run jobs" in the GitHub Actions UI. The conda-forge server should be available on the next attempt.

2. **Add retry logic to the workflow** (if you want automated resilience):

   Update the conda environment setup step in [`.github/workflows/ci-scheduled.yml`](https://github.com/jepegit/cellpy/blob/e984a9d6727054c9ac8ae5b70717eeb048547788/.github/workflows/ci-scheduled.yml) to retry on failure:

   ```yaml
   - uses: conda-incubator/setup-miniconda@v3
     with:
       auto-update-conda: true
       miniconda-version: latest
       activate-environment: cellpy_dev
       environment-file: github_actions_environment.yml
       python-version: "3.13"
   ```

   Or wrap it with a retry mechanism using a shell script:

   ```yaml
   - name: Setup conda (with retry)
     run: |
       for i in {1..3}; do
         echo "Attempt $i..."
         if conda env update --name cellpy_dev --file github_actions_environment.yml; then
           echo "Success!"
           break
         fi
         if [ $i -lt 3 ]; then
           echo "Failed, retrying in 30 seconds..."
           sleep 30
         fi
       done
   ```

**Recommendation:** Start by rerunning the job. If it fails again with the same error, then consider adding retry logic.
