import numpy as np
from dsp.filters import fir1, apply_filter, apply_filtfilt
from dsp.analysis import measure_delay
from dsp.signals import sine_wave
from helpers import rms, FS, FC 
import pytest 

def test_fir1_cift_dereceden_tek_sayida_katsayi_dondurur():
    h = fir1(64, 0.08)
    assert len(h) == 65

def test_apply_filter_cikis_uzunlugu_girise_esit(test_sinyali):
    h = fir1(64, 0.08)
    y = apply_filter(test_sinyali,h)
    assert len(y) == len(test_sinyali)

def test_group_delay_equal_tapin_bir_eksiginin_yarisidir(test_sinyali):
    
    h = fir1(64, 0.08)
    y = apply_filter(test_sinyali,h)
    assert measure_delay(y, test_sinyali, Fs=FS, fc=FC) == (len(h) - 1) / 2

def test_bant_disi_ton_en_az_40dB_bastirilir():
    s = sine_wave(10e3, 0.1, FS)
    h = fir1(64, 2e3/(FS/2))
    y = apply_filter(s, h)
    zayiflatma_db = 20 * np.log10(rms(y[100:]) / rms(s[100:]))
    assert zayiflatma_db <= -40

def test_bant_ici_ton_en_fazla_1dB_kaybeder():
    s = sine_wave(1e3, 0.1, FS)
    h = fir1(64, 2e3/(FS/2))
    y = apply_filter(s, h)
    zayiflatma_db = 20 * np.log10(rms(y[100:]) / rms(s[100:]))
    assert zayiflatma_db >= -1

def test_filtfilt_group_delay_zero(test_sinyali):
    h = fir1(64, 2e3/(FS/2))
    y = apply_filtfilt(test_sinyali, h)
    assert measure_delay(y, test_sinyali, Fs=FS, fc=FC) == 0

@pytest.mark.parametrize("Wn", [1.5, 1.0, 0.0, -0.2])
def test_fir1_gecersiz_Wn_icin_hata_verir(Wn):
    with pytest.raises(ValueError, match="Invalid cutoff frequency"):
        fir1(64, Wn)
