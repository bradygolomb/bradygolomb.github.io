"""
RUBBER-BAND BUNGEE DESIGN MODEL       (MEAM 3470 bungee lab)
=======================================================

What it does
------------
Given the drop height, the mass, and how the bands are tied, it finds how many
bands to put in series and in parallel and how much string to use so the
dropper falls a chosen target distance without hitting the floor or exceeding
the g limit.

Physics (energy balance)
------------------------
      Fall       H_fall = offset + string + s*L_group + x
      Energy     m*g*H_fall = n*s*W(x/s)                (bands store all the fall energy)
      Peak       a_peak = n*F(x/s) / (m*g)              (accelerometer reading, in g)
where
      n         bands in parallel per group,     s = groups in series
      x         total stretch of the band chain at the lowest point
      F(q)      force of one band stretched q metres       (measured cubic fit)
      W(q)      energy stored in one band = integral of F(q) dq
      offset    carabiner (band attachment) to the bottom of the dropper.
                At release the dropper BOTTOM is level with the drop point, so the
                dropper free-falls offset + string + unstretched bands before the
                bands start to stretch.

Tying (knot) effect on length
-----------------------------
Linking groups together eats part of each band's length. A free band is
RAW_BAND_M long, but in a tied chain each group only adds L_group:
      L_group    = measured chain length / number of groups in that chain
      knot loss = RAW_BAND_M - L_group         (length lost per tied link)
Tying only changes the unstretched length. Each band still stretches from its
own resting length, so the force curve F(q) is unchanged. Shorter groups mean
less free fall, which the model makes up with longer string.

Calibration from our real drop (DROP00)
---------------------------------------
Build: 22 series x 8 parallel (two strands of 22 x 4), string about 4.34 m,
0.75 kg, 14.3 m drop, 0.22 m offset.       Measured: 11.7 m fall, 4.2 g peak.
The hang-test fit predicted 12.01 m and 3.43 g, so from that one drop:
      STIFFNESS_SCALE   = 1.067    (bands act about 7% stiffer in a fast drop)
      PEAK_G_FACTOR     = 1.204    (measured peak is about 20% above the energy-model
                                    peak: rate stiffening, uneven load sharing in knots,
                                    sensor vibration)
This is a single-drop calibration; treat it as an estimate.

Colab / Jupyter: edit the DAY-OF INPUTS block at the bottom and run the cell.
Standard library only.
"""

import math

G = 9.80665

# ---------------------------------------------------------------------------
# Band force model (measured hang-test fit, same bands as the other group)
#     F(q) = A q^3 + B q^2 + C q        [N per band],   q = band stretch in m
# ---------------------------------------------------------------------------
A = 187.57329345409667
B = -102.96450994405254
C = 26.088487818355468
MEASURED_EXTENSION_MAX_M = 0.378  # fit is not used beyond measured data
MAX_STRETCH_RATIO = 5.0  # stretched length <= 5 x tied group length

# ---------------------------------------------------------------------------
# Tying (knot) length model
# ---------------------------------------------------------------------------
RAW_BAND_M = 3.5 * 0.0254  # free band length, m (3.5 in)

# ---------------------------------------------------------------------------
# Calibration from DROP00 (set both to 1.0 for the pure hang-test model)
# ---------------------------------------------------------------------------
STIFFNESS_SCALE = 1.067
PEAK_G_FACTOR = 1.204

# ---------------------------------------------------------------------------
# Design rules
# ---------------------------------------------------------------------------
FORCE_CAP_N = 0.80 * 0.850 * G * 2.5 / 2  # per-band cap from failure test
MIN_DROP_FRACTION = 0.70  # scoring minimum, fraction of height
GMAX_DESIGN_FRACTION = 0.90  # design peak <= 90% of the g limit
MODEL_UNCERTAINTY = 0.15  # robustness: bands +/- 15% stiffness
MAX_PARALLEL = 20
MAX_BANDS = 400
SHOW_DESIGNS = 6


# ============================ band functions ================================
def band_force(q, scale=1.0):
    """Force of one band stretched q metres, N."""
    q = max(0.0, q)
    return scale * q * (C + q * (B + A * q))


def band_work(q, scale=1.0):
    """Energy stored in one band stretched q metres, J."""
    q = max(0.0, q)
    return scale * q * q * (C / 2 + q * (B / 3 + A * q / 4))


def bisect(f, target, lo, hi):
    """Root of an increasing function f(x) = target on [lo, hi]."""
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if f(mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ============================ tying model ===================================
def tied_group_length(chain_length_m, groups_in_chain):
    """Length each tied group adds, from a measured hanging chain."""
    return chain_length_m / groups_in_chain


def stretch_limit(group_length):
    """Largest per-band stretch the model will use, m."""
    return min(MEASURED_EXTENSION_MAX_M, group_length * (MAX_STRETCH_RATIO - 1))


# ============================ drop simulation ===============================
def simulate(n, s, string, mass, offset, group_length, scale=None, ext_limit=None):
    """Lowest point of a drop for a built bungee.
    Returns dict (fall, peak_g, stretch per band, ...) or None if the bands
    would need to stretch past the model range."""
    scale = STIFFNESS_SCALE if scale is None else scale
    ext_limit = stretch_limit(group_length) if ext_limit is None else ext_limit
    weight = mass * G
    free_fall = offset + string + s * group_length

    def excess(x):  # stored energy minus energy to absorb (< 0 until bottom)
        return n * s * band_work(x / s, scale) - weight * (free_fall + x)

    x_hi = s * ext_limit
    if excess(x_hi) < 0:
        return None
    q_static = bisect(lambda q: band_force(q, scale), weight / n, 0.0, 2.0)
    x = bisect(excess, 0.0, min(s * q_static, x_hi), x_hi)
    model_g = n * band_force(x / s, scale) / weight
    return {
        "free_fall": free_fall,
        "fall": free_fall + x,
        "stretch_per_band": x / s,
        "model_g": model_g,
        "peak_g": model_g * PEAK_G_FACTOR,  # expected accelerometer peak
        "force_per_band": band_force(x / s, scale),
        "speed_at_catch": math.sqrt(2 * G * free_fall),
    }


# ============================ design search =================================
def find_designs(height, target, mass, offset, gmax, gmin, group_length):
    weight = mass * G
    ext_limit = stretch_limit(group_length)
    designs = []
    max_series = int((target - offset) / group_length) + 1

    for n in range(1, MAX_PARALLEL + 1):
        for s in range(1, max_series + 1):
            if n * s > MAX_BANDS:
                break
            need = weight * target / (n * s)  # energy per band at target
            if band_work(ext_limit, STIFFNESS_SCALE) < need:
                continue
            q = bisect(lambda v: band_work(v, STIFFNESS_SCALE), need, 0.0, ext_limit)
            if n * band_force(q, STIFFNESS_SCALE) < weight:
                continue
            string = target - s * q - offset - s * group_length
            if string < 0:
                continue
            nominal = simulate(n, s, string, mass, offset, group_length)
            if nominal is None:
                continue
            if nominal["peak_g"] > gmax * GMAX_DESIGN_FRACTION or nominal["peak_g"] < gmin:
                continue
            if nominal["force_per_band"] > FORCE_CAP_N:
                continue
            soft = simulate(
                n,
                s,
                string,
                mass,
                offset,
                group_length,
                STIFFNESS_SCALE * (1 - MODEL_UNCERTAINTY),
                0.6,
            )
            stiff = simulate(
                n,
                s,
                string,
                mass,
                offset,
                group_length,
                STIFFNESS_SCALE * (1 + MODEL_UNCERTAINTY),
                0.6,
            )
            robust = (
                soft is not None
                and soft["fall"] < height
                and soft["peak_g"] <= gmax
                and stiff is not None
                and stiff["fall"] >= MIN_DROP_FRACTION * height
                and stiff["peak_g"] >= gmin
            )
            designs.append(
                {
                    "n": n,
                    "s": s,
                    "bands": n * s,
                    "string": string,
                    "nom": nominal,
                    "soft": soft,
                    "stiff": stiff,
                    "robust": robust,
                }
            )

    # robust first, then fewest bands, then lowest peak
    designs.sort(key=lambda d: (not d["robust"], d["bands"], d["nom"]["peak_g"]))
    return designs


def strand_options(n):
    """Ways to split n parallel bands into identical side-by-side strands."""
    return [(k, n // k) for k in range(1, n + 1) if n % k == 0 and k <= 4]


# ============================ reports =======================================
def report(height, target, mass, offset, gmax, gmin, chain_length, groups_in_chain):
    L = tied_group_length(chain_length, groups_in_chain)
    print("=" * 66)
    print("BUNGEE DESIGN")
    print("=" * 66)
    print(
        f"Drop height (anchor to floor) {height:.3f} m | target fall {target:.3f} m "
        f"({100*target/height:.0f}%)"
    )
    print(f"Mass {mass:.3f} kg | offset {offset:.3f} m | g limit {gmin:g}-{gmax:g} g")
    print("\nTYING")
    print(f"     Measured chain: {chain_length:.3f} m for {groups_in_chain} tied groups")
    print(
        f"     Length per tied group: {1000*L:.1f} mm   (free band {1000*RAW_BAND_M:.1f} mm, "
        f"knot loss {1000*(RAW_BAND_M-L):.1f} mm per link)"
    )
    print(f"     Max stretch per band used: {1000*stretch_limit(L):.0f} mm")
    print(
        f"\nCALIBRATION: stiffness x{STIFFNESS_SCALE:.3f}, peak g x{PEAK_G_FACTOR:.3f} "
        f"(from DROP00)"
    )

    designs = find_designs(height, target, mass, offset, gmax, gmin, L)
    if not designs:
        print(
            "\nNo feasible design. Lower the target, raise the g limit, "
            "or raise MAX_PARALLEL / MAX_BANDS."
        )
        return None

    print("\nTOP DESIGNS     (peak = expected accelerometer reading)")
    print(
        " #      n   s bands string_m   fall_m clear_m peak_g | +/-15% bands: fall range, peak range | robust"
    )
    for i, d in enumerate(designs[:SHOW_DESIGNS], 1):
        nom, so, st = d["nom"], d["soft"], d["stiff"]
        rng = (
            (
                f"{st['fall']:5.2f}-{so['fall']:5.2f} m, {min(so['peak_g'], st['peak_g']):.2f}-"
                f"{max(so['peak_g'], st['peak_g']):.2f} g"
            )
            if so and st
            else "n/a"
        )
        print(
            f"{i:2d} {d['n']:3d} {d['s']:3d} {d['bands']:5d} {d['string']:8.3f} "
            f"{nom['fall']:7.2f} {height-nom['fall']:7.2f} {nom['peak_g']:6.2f} | {rng} | "
            f"{'YES' if d['robust'] else 'no'}"
        )

    b = designs[0]
    nom = b["nom"]
    rubber = b["s"] * L
    print("\nBUILD")
    print(
        f"     Configuration: {b['s']} groups in series x {b['n']} bands in parallel "
        f"= {b['bands']} bands"
    )
    for k, per in strand_options(b["n"]):
        if k > 1:
            print(
                f"       (or {k} identical strands of {b['s']} x {per}, joined at the "
                f"same string end and carabiner)"
            )
    print(f"     String section:              {b['string']:.3f} m")
    print(f"     Rubber band section:         {rubber:.3f} m   ({b['s']} x {1000*L:.1f} mm)")
    print(f"     Total unstretched length: {b['string'] + rubber:.3f} m")
    print("\nPREDICTION")
    print(
        f"     Free fall before bands catch: {nom['free_fall']:.2f} m "
        f"(speed {nom['speed_at_catch']:.1f} m/s)"
    )
    print(f"     Fall: {nom['fall']:.2f} m     | floor clearance {height-nom['fall']:.2f} m")
    print(
        f"     Peak: {nom['peak_g']:.2f} g expected on accelerometer "
        f"(energy model {nom['model_g']:.2f} g)"
    )
    print(
        f"     Per band: {nom['force_per_band']:.2f} N (cap {FORCE_CAP_N:.2f} N), "
        f"{1000*nom['stretch_per_band']:.0f} mm stretch"
    )
    print(
        f"     String change per 1 mm of group length: {b['s']:.0f} mm "
        f"(string = {b['string']:.3f} + {b['s']} x ({L:.4f} - new length))"
    )
    if not b["robust"]:
        print("     WARNING: failed the +/-15% robustness check; little margin for error.")
    return b


def validate_drop00():
    """Compare model predictions with our measured drop."""
    L = tied_group_length(0.38, 5)
    kw = dict(n=8, s=22, string=4.337, mass=0.75, offset=0.22, group_length=L)
    raw = simulate(**kw, scale=1.0, ext_limit=0.6)
    cal = simulate(**kw)
    print("\n" + "=" * 66)
    print("VALIDATION: DROP00 (22 x 8, 4.337 m string, 0.75 kg, 14.3 m)")
    print("=" * 66)
    print(f"{'':28s}{'fall (m)':>10s}{'peak (g)':>10s}")
    print(f"{'Hang-test model':28s}{raw['fall']:10.2f}{raw['model_g']:10.2f}")
    print(f"{'Calibrated model':28s}{cal['fall']:10.2f}{cal['peak_g']:10.2f}")
    print(f"{'Measured':28s}{11.7:10.2f}{4.2:10.2f}")
    print(
        f"Hang-test model error: fall {100*(raw['fall']-11.7)/11.7:+.1f}%, "
        f"peak {100*(raw['model_g']-4.2)/4.2:+.1f}%"
    )


# =============================== DAY-OF INPUTS ==============================
height = 14.3  # drop point (anchor) to floor, m
target = 12.155  # fall you aim for, m
mass = 0.75  # total suspended mass, kg
offset = 0.22  # carabiner to bottom of dropper, m
gmax = 5  # maximum allowed peak, g
gmin = 0  # minimum required peak, g (0 = none)
chain_length = 0.38  # measured length of a tied test chain, hanging, m
groups_in_chain = 5  # number of groups in that test chain
report(height, target, mass, offset, gmax, gmin, chain_length, groups_in_chain)
