"""Test the Data_K object."""

import numpy as np
import pytest
from pytest import approx

import wannierberri as wberri
from wannierberri.__Kpoint import KpointBZ
from wannierberri.__Data_K import Data_K

from create_system import create_files_Fe_W90, system_Fe_W90


def test_fourier(system_Fe_W90):
    """Compare slow FT and FFT."""
    system = system_Fe_W90

    k = np.array([0.1, 0.2, -0.3])

    grid = wberri.Grid(system, NKFFT=[4, 3, 2], NKdiv=1)

    dK = 1. / grid.div
    NKFFT = grid.FFT
    factor = 1./np.prod(grid.div)

    kpoint = KpointBZ(K=k, dK=dK, NKFFT=NKFFT, factor=factor, symgroup=None)

    assert kpoint.Kp_fullBZ == approx(k / grid.FFT)

    data_fftw  = Data_K(system, kpoint.Kp_fullBZ, grid=grid, Kpoint=kpoint, npar=0, fftlib='fftw')
    data_slow  = Data_K(system, kpoint.Kp_fullBZ, grid=grid, Kpoint=kpoint, npar=0, fftlib='slow')
    data_numpy = Data_K(system, kpoint.Kp_fullBZ, grid=grid, Kpoint=kpoint, npar=0, fftlib='numpy')

    test_fields = ["E_K", "D_H", "V_H", "shc_B_H"]

    for field in test_fields:
        assert getattr(data_fftw,  field) == approx(getattr(data_slow, field)), "fftw  does not match slow for {} ".format(field)
        assert getattr(data_numpy, field) == approx(getattr(data_slow, field)), "numpy does not match slow for {}".format(field)
        assert getattr(data_numpy, field) == approx(getattr(data_slow, field)), "numpy does not match fftw for {}".format(field)

    # TODO: Allow gauge degree of freedom



