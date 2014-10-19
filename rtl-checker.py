import subprocess
import difflib
import os
import sys
import fnmatch
from prettytable import PrettyTable

def rtl_check(filename):
    css = open(filename)
    nortl = open(filename + '.nortl', 'w')
    rtls = {}

    # Remove RTL rules from CSS file, and store them in the "rtls" dictionary.
    for line in css:
        line = line.strip()
        if line.startswith('[dir="rtl"]'):
            rules = []
            for rtl_rule in css:
                rtl_rule = rtl_rule.strip()
                if rtl_rule == '}':
                    break
                rules.append(rtl_rule)
            rtls[line] = rules
        else:
            nortl.write(line + '\n')

    css.close()
    nortl.close()

    # Flip the LTR rules using the "css-flip" npm tool. The "css-flip" tool is
    # patched here, so that it outputs a ".orig" file, that goes through the same
    # process as the flipped css, without an actual flipping! This is done to
    # prevent any whitespace/coding-style changes by going through the "css-flip"
    # tool to show up in our diff.
    subprocess.call(['css-flip', filename + '.nortl', '-o', filename + '.flipped'])

    # Find the diff between the no-rtl CSS file, and its RTL-flipped one.
    diff = list(difflib.ndiff(open(filename + '.nortl.orig').readlines(), open(filename + '.flipped').readlines()))

    # Remove Lines starting with '? ' from the diff
    cleaned = []
    for line in diff:
        if not line.startswith('?'):
            cleaned.append(line)
    diff = cleaned

    # Remove separate added or removed lines. This is caused by flipping identical
    # -left/-right properties, like this:
    #   margin-right: 0;
    #   margin-left: 0;
    # which look like this in the diff:
    # +   margin-left: 0;
    #     margin-right: 0;
    # -   margin-left: 0;
    cleaned = []
    for diff_pos in range(len(diff)):
        line = diff[diff_pos]

        if (line.startswith('- ') and not diff[diff_pos + 1].startswith('+ ')) \
            or (line.startswith('+ ') and not diff[diff_pos - 1].startswith('- ')):
            continue
        cleaned.append(line)
    diff = cleaned


    
    missing_rtls = []
    for diff_pos in range(len(diff)):
        line = diff[diff_pos].strip()

        if line.endswith('{'): # We are inside a CSS rule.
            if line.startswith('.js'):
                rtl_line = '[dir="rtl"]' + line
            else:
                rtl_line = '[dir="rtl"] ' + line
            
            while diff_pos + 3 < len(diff):
                diff_pos += 1
                rule = diff[diff_pos].strip()
                if '{' in rule:
                    continue;
                if rule.endswith('}'):
                    break;
                
                flipped_rule = diff[diff_pos + 1].strip('+ \n')
                next_line = diff[diff_pos + 2].strip('+ \n')
                
                if rule.startswith('- '): # We have a diff/flipped property
                    # If the rule doesn't have an [dir="rtl"] equivalent, or the
                    # property is not marked as /* LTR */, save an error.
                    if rtl_line not in rtls or next_line != '/* LTR */':
                        missing_rtls.append([line.strip('{ '), rule.strip('- '), flipped_rule])

    # Cleanup
    os.remove(filename + '.nortl')
    os.remove(filename + '.nortl.orig')
    os.remove(filename + '.flipped')

    return missing_rtls

root_path = sys.argv[1]

matches = []
for root, dirnames, filenames in os.walk(root_path):
  for filename in fnmatch.filter(filenames, '*.css'):
      matches.append(os.path.join(root, filename))

output_file = open('missing-rtl.txt', 'w')
for filename in matches:
    if 'test' in filename or 'Test' in filename or 'vendor' in filename:
        continue
    missing_rtls = rtl_check(filename)
    if len(missing_rtls) > 0:
        table = PrettyTable(["Rule", "LTR", "MISSING RTL"])
        table.align = "l"
        output_file.write('==== ' + filename + ' : ' + str(len(missing_rtls)) + ' ERRORS ====\n')
        for missing_rtl in missing_rtls:
            table.add_row(missing_rtl)
        output_file.write('\n' + table.get_string() + '\n\n')

output_file.close()
