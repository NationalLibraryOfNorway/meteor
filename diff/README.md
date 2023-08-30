## Diff script ##
This is a simple script to compare selected fields from one version of Meteor against the current
version. The script will output the results of the diff to the console.

### Getting the `previous_results.json` file
The `previous_results.json` file is the file that contains the results of the previous diff.
To create this file do the following:
- Using git, checkout the version of Meteor you want to compare against
- Run `python diff/run_prev_diff.py` from the root directory of the project
- The script will save the results of the diff to `/diff/previous_results.json`
- Checkout to your desired branch
- Run the diff script (see below)

### How to run the diff
The diff is run by executing the following command from root directory of the project:

``` python diff/evaluate_current_version.py -f <field> [-c] ```

If `field` is not recognized, or the cache option `-c` is used before a result json file is produced,
the script will fail. Otherwise the program will output the results of the diff to the console.
