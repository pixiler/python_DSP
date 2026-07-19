import numpy as np
import matplotlib.pyplot as plt
from matlab_example import sine_wave, plot_spectrum, plot_signal


def add_awgn(signal: np.ndarray, snr_db: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Additive White Gaussian Noise (AWGN) to a signal.

    Parameters:
    signal (np.ndarray): Input signal.
    snr_db (float): Desired Signal-to-Noise Ratio in dB.

    Returns:
    np.ndarray: Noisy signal.
    np.ndarray: Generated noise.

    """
    # Calculate signal power and convert SNR from dB
    signal_power = np.mean(signal ** 2)
    snr_linear = 10 ** (snr_db / 10)

    # Calculate noise power
    noise_power = signal_power / snr_linear

    # Generate white Gaussian noise
    noise = np.random.normal(0, np.sqrt(noise_power), signal.shape)

    # Add noise to the original signal
    noisy_signal = signal + noise
    return noisy_signal, noise

def plot_stem(axes: plt.Axes, signal : np.ndarray, length: int, title: str = None) -> None:

    axes.stem(signal[:length])
    axes.set_title(title)

def main() -> None:
    fc: float = 1e3  # Carrier frequency in Hz
    Fs: int = 50e3  # Sampling frequency in Hz
    t: float = 0.1  # Duration in seconds

    y = sine_wave(fc, t, Fs)
    snr_db: float = 10  # Desired SNR in dB
    noisy_signal, noise = add_awgn(y, snr_db)
    print(f"Desired SNR (linear): {10 ** (snr_db / 10)}")
    print(f"noise power: {np.mean(noise ** 2)}")
    print(f"Actual SNR (dB): {10 * np.log10(np.mean(y ** 2) / np.mean(noise ** 2))}")

    plt.figure(figsize=(12, 6))
    plot_signal(plt.gca(), y, Fs, fc, 1)
    plot_signal(plt.gca(), noisy_signal, Fs, fc, 1)
    plt.show()

    fig, ax = plt.subplots(2, 1, figsize=(12, 8))
    plot_spectrum(ax[0], y, Fs, label="Original Signal Spectrum")
    plot_spectrum(ax[1], noisy_signal, Fs, label="Noisy Signal Spectrum")
    plt.show()

    fig, ax = plt.subplots(3, 1, figsize=(12, 8))
   
    for i, snr_db in enumerate([0, 10, 20]): 
        noisy_signal, noise = add_awgn(y, snr_db)
        plot_stem(ax[i],noisy_signal, 30, title = f"SNR = {snr_db} dB")
        
    plt.show()

    fig, ax = plt.subplots(2, 1, figsize=(12, 8))
    plot_spectrum(ax[0], y, Fs, label="Original Signal Spectrum", xscale='log')
    plot_spectrum(ax[1], noisy_signal, Fs, label="Noisy Signal Spectrum", xscale='log')
    plt.show()

    noisy_signal, noise = add_awgn(y, 0)
    plt.figure(figsize=(12, 6))
    plot_spectrum(plt.gca(), noisy_signal, Fs, label="Noisy Signal Spectrum in 0 db SNR", xscale='log')
    plt.show()

if __name__ == "__main__":
    main()




