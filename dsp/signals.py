import numpy as np

def sine_wave(frequency: float, duration: float, sample_rate: int) -> np.ndarray:
    """
    Generates a sine wave signal.

    Args:
        frequency (float): Frequency of the sine wave in Hz.
        duration (float): Duration of the signal in seconds.
        sample_rate (int): Sampling rate in samples per second.

    Returns:
        np.ndarray: An array containing the generated sine wave samples.
    """
    
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.sin(2 * np.pi * frequency * t)

def add_awgn(signal: np.ndarray, snr_db: float, rng=None) -> tuple[np.ndarray, np.ndarray]:
    """
    Add additive white Gaussian noise (AWGN) to a signal.

    Parameters:
        signal (np.ndarray): Input signal.
        snr_db (float): Desired signal-to-noise ratio in dB.
        rng (np.random.Generator, optional): Random number generator for noise.
            If None, a default generator is created.

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing the noisy signal and
            the generated noise vector.

    """

    if rng is None:
        rng = np.random.default_rng()

    # Calculate signal power and convert SNR from dB
    signal_power = np.mean(signal ** 2)
    snr_linear = 10 ** (snr_db / 10)

    # Calculate noise power
    noise_power = signal_power / snr_linear

    # Generate white Gaussian noise
    noise = rng.normal(0, np.sqrt(noise_power), signal.shape)

    # Add noise to the original signal
    return signal + noise, noise