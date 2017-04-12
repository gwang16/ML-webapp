import subprocess


command = 'Rscript'
script = 'Rtest.R'
args = ['']
cmd = [command, script] + args
x = subprocess.check_output(cmd, universal_newlines = True)

print(type(x))