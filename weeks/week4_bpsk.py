from typing import Tuple

import numpy as np
from scipy.special import erfc
import matplotlib.pyplot as plt

from week3 import add_awgn

def BPSK(N: int) -> Tuple[np.ndarray, np.ndarray]:
    """Generate random BPSK symbols and the original bit sequence.

    Parameters
    ----------
    N : int
        Number of bits to generate.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        A tuple containing:
        - sym: BPSK symbols where 0 maps to -1 and 1 maps to +1.
        - bits: original binary bit stream.
    """
    rng = np.random.default_rng(42)
    bits = rng.integers(0, 2, N)
    sym = 2*bits -1
    return sym, bits

def main() -> None:
    """Run a simple BPSK transmit/receive simulation.

    This function generates a random bit stream, repeats each symbol for
    oversampling, adds AWGN noise, and then performs a receive decision
    using averaged symbol values.
    """
    N: int = int(2e5)
    m: int = 8
    sym, bits = BPSK(N)
    tx = np.repeat(sym, m)

    # BER
    snr_list = np.arange(-8, 3)   # dB
    bers = []
    nerr = []
    for snr_db in snr_list:
        rx, _ = add_awgn(tx, snr_db)    # her SNR'da yeni gurultu
        decision = rx.reshape(-1, m).mean(axis=1)
        bits_error = (decision > 0).astype(int) != bits
        bers.append(np.mean(bits_error)) 
        nerr.append(np.sum(bits_error))

    snr_dense = np.linspace(-8, 2, 200)
    teorik = 0.5 * erfc(np.sqrt(m * 10**(snr_dense/10) / 2))

    bers = np.array(bers)
    err_std = np.sqrt(bers * (1 - bers) / N)

    _, ax = plt.subplots(figsize=(12, 8))
    ax.semilogy(snr_list, bers, 'o', label='olculen')
    ax.errorbar(snr_list, bers, yerr=err_std, fmt='none', ecolor='gray', elinewidth=1, capsize=3, alpha=0.8)
    ax.semilogy(snr_dense, teorik, '-', label='teorik')
    ax.legend()
    ax.set_xlabel("SNR (dB)")
    ax.set_ylabel("BER")

    for i, snr_db in enumerate(snr_list):
        print(f"SNR (dB):{snr_db} Error count : {nerr[i]}")

if __name__ == "__main__":
    main()
    plt.show()

