import re

with open('src/soniclit/fwh_solver.py', 'r') as f:
    content = f.read()

# Let's fix the d0, d1, d2, M2, geom_n_dot_mach in stationary_serial
# Wait, let's actually read fwh_solver.py to see if d0, d1, d2 were already there.
