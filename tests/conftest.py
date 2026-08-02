"""Shared fixtures for DSP unit tests.

This module provides reusable test fixtures for the DSP package, including
sample rate constants and a deterministic sine wave generator used across
multiple test modules.
"""

import pytest
import numpy as np
from dsp.signals import sine_wave
from helpers import FS, FC

@pytest.fixture
def test_sinyali():
    """Create a deterministic 1 kHz sine wave sampled at 50 kHz.

    Returns a NumPy array containing a 0.1 second sinusoid used by
    multiple tests to validate DSP resampling and filtering behavior.
    """
    return sine_wave(FC, 0.1, FS)

@pytest.fixture
def rng():
    """Provide a reproducible pseudorandom number generator.

    This fixture returns a NumPy Generator seeded with a fixed value so tests
    that require random input remain deterministic.
    """
    return np.random.default_rng(42)
