drupal-rtl-checker
==================

This script detects missing RTL rules in Drupal 8 CSS files, in two ways:

1. Checking for CSS rules that contain LTR properties, but don't have a `[dir="rtl"]` equivalent.
2. Checking for LTR properties that aren't marked with the `/* LTR */` comment.

The script consists of a python diffing code, a patched
[css-flip](https://github.com/twitter/css-flip) nodejs package, and some code to
filter out false-positives in the output.

## Setting up
To set up this script to run locally, you must have the nodejs `css-flip` package
and the python `prettytable` library installed.

You should then apply the `css-flip.patch` file in this repository to your local
`css-flip` package. This patch basically makes the css-flip
package output an extra CSS file during processing, that is identical to the
input file, but with some whitespace/formatting changes.

Then, you can run the `rtl-checker.py` script with the following format:
```
python rtl-checker.py /path/to/drupal
```
The script outputs a `missing-rtl.txt` file containing a table of all the
missing RTL rules it has found.
