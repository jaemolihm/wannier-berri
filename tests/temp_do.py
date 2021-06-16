import numpy as np
import wannierberri as wberri
import pickle
import matplotlib.pyplot as plt

seedname = "data/GaAs_Wannier90/GaAs"
try:
    with open("system.pkl", "rb") as f:
        system = pickle.load(f)
except Exception as e:
    system = wberri.System_w90(seedname, berry=True, SHCqiao=True, SHCryoo=True, use_wcc_phase=False)
    with open("system.pkl", "wb") as f:
        pickle.dump(system, f)

try:
    with open("system_wcc.pkl", "rb") as f:
        system_wcc = pickle.load(f)
except Exception as e:
    system_wcc = wberri.System_w90(seedname, berry=True, SHCqiao=True, SHCryoo=True, use_wcc_phase=True)
    with open("system_wcc.pkl", "wb") as f:
        pickle.dump(system_wcc, f)

quantities = ["opt_SHCqiao", "opt_SHCryoo"]

# Efermi = np.array([7.0, 8.0])
# omega = np.arange(0.0, 7.1, 1.0)
Efermi = np.array([7.0])
# omega = np.array([0.0])
omega = np.linspace(0., 2., 101)
kubo_params = dict(smr_fixed_width=0.20, smr_type="Gaussian")
# grid_param = dict(NK=[3, 3, 3], NKFFT=[3, 3, 3])
grid_param = dict(NK=[1, 1, 3], NKFFT=[1, 1, 3])
adpt_num_iter = 0

grid = wberri.Grid(system, **grid_param)
result = wberri.integrate(system,
        grid = grid,
        Efermi = Efermi,
        omega = omega,
        quantities = quantities,
        adpt_num_iter = adpt_num_iter,
        parameters = kubo_params,
        restart = False,
    )

result_wcc = wberri.integrate(system_wcc,
        grid = grid,
        Efermi = Efermi,
        omega = omega,
        quantities = quantities,
        adpt_num_iter = adpt_num_iter,
        parameters = kubo_params,
        restart = False,
    )

plt.plot(omega, result.results["opt_SHCryoo"].data[0, :, 0, 1, 2])
plt.plot(omega, result_wcc.results["opt_SHCryoo"].data[0, :, 0, 1, 2])
plt.plot(omega, result_wcc.results["opt_SHCryoo"].data[0, :, 0, 1, 2] - result.results["opt_SHCryoo"].data[0, :, 0, 1, 2])
plt.axhline(0, c='k')
# plt.show()