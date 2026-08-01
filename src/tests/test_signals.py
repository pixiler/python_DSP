import numpy as np
import pytest

from helpers import rms
from dsp.signals import add_awgn
from dsp.analysis import snr_calculate


def test_sine_wave_genligi(test_sinyali):
    assert rms(test_sinyali) == pytest.approx(1/np.sqrt(2), rel=1e-3)
    assert np.max(np.abs(test_sinyali)) <= 1.0

@pytest.mark.parametrize("snr_db", [0.0, 10.0, 20.0])
def test_add_awgn_olculen_snr_hedefe_yakin(test_sinyali, rng, snr_db):
    _, noise = add_awgn(test_sinyali, snr_db=snr_db, rng=rng)
    olculen = snr_calculate(test_sinyali, noise)
    # Tolerans: sonlu ornekleme sapmasi ~0.09 dB (sqrt(2/N)), 5x pay birakildi
    assert olculen == pytest.approx(snr_db, abs=0.5)

def test_add_awgn_sifir_db_de_gurultu_gucu_sinyale_esit(test_sinyali, rng):
    _, noise = add_awgn(test_sinyali, snr_db=0.0, rng=rng)
    assert np.mean(noise**2) == pytest.approx(np.mean(test_sinyali**2), rel=0.05)

def test_add_awgn_rng_verilmezse_her_cagri_farkli(test_sinyali):
    _, n1 = add_awgn(test_sinyali, 10.0)
    _, n2 = add_awgn(test_sinyali, 10.0)
    assert not np.array_equal(n1, n2)