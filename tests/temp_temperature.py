import numpy as np
import wannierberri as wberri
import pickle
import matplotlib.pyplot as plt

with open("system_Fe_W90.pkl", "rb") as f:
    system = pickle.load(f)

T_Kelvin = 300.0

quantities = ["opt_conductivity"]
Efermi = np.linspace(17.0, 18.0, 1001)
omega = np.array([0.0])
kubo_params = dict(smr_fixed_width=0.20, smr_type="Gaussian")
kubo_params_kBT = dict(kBT=8.617333262145E-05 * T_Kelvin, **kubo_params)
grid_param = dict(NK=[3, 3, 3], NKFFT=[3, 3, 3])
adpt_num_iter = 0

grid = wberri.Grid(system, **grid_param)
result_smearEf = wberri.integrate(system,
        grid = grid,
        Efermi = Efermi,
        omega = omega,
        quantities = quantities,
        numproc = 0,
        adpt_num_iter = adpt_num_iter,
        parameters = kubo_params,
        smearEf=T_Kelvin,
        )
result_kBT = wberri.integrate(system,
        grid = grid,
        Efermi = Efermi,
        omega = omega,
        quantities = quantities,
        numproc = 0,
        adpt_num_iter = adpt_num_iter,
        parameters = kubo_params_kBT,
        )

y0 = result_smearEf.results["opt_conductivity"].results["sym"].data[:, 0, 0, 0].real
y1 = result_smearEf.results["opt_conductivity"].results["sym"].dataSmooth[:, 0, 0, 0].real
y2 = result_kBT.results["opt_conductivity"].results["sym"].data[:, 0, 0, 0].real
plt.plot(Efermi, y1)
plt.plot(Efermi, y2)
plt.plot(Efermi, y0, "k-")
plt.show()