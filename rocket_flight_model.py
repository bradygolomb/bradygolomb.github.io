"""
BOTTLE ROCKET FLIGHT MODEL + INVERSE SOLVER     (Penn MEAM 2480, Spring 2026)
Brady Golomb, Chris Inglis, Hussein Elzaafarany

Two-phase (thrust, then ballistic) flight model for a 2 L water + butane rocket,
calibrated to launch data, plus an inverse solver that picks the launch angle and
butane charge to pass through a wall gap and land at a target distance.
Requires numpy, scipy, matplotlib. Edit SECTION 10 at the bottom and run.
"""

# ══════════════════════════════════════════════════════════════════════════════
# LAB 4 ROCKET MODEL
# Fixed Lab 3 coefficients + new alpha calibration from 6 butane trials
# ══════════════════════════════════════════════════════════════════════════════

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar, minimize

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — PHYSICAL CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
G        = 9.81          # m/s^2
RHO_AIR  = 1.20          # kg/m^3
RHO_W    = 1000.0        # kg/m^3
R_GAS    = 8.314         # J/(mol K)
M_BUT    = 0.05812       # kg/mol, n-butane
P_ATM    = 101_325.0     # Pa

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — ROCKET GEOMETRY AND FIXED TEST CONDITIONS
# ─────────────────────────────────────────────────────────────────────────────
V_BOTTLE = 2.0e-3        # m^3, 2 L bottle
R_BOTTLE = 0.055         # m, approximate bottle body radius
A_BODY   = np.pi * R_BOTTLE**2

VOL_ML   = 500.0         # mL water
T_WATER  = 22.3          # deg C
M_DRY    = 0.298         # kg, new dry rocket mass

# IMPORTANT FIX:
# The physical nozzle diameter is known to be 21 mm, so the radius is fixed.
D_NOZ    = 0.0210        # m
R_NOZ    = D_NOZ / 2     # 0.0105 m
A_NOZ    = np.pi * R_NOZ**2

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — INHERITED COEFFICIENTS FROM LAB 3
# Do not fit these in Lab 4. Only alpha is re-fit from the 6 new trials.
# Replace these with your exact Lab 3 printed values if needed.
# ─────────────────────────────────────────────────────────────────────────────
CD_NOZ   = 0.3792        # nozzle discharge coefficient from Lab 3
CD_AERO  = 1.3406        # aerodynamic drag coefficient from Lab 3

# This is calibrated below from the 6 new Lab 4 trials.
ALPHA    = 1.0

print("Fixed nozzle diameter:", D_NOZ * 1000, "mm")
print("Fixed nozzle radius:", R_NOZ * 1000, "mm")
print("Fixed nozzle area:", A_NOZ, "m^2")
print("Inherited CD_NOZ:", CD_NOZ)
print("Inherited CD_AERO:", CD_AERO)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — BUTANE SATURATION PRESSURE
# ══════════════════════════════════════════════════════════════════════════════

def butane_sat_pressure(T_K: float) -> float:
    """
    Antoine equation for n-butane. Returns saturation pressure in Pa.
    T_K is absolute temperature in K.
    """
    A, B, C = 4.35576, 1175.581, -2.071
    return 10 ** (A - B / (T_K + C)) * 1e5


def saturated_gas_mass(p_sat: float, V_gas: float, T_K: float) -> float:
    """
    Gas mass required to fill V_gas at saturation pressure p_sat.
    """
    return p_sat * V_gas * M_BUT / (R_GAS * T_K)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — FORWARD SIMULATOR
# ══════════════════════════════════════════════════════════════════════════════

def simulate(
        angle_deg : float,
        m_butane  : float,          # kg, EFFECTIVE butane mass after alpha
        vol_mL    : float = VOL_ML,
        T_water_C : float = T_WATER,
        cd_noz    : float = CD_NOZ,
        cd_aero   : float = CD_AERO,
        m_dry     : float = M_DRY,
        dt        : float = 0.001,
        max_steps : int   = 1_200_000,
) -> dict:
    """
    Simulate one launch.

    m_butane is the EFFECTIVE butane mass in kg.
    Use m_butane = ALPHA * measured_butane_g / 1000.

    Key improvement from the old version:
    - The nozzle radius is fixed from the 21 mm diameter.
    - Butane is modeled as saturated vapor while liquid butane remains.
      As the water leaves and gas volume increases, liquid butane evaporates
      to keep the gas near saturation pressure until liquid butane runs out.
    """
    theta = np.radians(angle_deg)
    T_K   = T_water_C + 273.15
    p_sat = butane_sat_pressure(T_K)

    # Initial water and gas volumes
    m_w = vol_mL * 1e-6 * RHO_W
    V_g = V_BOTTLE - m_w / RHO_W

    # Initial butane split: gas up to saturation, rest liquid.
    mg_sat = saturated_gas_mass(p_sat, V_g, T_K)
    mg = min(m_butane, mg_sat)
    mb_liq = max(m_butane - mg, 0.0)

    # Initial state
    x, y = 0.0, 0.0
    vx, vy = 0.0, 0.0
    t = 0.0
    max_y = 0.0
    burnout_t = 0.0
    burnout_v = 0.0
    phase = "thrust"

    traj_x = [0.0]
    traj_y = [0.0]

    for step in range(max_steps):
        t += dt

        if phase == "thrust":
            V_g = max(V_BOTTLE - m_w / RHO_W, 1e-12)

            # If liquid butane is still present, keep vapor at saturation
            # as much as possible by evaporating liquid into the growing gas volume.
            if mb_liq > 0:
                mg_needed = saturated_gas_mass(p_sat, V_g, T_K)
                dm_evap = max(mg_needed - mg, 0.0)
                dm_evap = min(dm_evap, mb_liq)
                mg += dm_evap
                mb_liq -= dm_evap

            # Pressure from current butane vapor mass.
            p = mg * R_GAS * T_K / (M_BUT * V_g)

            if p <= P_ATM or m_w <= 1e-6:
                phase = "ballistic"
                burnout_t = t
                burnout_v = np.hypot(vx, vy)
                continue

            dp = p - P_ATM

            # Water mass flow rate through fixed 21 mm diameter nozzle.
            mdot_w = cd_noz * A_NOZ * np.sqrt(2.0 * RHO_W * dp)

            # Exhaust velocity and thrust.
            ve = np.sqrt(2.0 * dp / RHO_W)
            thrust = mdot_w * ve + dp * A_NOZ

            m_tot = m_dry + m_w + mg + mb_liq

            v = np.hypot(vx, vy)
            if v > 1e-9:
                Fd = 0.5 * RHO_AIR * cd_aero * A_BODY * v**2
                Fd_x = -Fd * vx / v
                Fd_y = -Fd * vy / v
            else:
                Fd_x = 0.0
                Fd_y = 0.0

            ax = (thrust * np.cos(theta) + Fd_x) / m_tot
            ay = (thrust * np.sin(theta) + Fd_y) / m_tot - G

            vx += ax * dt
            vy += ay * dt
            x  += vx * dt
            y  += vy * dt

            m_w = max(m_w - mdot_w * dt, 0.0)

        else:
            # Ballistic phase: no water thrust.
            m_tot = m_dry + mg + mb_liq

            v = np.hypot(vx, vy)
            if v > 1e-9:
                Fd = 0.5 * RHO_AIR * cd_aero * A_BODY * v**2
                Fd_x = -Fd * vx / v
                Fd_y = -Fd * vy / v
            else:
                Fd_x = 0.0
                Fd_y = 0.0

            ax = Fd_x / m_tot
            ay = Fd_y / m_tot - G

            vx += ax * dt
            vy += ay * dt
            x  += vx * dt
            y  += vy * dt

        max_y = max(max_y, y)

        if step % 10 == 0:
            traj_x.append(x)
            traj_y.append(max(y, 0.0))

        if y < 0 and phase == "ballistic" and t > 0.05:
            break

    return {
        "range_m": max(x, 0.0),
        "tof_s": t,
        "max_height_m": max_y,
        "burnout_v": burnout_v,
        "burnout_t": burnout_t,
        "traj_x": np.array(traj_x),
        "traj_y": np.array(traj_y),
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — NEW LAB 4 CALIBRATION DATA
# ══════════════════════════════════════════════════════════════════════════════

# All 6 trials are at approximately the same angle, water volume, and temperature.
# Columns:
#   angle_deg, vol_mL, T_C, measured butane charge in grams, measured range, measured time of flight

CALIB_DATA = [
    dict(angle_deg=47, vol_mL=500, T_C=22.5, butane_g=16, range_m=27.6, tof_s=2.51),
    dict(angle_deg=47, vol_mL=500, T_C=22.4, butane_g= 8, range_m=14.9, tof_s=2.04),
    dict(angle_deg=47, vol_mL=500, T_C=22.3, butane_g= 5, range_m= 8.1, tof_s=1.52),
    dict(angle_deg=47, vol_mL=500, T_C=22.3, butane_g=26, range_m=32.5, tof_s=3.15),
    dict(angle_deg=47, vol_mL=500, T_C=23.0, butane_g=12, range_m=23.2, tof_s=2.65),
    dict(angle_deg=47, vol_mL=500, T_C=23.3, butane_g= 3, range_m= 4.3, tof_s=1.28),
]


def calibrate_alpha(data=CALIB_DATA, bounds=(0.05, 5.0), verbose=True):
    """
    Calibrate only alpha.

    CD_NOZ, CD_AERO, and R_NOZ are fixed.
    Alpha scales the measured butane mass:

        m_butane_effective = alpha * measured_butane_mass

    The loss compares both range and time of flight using normalized errors.
    """
    mean_range = np.mean([d["range_m"] for d in data])
    mean_tof   = np.mean([d["tof_s"]   for d in data])

    def loss(alpha):
        if alpha <= 0:
            return 1e12

        range_errs = []
        tof_errs = []

        for d in data:
            mb_eff = alpha * d["butane_g"] * 1e-3
            res = simulate(
                angle_deg=d["angle_deg"],
                m_butane=mb_eff,
                vol_mL=d["vol_mL"],
                T_water_C=d["T_C"],
            )

            range_errs.append(abs(res["range_m"] - d["range_m"]) / mean_range)
            tof_errs.append(abs(res["tof_s"] - d["tof_s"]) / mean_tof)

        return np.mean(range_errs) + np.mean(tof_errs)

    opt = minimize_scalar(loss, bounds=bounds, method="bounded", options={"xatol": 1e-5})
    alpha = float(opt.x)

    if verbose:
        print("=" * 72)
        print("ALPHA CALIBRATION")
        print("=" * 72)
        print(f"Fixed CD_NOZ  = {CD_NOZ:.5f}")
        print(f"Fixed CD_AERO = {CD_AERO:.5f}")
        print(f"Fixed D_NOZ   = {D_NOZ*1000:.2f} mm")
        print(f"Best alpha    = {alpha:.5f}")
        print(f"Loss          = {opt.fun:.5f}")
        print()
        print_calibration_table(data, alpha)

    return alpha


def print_calibration_table(data=CALIB_DATA, alpha=1.0):
    print(f"{'Butane':>8} | {'Pred Range':>11} {'Meas Range':>11} {'Err':>9} | {'Pred ToF':>9} {'Meas ToF':>9} {'Err':>8}")
    print("-" * 86)

    range_abs = []
    tof_abs = []

    for d in data:
        mb_eff = alpha * d["butane_g"] * 1e-3
        res = simulate(d["angle_deg"], mb_eff, d["vol_mL"], d["T_C"])

        r_err = res["range_m"] - d["range_m"]
        t_err = res["tof_s"] - d["tof_s"]

        range_abs.append(abs(r_err))
        tof_abs.append(abs(t_err))

        print(
            f"{d['butane_g']:>7.1f}g | "
            f"{res['range_m']:>10.2f}m {d['range_m']:>10.2f}m {r_err:>+8.2f}m | "
            f"{res['tof_s']:>8.2f}s {d['tof_s']:>8.2f}s {t_err:>+7.2f}s"
        )

    print("-" * 86)
    print(f"Range MAE = {np.mean(range_abs):.3f} m")
    print(f"ToF MAE   = {np.mean(tof_abs):.3f} s")


# Run calibration once.
ALPHA = calibrate_alpha()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — PLOT CALIBRATION TRAJECTORIES
# ══════════════════════════════════════════════════════════════════════════════

def plot_calibration(data=CALIB_DATA, alpha=None):
    if alpha is None:
        alpha = ALPHA

    fig, ax = plt.subplots(figsize=(11, 4.5))

    for d in data:
        mb_eff = alpha * d["butane_g"] * 1e-3
        res = simulate(d["angle_deg"], mb_eff, d["vol_mL"], d["T_C"])

        label = (
            f"{d['butane_g']} g: pred {res['range_m']:.1f} m, "
            f"meas {d['range_m']:.1f} m"
        )

        ax.plot(res["traj_x"], res["traj_y"], lw=2, label=label)
        ax.axvline(d["range_m"], ls="--", lw=1, alpha=0.5)

    ax.set_title(f"Calibration trajectories with alpha = {alpha:.4f}")
    ax.set_xlabel("Horizontal distance, x (m)")
    ax.set_ylabel("Height, y (m)")
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.show()

plot_calibration()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — INVERSE SOLVER
# ══════════════════════════════════════════════════════════════════════════════

def height_at_x(traj_x, traj_y, x_target):
    """
    Interpolate trajectory height at a specified horizontal distance.
    """
    traj_x = np.asarray(traj_x)
    traj_y = np.asarray(traj_y)

    if x_target <= traj_x[0]:
        return traj_y[0]
    if x_target >= traj_x[-1]:
        return traj_y[-1]

    return np.interp(x_target, traj_x, traj_y)


def solve(
        x_hole,
        y_hole,
        x_final,
        alpha=None,
        angle_bounds=(10.0, 80.0),
        butane_bounds=(1.0, 50.0),
        verbose=True,
):
    """
    Find measured butane charge and angle needed to:
    1. pass through the hole at (x_hole, y_hole)
    2. land at x_final

    Important:
    The output butane_g is the measured butane amount to put in.
    Internally, the simulator uses alpha * butane_g.
    """
    if alpha is None:
        alpha = ALPHA

    def cost(params):
        angle, butane_g = params

        if not (angle_bounds[0] <= angle <= angle_bounds[1]):
            return 1e9
        if not (butane_bounds[0] <= butane_g <= butane_bounds[1]):
            return 1e9

        mb_eff = alpha * butane_g * 1e-3
        res = simulate(angle_deg=angle, m_butane=mb_eff)

        h_pred = height_at_x(res["traj_x"], res["traj_y"], x_hole)

        range_err = (res["range_m"] - x_final) / max(x_final, 1.0)
        hole_err  = (h_pred - y_hole) / max(y_hole, 0.25)

        return range_err**2 + hole_err**2

    # Coarse grid first so the optimizer starts near a good point.
    angles = np.linspace(angle_bounds[0], angle_bounds[1], 50)
    butanes = np.linspace(butane_bounds[0], butane_bounds[1], 50)

    best = (np.inf, None, None)
    for a in angles:
        for b in butanes:
            c = cost([a, b])
            if c < best[0]:
                best = (c, a, b)

    if verbose:
        print("=" * 72)
        print("INVERSE SOLVER")
        print("=" * 72)
        print(f"Target hole: ({x_hole:.2f} m, {y_hole:.2f} m)")
        print(f"Target landing distance: {x_final:.2f} m")
        print(f"Grid best: angle = {best[1]:.2f} deg, butane = {best[2]:.2f} g, cost = {best[0]:.5f}")

    opt = minimize(
        cost,
        x0=[best[1], best[2]],
        method="Nelder-Mead",
        options={"xatol": 0.02, "fatol": 1e-7, "maxiter": 2000, "adaptive": True},
    )

    angle_opt, butane_opt = opt.x
    angle_opt = float(np.clip(angle_opt, *angle_bounds))
    butane_opt = float(np.clip(butane_opt, *butane_bounds))

    final = simulate(angle_opt, alpha * butane_opt * 1e-3)
    h_hole = height_at_x(final["traj_x"], final["traj_y"], x_hole)
    final_cost = cost([angle_opt, butane_opt])

    result = {
        "angle_deg": angle_opt,
        "butane_g": butane_opt,
        "alpha": alpha,
        "effective_butane_g": alpha * butane_opt,
        "range_m": final["range_m"],
        "height_at_hole": h_hole,
        "tof_s": final["tof_s"],
        "max_height_m": final["max_height_m"],
        "burnout_v": final["burnout_v"],
        "burnout_t": final["burnout_t"],
        "cost": final_cost,
        "traj_x": final["traj_x"],
        "traj_y": final["traj_y"],
    }

    if verbose:
        print()
        print("SOLUTION")
        print("-" * 72)
        print(f"Launch angle             = {angle_opt:.2f} deg")
        print(f"Measured butane charge   = {butane_opt:.2f} g")
        print(f"Effective butane in model= {alpha * butane_opt:.2f} g")
        print(f"Predicted range          = {final['range_m']:.2f} m   target {x_final:.2f} m")
        print(f"Height at hole           = {h_hole:.2f} m   target {y_hole:.2f} m")
        print(f"Time of flight           = {final['tof_s']:.2f} s")
        print(f"Max height               = {final['max_height_m']:.2f} m")
        print(f"Final cost               = {final_cost:.6f}")
        if final_cost > 0.01:
            print()
            print("Warning: final cost is not tiny, so the requested shot may be difficult")
            print("or impossible within the angle/butane bounds.")

    return result


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — PLOT INVERSE SOLUTION
# ══════════════════════════════════════════════════════════════════════════════

def plot_solution(result, x_hole, y_hole, x_final):
    xs = result["traj_x"]
    ys = result["traj_y"]

    fig, ax = plt.subplots(figsize=(11, 4.5))

    ax.plot(xs, ys, lw=2.5, label="Predicted trajectory")
    ax.plot(x_hole, y_hole, "o", ms=9, label="Target hole")
    ax.plot(x_hole, result["height_at_hole"], "x", ms=10, label="Predicted height at hole")
    ax.axvline(x_final, ls="--", lw=1.5, label="Target landing")
    ax.axvline(result["range_m"], ls=":", lw=1.5, label="Predicted landing")

    ax.set_title(
        f"Solution: {result['angle_deg']:.2f} deg, "
        f"{result['butane_g']:.2f} g measured butane"
    )
    ax.set_xlabel("Horizontal distance, x (m)")
    ax.set_ylabel("Height, y (m)")
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.25)
    ax.legend()
    plt.tight_layout()
    plt.show()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 10 — RUN THIS CELL FOR YOUR DESIRED SHOT
# Edit only these three target values.
# ══════════════════════════════════════════════════════════════════════════════

X_HOLE  = 8.15   # m, horizontal location of hole
Y_HOLE  = 6.4    # m, height of hole
X_FINAL = 22   # m, desired landing distance

result = solve(X_HOLE, Y_HOLE, X_FINAL)

plot_solution(result, X_HOLE, Y_HOLE, X_FINAL)
