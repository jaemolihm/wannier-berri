"""Test the anomalous Hall conductivity."""

import numpy as np
import pytest
from pytest import approx

import wannierberri as wberri

from create_system import create_files_Fe_W90,  create_files_GaAs_W90,  system_Fe_W90, system_Fe_W90_wcc,system_GaAs_W90 ,system_GaAs_W90_wcc
from compare_result import compare_energyresult

def check_integrate(system,quantities,fout_name,Efermi,comparer,numproc=0,grid_param={'NK':[6,6,6],'NKFFT':[3,3,3]},additional_parameters={},adpt_num_iter=1,suffix="",precision=1e-10,extra_precision={}):
    grid = wberri.Grid(system, **grid_param)
    result = wberri.integrate(system,
            grid = grid,
            Efermi = Efermi,
#            omega = omega,
            quantities = quantities,
            numproc = numproc,
            adpt_num_iter = adpt_num_iter,
            parameters = additional_parameters,
            fout_name = fout_name,
            suffix=suffix,
            restart = False,
            )
    if len(suffix)>0:
        suffix="-"+suffix

    for quant in quantities:
        data=result.results.get(quant).data
        assert data.shape[0] == len(Efermi)
        assert np.all( np.array(data.shape[1:]) == 3)
        prec=extra_precision[quant] if quant in extra_precision else precision
        comparer(fout_name, quant+suffix,  adpt_num_iter , suffix_ref=compare_quant(quant) ,precision=prec )


@pytest.fixture(scope="module")
def Efermi_Fe():
    return np.linspace(17,18,11)


@pytest.fixture(scope="module")
def Efermi_GaAs():
    return np.linspace(7,9,11)


@pytest.fixture(scope="module")
def quantities_Fe():
    return  ['ahc','ahc_ocean','dos','cumdos'  ,'conductivity_ohmic','conductivity_ohmic_fsurf']


@pytest.fixture(scope="module")
def quantities_GaAs():
    return  ["berry_dipole","berry_dipole_ocean","berry_dipole_fsurf"]


def compare_quant(quant):
    compare= {'ahc_ocean':'ahc',"berry_dipole_ocean":"berry_dipole"}
    if quant in compare:
        return compare[quant]
    else:
        return quant



def test_Fe(system_Fe_W90, compare_energyresult,quantities_Fe,Efermi_Fe):
    """Test anomalous Hall conductivity , ohmic conductivity, dos, cumdos"""
    check_integrate(system_Fe_W90 , quantities_Fe , fout_name="berry_Fe_W90" , suffix="" , Efermi=Efermi_Fe , comparer=compare_energyresult )


def test_Fe_wcc(system_Fe_W90_wcc, compare_energyresult,quantities_Fe,Efermi_Fe):
    """Test anomalous Hall conductivity , ohmic conductivity, dos, cumdos"""
    check_integrate(system_Fe_W90_wcc , quantities_Fe , fout_name="berry_Fe_W90" , suffix="wcc" , Efermi=Efermi_Fe , comparer=compare_energyresult )


def test_GaAs(system_GaAs_W90, compare_energyresult,quantities_GaAs,Efermi_GaAs):
    """Test berry dipole"""
    check_integrate(system_GaAs_W90 , quantities_GaAs , fout_name="berry_GaAs_W90" , suffix="" , Efermi=Efermi_GaAs , comparer=compare_energyresult ,
                  extra_precision = {"berry_dipole_fsurf":1e-6} )   # This is a low precision for the nonabelian thing, not sure if it does not indicate a problem, or is a gauge-dependent thing

def test_GaAs_wcc(system_GaAs_W90_wcc, compare_energyresult,quantities_GaAs,Efermi_GaAs):
    """Test berry dipole with wcc_phase"""
    check_integrate(system_GaAs_W90_wcc , quantities_GaAs , fout_name="berry_GaAs_W90" , suffix="wcc" , Efermi=Efermi_GaAs , comparer=compare_energyresult ,
                  precision=1e-10 ,extra_precision = {"berry_dipole_fsurf":1e-6} )   # This is a low precision for the nonabelian thing, not sure if it does not indicate a problem
