import numpy as np
import matplotlib.pyplot as plt

from .analysis import fft, find_cutoff
from .filters import frequency_response

def plot_signal(axes: plt.Axes, signal: np.ndarray, sample_rate: int, frequency: float, nSines: int = 1, label: str = None) -> None:
    """
    Plots the given signal.

    Args:
        axes (plt.Axes): The axes on which to plot the signal.
        signal (np.ndarray): The signal to be plotted.
        sample_rate (int): Sampling rate in samples per second.
        frequency (float): Frequency of the sine wave in Hz.
        nSines (int, optional): The number of sine waves to display.
        label (str, optional): The label for the plot. 
    """
    t = np.arange(len(signal)) / sample_rate
    axes.plot(t, signal, '.-', label=label)
    axes.legend()
    axes.set_xlim(0, nSines/frequency)  # Show one period of the sine wave
    axes.set_title(f"Sine Wave Signal ({frequency} Hz)")
    axes.set_xlabel("Time [s]")
    axes.set_ylabel("Amplitude")
    axes.grid()

def plot_spectrum(axes: plt.Axes, signal: np.ndarray, sample_rate: int, label: str = None, xscale: str = 'linear') -> None:
    """
    Plots the magnitude spectrum of a signal.

    Args:
        axes (plt.Axes): The axes on which to plot the spectrum.
        signal (np.ndarray): The input signal.
        sample_rate (int): The sampling rate in samples per second.
        label (str, optional): The label for the plot.
        xscale (str, optional): xscale for the plot.
    """
    fft_values, f = fft(signal, sample_rate)
    magnitude = np.abs(fft_values)

    if xscale == 'log':
        axes.plot(f[len(f)//2+1:], magnitude[len(magnitude)//2+1:], label = label)
    else :
        axes.plot(f, magnitude, label = label)
    
    axes.legend()
    axes.set_title("Magnitude Spectrum")
    axes.set_xlabel("Frequency [Hz]")
    axes.set_ylabel("Magnitude")
    axes.set_xscale(xscale)
    
    axes.grid()

def plot_frequency_response(axes: plt.Axes, b: np.ndarray, a=1.0, worN=1024, fs=2.0, level_db : float = -6.0, label: str = None) -> None:
    """Plot the filter frequency response and mark the cutoff frequency.

    Args:
        axes (plt.Axes): The axes on which to plot the response.
        b (np.ndarray): Numerator filter coefficients.
        a (np.ndarray | float): Denominator filter coefficients, or 1.0 for an FIR filter.
        worN (int): Number of frequency points to compute.
        fs (float): Sampling frequency.
        label (str, optional): Plot label.
    """
    w, h = frequency_response(b, a=a, worN=worN, fs=fs)
    f_c = find_cutoff(w, h, level_db)

    mag_db = 20 * np.log10(np.abs(h))

    # Kesim bulunduysa label'a ekle, bulunamadiysa label oldugu gibi kalsin
    if f_c is not None and label is not None:
        label = f"{label} (f_c = {f_c:.0f} Hz)"
        
    line, = axes.plot(w, mag_db, label=f'{label}')
    if f_c is not None:
        axes.axvline(f_c, color=line.get_color(), linestyle='--', alpha=0.3)
        axes.plot(f_c, level_db, 'ro')  # Mark the cutoff frequency point
    axes.set_xlabel("Frequency [Hz]")
    axes.set_ylabel("Magnitude [dB]")
    axes.grid(True)
    axes.legend()
