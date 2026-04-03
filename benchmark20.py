import numpy as np
import timeit

N = 1000000
p = np.random.rand(N)
inv_R = np.random.rand(N)
inv_one_minus_Mr_sq = np.random.rand(N)
inv_one_minus_Mr = np.random.rand(N)
Mr0_inv_R = np.random.rand(N)

inv_4pi = 1.0 / (4.0 * np.pi)
speed_of_sound = 340.0
inv_speed_of_sound = 1.0/speed_of_sound

def f1():
    factor_pt1_scaled = p * inv_R * inv_one_minus_Mr_sq * inv_4pi
    factor_pq1_scaled = factor_pt1_scaled * inv_speed_of_sound
    factor_pq2_scaled = factor_pt1_scaled * inv_R
    factor_pt2_scaled = factor_pq2_scaled * (-Mr0_inv_R) * inv_one_minus_Mr * speed_of_sound
    factor_pq3_scaled = factor_pt2_scaled * inv_speed_of_sound
    return factor_pt1_scaled, factor_pt2_scaled, factor_pq1_scaled, factor_pq2_scaled, factor_pq3_scaled

def f2():
    factor_pt1_scaled = p * inv_R * inv_one_minus_Mr_sq * inv_4pi
    factor_pq1_scaled = factor_pt1_scaled * inv_speed_of_sound
    factor_pq2_scaled = factor_pt1_scaled * inv_R
    factor_pq3_scaled = factor_pq2_scaled * (-Mr0_inv_R) * inv_one_minus_Mr
    factor_pt2_scaled = factor_pq3_scaled * speed_of_sound
    return factor_pt1_scaled, factor_pt2_scaled, factor_pq1_scaled, factor_pq2_scaled, factor_pq3_scaled

print("f1:", timeit.timeit(f1, number=100))
print("f2:", timeit.timeit(f2, number=100))
