with open('src/soniclit/fwh_solver.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "def _calculate_source_terms_local(" in line:
        start = i
        break

print("".join(lines[start:start+75]))
