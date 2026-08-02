import numpy as np
import pytest
from dsp.signals import sine_wave
from dsp.resampling import interpolate, up_sample, decimate
from helpers import rms, FS, FC

def test_interpolate_genligi_sinyal_uzunlugundan_bagimsiz():
    kisa = sine_wave(FC, 0.01, FS)
    uzun = sine_wave(FC, 0.1, FS)

    r_kisa = interpolate(kisa, FS, 2)
    r_uzun = interpolate(uzun, FS, 2)

    assert rms(r_kisa.signal[r_kisa.group_delay:]) == pytest.approx(
        rms(r_uzun.signal[r_uzun.group_delay:]), rel=0.01
    )

@pytest.mark.parametrize("factor", [2, 3, 4])

def test_up_sample_uzunlugu_factor_kati(test_sinyali, factor):
    assert len(up_sample(test_sinyali, factor)) == factor * len(test_sinyali)

@pytest.mark.parametrize("factor", [2, 3, 4])
def test_up_sample_ara_indisler_sifir(test_sinyali, factor):
    y = up_sample(test_sinyali, factor)
    mask = np.ones(len(y), dtype=bool)
    mask[::factor] = False
    assert np.all(y[mask] == 0)

def test_up_sample_orijinal_ornekleri_korur(test_sinyali):
    y = up_sample(test_sinyali, 2)
    np.testing.assert_array_equal(y[::2], test_sinyali)

@pytest.mark.parametrize("factor",[2, 3, 4])
def test_decimate_uzunlugu_sinyalin_uzunlugunun_K_orani(test_sinyali, factor):
    s, _ , _ = decimate(test_sinyali, Fs=FS, factor=factor)
    beklenen = int(np.ceil(len(test_sinyali) / factor))
    assert len(s) == beklenen

