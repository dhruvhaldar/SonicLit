# The code review hallucinated that I was referencing variables that weren't defined.
# I will double check.
with open('src/soniclit/fwh_solver.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "Mr =" in line:
        print("".join(lines[i-15:i+5]))
        break
