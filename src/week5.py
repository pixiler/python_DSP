import numpy as np
from week3 import add_awgn
from matlab_example import sine_wave

y = sine_wave(1e3, 0.001, 50e3)

np.random.seed(42)
n1 = add_awgn(y, 10)[1]

np.random.seed(42)
n2 = add_awgn(y, 10)[1]

print(np.array_equal(n1, n2))