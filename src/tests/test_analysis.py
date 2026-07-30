
import pytest
import numpy as np
from dsp.analysis import fft
from helpers import FS, FC

def test_fft_tepesi_dogru_binde(test_sinyali):
    Y, f = fft(test_sinyali, FS)
    mag = np.abs(Y)
    pozitif = f >= 0
    delta_f = FS / len(test_sinyali)
    assert f[pozitif][np.argmax(mag[pozitif])] == pytest.approx(FC, abs=delta_f/2)
    

def test_fft_tepe_genligi_yarim(test_sinyali):
    Y, _ = fft(test_sinyali, FS)
    assert np.max(np.abs(Y)) == pytest.approx(0.5, rel=0.01)

def test_parseval_zaman_ve_frekans_gucu_esit(test_sinyali):
    Y, _ = fft(test_sinyali, FS)
    pwr_time = np.mean(test_sinyali**2)
    pwr_freq = np.sum(np.abs(Y)**2)
    assert pwr_time == pytest.approx(pwr_freq, rel=1e-9)
