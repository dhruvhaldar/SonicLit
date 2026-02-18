import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from time import time
try:
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    nproc = comm.Get_size()
    rank = comm.Get_rank()
    MPI_AVAILABLE = True
except (ImportError, RuntimeError):
    MPI = None
    comm = None
    nproc = 1
    rank = 0
    MPI_AVAILABLE = False

#Function for cubic spline interpolation
def cubic_spline(interpolation_weight, f0, f1, f2, f3):
    """
    Performs cubic spline interpolation. Optimized using Horner's method.

    Parameters
    ----------
    interpolation_weight : float
        Weight factor for interpolation (0 to 1).
    f0, f1, f2, f3 : float
        Function values at control points.

    Returns
    -------
    float
        Interpolated value.
    """
    w = interpolation_weight

    # Intermediate terms to reduce operations
    f1_minus_f3 = f1 - f3

    # A6 = f0 - 3f1 + 3f2 - f3 = (f0 - f3) + 3(f2 - f1)
    A6 = (f0 - f3) + 3.0*(f2 - f1)

    # 3*B2 = 3*(f1 - 2f2 + f3)
    B2_3 = 3.0 * (f1 - 2.0*f2 + f3)

    # C6 = -f0 + 6f1 - 3f2 - 2f3 = 3(f1 - f3) - A6
    C6 = 3.0 * f1_minus_f3 - A6

    # Horner's method evaluation: out = (w * (C6 + w * (B2_3 + w * A6)) + 6f2) / 6
    term = w * A6
    term += B2_3
    term *= w
    term += C6
    term *= w
    term += 6.0 * f2
    term *= (1.0/6.0)

    return term


def _precompute_spline_coeffs(interpolation_weight):
    """
    Precomputes coefficients for cubic spline interpolation to avoid
    repeated calculation of weights inside a loop.

    Returns
    -------
    c0, c1, c2, c3 : ndarray
        Coefficients such that result = c0*f0 + c1*f1 + c2*f2 + c3*f3
    """
    w = interpolation_weight
    w_sq = w * w
    w_cu = w_sq * w

    # Coefficients derived from Horner's method implementation in cubic_spline:
    # c0 = (w^3 - w) / 6
    # c1 = (-3w^3 + 3w^2 + 6w) / 6 = -w^3/2 + w^2/2 + w
    # c2 = (3w^3 - 6w^2 - 3w + 6) / 6 = w^3/2 - w^2 - w/2 + 1
    # c3 = (-w^3 + 3w^2 - 2w) / 6

    # Use 1.0/6.0 multiplication instead of division for speed
    inv_6 = 1.0/6.0

    c0 = (w_cu - w) * inv_6
    c1 = -0.5*w_cu + 0.5*w_sq + w
    c2 = 0.5*w_cu - w_sq - 0.5*w + 1.0
    c3 = (-w_cu + 3.0*w_sq - 2.0*w) * inv_6

    return c0, c1, c2, c3


#Functions for calculation of FWH source terms from surface pressure, mass and momentum flux data

#Serial Implementation
def calculate_source_terms_serial(surf_file : str, preprocessed_data, ambient_pressure, ambient_density, speed_of_sound, mach_number, f, is_permeable, skip_Qn=False):
    """
    Calculates FWH source terms (Qn, Lm, Lr) from surface data (Serial implementation).

    Parameters
    ----------
    surf_file : str
        Path prefix for surface files.
    preprocessed_data : pandas.DataFrame or dict
        Preprocessed geometry data. Can be a DataFrame (legacy) or a dictionary of NumPy arrays 'n' and 'r' (optimized).
    ambient_pressure : float
        Ambient pressure.
    ambient_density : float
        Ambient density.
    speed_of_sound : float
        Speed of sound.
    mach_number : array_like
        Mach number vector.
    f : int
        Current time step index.
    is_permeable : bool
        Flag for permeable surface.
    skip_Qn : bool, optional
        If True, skips Qn calculation and returns None for Qn.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing Qn, Lm, Lr terms.
    """
    if "://" in str(surf_file):
        raise ValueError("Security: Remote file paths are not allowed.")

    if is_permeable == True:
        # Optimized: Skip 'temperature' column (index 12) to reduce I/O overhead
        surface_data = pd.read_csv(surf_file, usecols = [8, 9, 10, 11, 13], names = ['density','velocity_x','velocity_y','velocity_z','pressure'], dtype=np.float64, engine='pyarrow')
    else:
        surface_data = pd.read_csv(surf_file, usecols = range(13,14), names = ['pressure'], dtype=np.float64, engine='pyarrow')
    
    surface_data = surface_data[f]

    if isinstance(preprocessed_data, dict):
        # Optimized path
        geom_n = preprocessed_data['n']
        geom_r = preprocessed_data['r']
    else:
        # Legacy path
        geom_n = preprocessed_data[['n1','n2','n3']].to_numpy()
        geom_r = preprocessed_data[['r1','r2','r3']].to_numpy()

    surf_p = surface_data['pressure'].to_numpy() - ambient_pressure
    U0 = speed_of_sound*mach_number
    
    # Optimization: Return dictionary of numpy arrays to avoid DataFrame overhead
    if is_permeable == True:
        surf_rho = surface_data['density'].to_numpy()
        # Optimized: Avoid creating large (N,3) arrays by using component-wise operations
        surf_vx = surface_data['velocity_x'].to_numpy()
        surf_vy = surface_data['velocity_y'].to_numpy()
        surf_vz = surface_data['velocity_z'].to_numpy()

        # Optimized: Avoid creating large intermediate (N,3) array for Qn calculation
        # Qn = (-rho0*U0 + rho*v) dot n
        #    = -rho0 * (U0 dot n) + rho * (v dot n)

        # Calculate v dot n first (N,)
        # Optimized: Component-wise dot product avoids (N,3) array allocation
        v_dot_n = surf_vx * geom_n[:, 0] + surf_vy * geom_n[:, 1] + surf_vz * geom_n[:, 2]

        # Calculate rho * (v dot n) (N,)
        rho_v_dot_n = surf_rho * v_dot_n

        if not skip_Qn:
            # Calculate U0 dot n (N,)
            if isinstance(preprocessed_data, dict) and 'U0_dot_n' in preprocessed_data:
                # Optimized: Use precomputed value
                U0_dot_n = preprocessed_data['U0_dot_n']
            else:
                U0_dot_n = np.dot(geom_n, U0)

            Qn = -ambient_density * U0_dot_n + rho_v_dot_n
        else:
            Qn = None

        # L = p*n + rho*(v - U0)*((v) dot n)
        #   = p*n + rho_v_dot_n * (v - U0)

        # Optimized: Compute L components directly to avoid (N,3) array allocations
        L1 = surf_p * geom_n[:, 0] + rho_v_dot_n * (surf_vx - U0[0])
        L2 = surf_p * geom_n[:, 1] + rho_v_dot_n * (surf_vy - U0[1])
        L3 = surf_p * geom_n[:, 2] + rho_v_dot_n * (surf_vz - U0[2])
        
    else:
        if not skip_Qn:
            # Qn = (-rho0*U0) dot n
            # Optimized: Explicit calculation to handle both scalar and array ambient_density
            Qn = (-ambient_density * U0[0]) * geom_n[:, 0] + \
                 (-ambient_density * U0[1]) * geom_n[:, 1] + \
                 (-ambient_density * U0[2]) * geom_n[:, 2]
        else:
            Qn = None

        L1 = surf_p * geom_n[:, 0]
        L2 = surf_p * geom_n[:, 1]
        L3 = surf_p * geom_n[:, 2]
    
    Lm = -L1*mach_number[0] - L2*mach_number[1] - L3*mach_number[2]
    Lr = L1*geom_r[:, 0] + L2*geom_r[:, 1] + L3*geom_r[:, 2]
    
    return {'Qn': Qn, 'Lm': Lm, 'Lr': Lr}

def _calculate_source_terms_local(surface_data_local, preprocessed_data_local, ambient_density_local, U0, mach_number, is_permeable, skip_Qn):
    """
    Calculates FWH source terms (Qn, Lm, Lr) from LOCAL surface data slices.
    Internal helper for parallel implementation to avoid redundant scatters.

    Parameters
    ----------
    surface_data_local : numpy.ndarray
        Local slice of surface data (pressure, density, velocity).
    preprocessed_data_local : numpy.ndarray
        Local slice of preprocessed geometry data (n, r).
    ambient_density_local : float or numpy.ndarray
        Ambient density (scalar or local slice).
    U0 : numpy.ndarray
        Speed of sound * mach number.
    mach_number : numpy.ndarray
        Mach number vector.
    is_permeable : bool
        Flag for permeable surface.
    skip_Qn : bool
        If True, skips Qn calculation and returns zeros for Qn.

    Returns
    -------
    dict
        Dictionary containing local 'Qn', 'Lm', 'Lr' arrays.
    """
    # Optimized: Avoid creating large (N,3) arrays by using component-wise operations
    surfS = surface_data_local
    preS = preprocessed_data_local
    rho0S = ambient_density_local

    # Preallocate output arrays for Lm and Lr (Qn is computed directly)
    # outS structure: [Qn, Lm, Lr]
    # But we return dict, so just compute components.

    n_local = surfS.shape[0]
    Qn = np.zeros(n_local)

    if is_permeable:
        # surfS columns: [density, vx, vy, vz, pressure]
        # preS columns: [n1, n2, n3, r1, r2, r3]

        # Calculate v dot n (N,)
        v_dot_n = surfS[:,1]*preS[:,0] + surfS[:,2]*preS[:,1] + surfS[:,3]*preS[:,2]

        # Calculate rho * (v dot n) (N,)
        rho_v_dot_n = surfS[:,0] * v_dot_n

        if not skip_Qn:
            # Calculate U0 dot n (N,)
            U0_dot_n = U0[0]*preS[:,0] + U0[1]*preS[:,1] + U0[2]*preS[:,2]

            # Qn = -rho0 * (U0 dot n) + rho * (v dot n)
            Qn = -rho0S * U0_dot_n + rho_v_dot_n

        # L = p*n + rho*(v - U0)*(v dot n)
        #   = p*n + rho_v_dot_n * (v - U0)

        L1 = surfS[:,4]*preS[:,0] + rho_v_dot_n * (surfS[:,1]-U0[0])
        L2 = surfS[:,4]*preS[:,1] + rho_v_dot_n * (surfS[:,2]-U0[1])
        L3 = surfS[:,4]*preS[:,2] + rho_v_dot_n * (surfS[:,3]-U0[2])

    else:
        # surfS columns: [pressure]
        if not skip_Qn:
            Qn = (-rho0S*U0[0])*preS[:,0] + (-rho0S*U0[1])*preS[:,1] + (-rho0S*U0[2])*preS[:,2]

        L1 = surfS[:,0]*preS[:,0]
        L2 = surfS[:,0]*preS[:,1]
        L3 = surfS[:,0]*preS[:,2]

    Lm = -L1*mach_number[0] - L2*mach_number[1] - L3*mach_number[2]
    Lr = L1*preS[:,3] + L2*preS[:,4] + L3*preS[:,5]

    return {'Qn': Qn, 'Lm': Lm, 'Lr': Lr}

#Parallel Implementation
def calculate_source_terms_parallel(surf_file : str, preprocessed_data, ambient_pressure, ambient_density, speed_of_sound, mach_number, f, is_permeable, skip_Qn=False):
    """
    Calculates FWH source terms (Qn, Lm, Lr) from surface data (Parallel implementation).
    This function handles data distribution (scatter/gather) for backward compatibility.

    Parameters
    ----------
    surf_file : str
        Path prefix for surface files.
    preprocessed_data : numpy.ndarray
        Preprocessed geometry data.
    ambient_pressure : float
        Ambient pressure.
    ambient_density : float
        Ambient density.
    speed_of_sound : float
        Speed of sound.
    mach_number : array_like
        Mach number vector.
    f : int
        Current time step index.
    is_permeable : bool
        Flag for permeable surface.
    skip_Qn : bool, optional
        If True, skips Qn calculation and returns zeros for Qn (assumes caller handles static Qn).

    Returns
    -------
    dict
        Dictionary containing Qn, Lm, Lr terms (global).
    
    Raises
    ------
    RuntimeError
        If MPI is not available.
    """
    if "://" in str(surf_file):
        raise ValueError("Security: Remote file paths are not allowed.")

    if not MPI_AVAILABLE:
        raise RuntimeError("MPI is not available. Please install mpi4py and an MPI implementation to use parallel features.")

    if is_permeable == True:
        # Optimized: Skip 'temperature' column (index 12) to reduce I/O overhead
        surface_data = pd.read_csv(surf_file, usecols = [8, 9, 10, 11, 13], names = ['density','velocity_x','velocity_y','velocity_z','pressure'], dtype=np.float64, engine='pyarrow')
    else:
        surface_data = pd.read_csv(surf_file, usecols = range(13,14), names = ['pressure'], dtype=np.float64, engine='pyarrow')
    
    if isinstance(preprocessed_data, pd.DataFrame):
        preprocessed_data = preprocessed_data[['n1','n2','n3','r1','r2','r3']].to_numpy()

    surface_data = surface_data[f]
    U0 = speed_of_sound*mach_number
    surface_data['pressure'] = surface_data['pressure']-ambient_pressure
    surface_data = surface_data.to_numpy()
    
    ave, res = divmod(preprocessed_data[:,0].size, nproc)
    c = [ave + 1 if f < res else ave for f in range(nproc)]
    c = np.array(c)
    index0 = [sum(c[:i]) for i in range(len(c))]
    
    preS = [preprocessed_data[index0[i]:index0[i]+c[i],:] for i in range(nproc)]
    surfS = [surface_data[index0[i]:index0[i]+c[i],:] for i in range(nproc)]
    rho0S = [ambient_density[index0[i]:index0[i]+c[i]] for i in range(nproc)]

    # Scatter data
    preS = comm.scatter(preS, root=0)
    surfS = comm.scatter(surfS, root=0)
    rho0S = comm.scatter(rho0S, root=0)
    
    U0 = comm.bcast(U0, root=0)
    is_permeable = comm.bcast(is_permeable, root=0)
    mach_number = comm.bcast(mach_number, root=0)
    skip_Qn = comm.bcast(skip_Qn, root=0)

    # Perform calculation on local data
    local_res = _calculate_source_terms_local(surfS, preS, rho0S, U0, mach_number, is_permeable, skip_Qn)
    
    # Pack results for gather
    outS = np.zeros((len(preS), 3))
    outS[:, 0] = local_res['Qn']
    outS[:, 1] = local_res['Lm']
    outS[:, 2] = local_res['Lr']
    
    outS = comm.gather(outS, root=0)
    outS = comm.bcast(outS,root=0)
    
    conc = np.concatenate(outS)
    # Optimization: Return dictionary of numpy arrays to avoid DataFrame overhead
    return {'Qn': conc[:,0], 'Lm': conc[:,1], 'Lr': conc[:,2]}



"""
    This implementation is based on using the Garrick Triangle (GT) method for Farassat's formulation 1A of the FWH analogy, for **stationary source and observer positions**. This formulation can be used when simulating a wind tunnel or wind tunnel-like setup.
    
    Resources
    -------
    
    For detail on the implementation see the work of Bres et al (2010) `here <https://doi.org/10.2514/6.2010-3711>`_.
    For the full derivations of Farassat's 1 and 1A formulations, go through `this <https://ntrs.nasa.gov/api/citations/20070010579/downloads/20070010579.pdf>`_  NASA Technical Memorandum.
    
    Parameters
    ----------
    surf_file : str
        Relative path and filename to the csv file containing surface point data in Cartesian coordinates.
    out_file : str
        Relative path and filename for the output CSV file.
    obs_loc : array_like *or* list of lists
        Observer location(s) in Cartesian coordinates specified as a list of lists with one or more elements, e.g. [0., 5.5, 20.5], or [[0., 0., 0.], ..., [1., 1., 1.]]
    t_src   : array_like *or* list
        Source times in seconds when snapshots of surface pressure, velocity and density are stored, e.g., [0, 10000].
    Ma : float
        Freestream Mach number.
    perm    : bool
        Flag for permeable or impermeable surface formulation.
    write    : bool
        Flag for writing output file (If 'True' writes output time history in .csv format, else only saves the .png file).
    Ta : float
        Temperature of the freestream in K. The default is 300.
    gamma : float, optional
        Ratio of specific heats. The default is 1.4.
    MW : float, optional
        Mean molar mass of the fluid in g/mol. The default is 28.97 g/mol (dry air).
    
    Output
    ------
    
    The function writes one or more CSV files (depending on the number of observer locations) containing two columns - Observer time (sec) and Acoustic pressure (Pa)
    
    Returns
    -------
    None.
    
    Notes
    -----
    - This formulation follows the assumption of a stationary source, such as a solid body in a wind tunnel, and hence simplifies the calculations and makes the code efficient.
    - Based on the wind tunnel assumption U\ :sub:`x` = U\ :sub:`inf`, and the second and third principle components of the freestream velocity are set to zero, i.e, U\ :sub:`y` = U\ :sub:`z` = 0.
    
    Examples
    --------
    
    >>> surf_file = "results/surface/surf_xyz_0.csv"
    >>> out_file = "acoustics_fwh/farfield_pres"
    >>> observers = [[0., 0., 10.], [0., 0., -10.]]
    >>> t_src = [0, 0.1, 0.2, 0.3 ..]
    >>> Ma = 0.2
    >>> perm = False
    >>> write = True
    >>> Ta = 293
    >>> fwh.stationary_serial(surf_file,  out_file, obs_loc, t_src, Ma, perm, Ta, write)  or  fwh.stationary_parallel(surf_file,  out_file, obs_loc, t_src, Ma, perm, Ta, write)

    """

#Serial Implementation
def stationary_serial(surf_file : str,  output_filename : str, observer_locations : list, source_times : list, mach_number : list, is_permeable : bool, write : bool = True, ambient_temperature : float = 298, gamma : float = 1.4, MW : float = 28.97):

        if "://" in surf_file:
            raise ValueError("Security: Remote file paths are not allowed.")

        Runiv = 8.314 #Universal gas constant in J/mol . K
        mach_number = np.array(mach_number)
        source_times = np.array(source_times)
        dt = source_times[1]-source_times[0]
        speed_of_sound = np.sqrt(gamma*Runiv*1e3*ambient_temperature/MW)

        #Preprocessing
        preprocessed_data = pd.read_csv(surf_file+'0.csv', usecols = range(7), names = ['y1','y2','y3','n1','n2','n3','dS'], dtype=np.float64, engine='pyarrow')
        filt = preprocessed_data['dS']!=0 #key to Filter rows with on-zero area
        preprocessed_data = preprocessed_data[filt]

        # Optimization: Convert to NumPy arrays for vectorized calculations
        geom_y = preprocessed_data[['y1','y2','y3']].to_numpy()
        geom_n = preprocessed_data[['n1','n2','n3']].to_numpy()
        geom_dS = preprocessed_data['dS'].to_numpy()

        beta = np.sqrt(1-mach_number[0]**2-mach_number[1]**2-mach_number[2]**2)

        p_mean = pd.read_csv(surf_file+'Avg.csv', usecols = range(13,14), names = ['pressure'], dtype=np.float64, engine='pyarrow')
        p_mean = p_mean[filt].reset_index(drop=True)
        rho_mean = pd.read_csv(surf_file+'Avg.csv', usecols = range(8,9), names = ['density'], dtype=np.float64, engine='pyarrow')
        rho_mean = rho_mean[filt].reset_index(drop=True)
        ambient_pressure = p_mean.to_numpy()[:,0]
        ambient_density = rho_mean.to_numpy()[:,0]

        for idx, xo in enumerate(observer_locations):

            #calculation of time independent quantities
            diff = xo - geom_y
            Mr0 = np.dot(diff, mach_number)
            R0 = np.linalg.norm(diff, axis=1)

            # Calculate R - effective acoustic distance
            Rstar = np.sqrt(Mr0**2+(beta*R0)**2)
            R = (-Mr0+Rstar)/(beta**2)

            # Radiation vector
            # Optimized: Simplify r_vec calculation: (-M*R + diff)/R = -M + diff/R
            r_vec = diff / R[:, np.newaxis] - mach_number
            Mr = np.dot(r_vec, -mach_number)

            preprocessed_arrays = {'n': geom_n, 'r': r_vec}

            if is_permeable:
                # Optimized: Precompute U0 dot n to avoid repeated calculation inside the loop
                U0_static = speed_of_sound * mach_number
                U0_dot_n_static = np.dot(geom_n, U0_static)
                preprocessed_arrays['U0_dot_n'] = U0_dot_n_static

            tau = np.array(R/speed_of_sound) #travelling time of sound from all sources
            t_o = source_times+min(tau) #observer times
            tau_star = tau-min(tau)
            interpolation_weight = (tau_star%dt)/dt
            # Optimized: Vectorized calculation instead of list comprehension
            j_star = (tau_star // dt).astype(int)

            t_range = [int((max(tau)-min(tau))//dt)+2,len(t_o)-1]


            D = (max(j_star)-1)*(max(j_star)>1) #number of void elements to be added at end for satisfying j_adv within range
            acoustic_pressure = np.zeros(len(t_o)+D)
            count = np.zeros(len(t_o)+D)

            # Optimization: Precompute size for bincount to avoid repeated max() calls and allocation
            len_p_act = np.max(j_star) + 1

            # Optimization: Precompute geometric factors outside the loop
            M2 = np.sum(mach_number**2)
            one_minus_Mr = 1.0 - Mr
            one_minus_Mr_sq = one_minus_Mr**2
            one_minus_Mr_cu = one_minus_Mr**3

            # Optimization: Precompute spline coefficients
            sp_c0, sp_c1, sp_c2, sp_c3 = _precompute_spline_coeffs(interpolation_weight)

            factor_pt1 = geom_dS / (R * one_minus_Mr_sq)
            factor_pt2 = (geom_dS * (Mr - M2)) / (R**2 * one_minus_Mr_cu)
            factor_pq1 = factor_pt1 / speed_of_sound
            factor_pq2 = geom_dS / (R**2 * one_minus_Mr_sq)
            factor_pq3 = factor_pt2 # Same geometric factor for Lr term
            inv_4pi = 1.0 / (4.0 * np.pi)

            # Optimization: Precompute scaled factors to reduce mults inside loop
            factor_pt1_scaled = factor_pt1 * inv_4pi
            factor_pt2_scaled = factor_pt2 * (speed_of_sound * inv_4pi)
            factor_pq1_scaled = factor_pq1 * inv_4pi
            factor_pq2_scaled = factor_pq2 * inv_4pi
            factor_pq3_scaled = factor_pq3 * inv_4pi

            one_minus_interpolation_weight = 1.0 - interpolation_weight

            # Optimization: Precompute Qn_static for impermeable surfaces
            Qn_static = None
            skip_Qn = False
            pt_static = None

            if not is_permeable:
                # Calculate Qn_static: (-rho0*U0) dot n
                U0_static = speed_of_sound * mach_number
                Qn_static = (-ambient_density * U0_static[0]) * geom_n[:, 0] + \
                            (-ambient_density * U0_static[1]) * geom_n[:, 1] + \
                            (-ambient_density * U0_static[2]) * geom_n[:, 2]
                skip_Qn = True

                # Precompute pt component since Qn is static and Qndot is 0
                # pt = 0 * factor_pt1_scaled + Qn_static * factor_pt2_scaled
                pt_static = Qn_static * factor_pt2_scaled

            src_t0 = calculate_source_terms_serial(surf_file+'0.csv', preprocessed_arrays, ambient_pressure, ambient_density, speed_of_sound, mach_number, filt, is_permeable, skip_Qn=skip_Qn)
            src_t1 = calculate_source_terms_serial(surf_file+'1.csv', preprocessed_arrays, ambient_pressure, ambient_density, speed_of_sound, mach_number, filt, is_permeable, skip_Qn=skip_Qn)
            src_t2 = calculate_source_terms_serial(surf_file+'2.csv', preprocessed_arrays, ambient_pressure, ambient_density, speed_of_sound, mach_number, filt, is_permeable, skip_Qn=skip_Qn)

            # Optimization: Precompute inverse time step factor and initialize loop variables
            inv_2dt = 0.5 / dt
            Lrdot_next = None
            Qndot_next = None

            for j in range(1,len(source_times)-2):
                j_adv = j+j_star+1 #advanced time step
                j_cond = (j_adv >= t_range[0])*(j_adv < t_range[1])

                src_t3 = calculate_source_terms_serial(surf_file+str(j+2)+'.csv', preprocessed_arrays, ambient_pressure, ambient_density, speed_of_sound, mach_number, filt, is_permeable, skip_Qn=skip_Qn)

                # Extract arrays for faster calculation
                # Optimized: Direct dictionary access (values are already numpy arrays)
                Lr0 = src_t0['Lr']
                Lr1 = src_t1['Lr']
                Lr2 = src_t2['Lr']
                Lr3 = src_t3['Lr']

                Lm0 = src_t0['Lm']
                Lm1 = src_t1['Lm']
                Lm2 = src_t2['Lm']
                Lm3 = src_t3['Lm']

                # Optimized: Reuse Lrdot calculations from previous iteration
                if Lrdot_next is None:
                    Lrdot1 = (-Lr0+Lr2)*inv_2dt
                else:
                    Lrdot1 = Lrdot_next

                Lrdot2 = (-Lr1+Lr3)*inv_2dt
                Lrdot_next = Lrdot2

                # Optimized: Use precomputed spline coefficients
                Lr = sp_c0*Lr0 + sp_c1*Lr1 + sp_c2*Lr2 + sp_c3*Lr3
                # Optimized: Linear interpolation as L2 + w*(L1-L2) to save mults
                Lrdot = Lrdot2 + interpolation_weight * (Lrdot1 - Lrdot2)
                Lm = sp_c0*Lm0 + sp_c1*Lm1 + sp_c2*Lm2 + sp_c3*Lm3

                if not is_permeable:
                    # Optimized: Use precomputed pt_static
                    pt = pt_static
                else:
                    Qn0 = src_t0['Qn']
                    Qn1 = src_t1['Qn']
                    Qn2 = src_t2['Qn']
                    Qn3 = src_t3['Qn']

                    # Optimized: Reuse Qndot calculations from previous iteration
                    if Qndot_next is None:
                        Qndot1 = (-Qn0+Qn2)*inv_2dt
                    else:
                        Qndot1 = Qndot_next

                    Qndot2 = (-Qn1+Qn3)*inv_2dt
                    Qndot_next = Qndot2

                    Qn = sp_c0*Qn0 + sp_c1*Qn1 + sp_c2*Qn2 + sp_c3*Qn3
                    # Optimized: Linear interpolation as L2 + w*(L1-L2)
                    Qndot = Qndot2 + interpolation_weight * (Qndot1 - Qndot2)

                    # Optimized: Use precomputed factors
                    pt = Qndot * factor_pt1_scaled + Qn * factor_pt2_scaled

                # Loading component
                pq = Lrdot * factor_pq1_scaled + (Lr - Lm) * factor_pq2_scaled + Lr * factor_pq3_scaled

                p = pt+pq
                p *= j_cond


                # Optimized: Use bincount for faster unbuffered accumulation
                p_act = np.bincount(j_star, weights=p, minlength=len_p_act)
                n_elm = np.bincount(j_star, weights=j_cond, minlength=len_p_act)

                acoustic_pressure[min(j_adv):max(j_adv)+1] += p_act
                count[min(j_adv):max(j_adv)+1] += n_elm

                src_t0 = src_t1
                src_t1 = src_t2
                src_t2 = src_t3


            fig, ax = plt.subplots( nrows=1, ncols=1, figsize = [12,8] )  # create figure & 1 axis
            ax.plot(t_o[t_range[0]:t_range[1]], acoustic_pressure[t_range[0]:t_range[1]],'b')
            plt.title('Pressure time history at location '+str(xo))
            ax.set_xlabel('time (sec)')
            ax.set_ylabel("$p'$ (Pa)")
            fig.savefig(output_filename + str(idx)+ '.png')   # save the figure to file
            plt.close(fig)
            if write :
                p_df = pd.DataFrame({"t_o": t_o[t_range[0]:t_range[1]], "p'": acoustic_pressure[t_range[0]:t_range[1]]})
                p_df.to_csv(output_filename + str(idx)+ '.csv', index=False)
                print("Far-field acoustic pressure for location " + str(xo) + " has been computed successfully. Output CSV file printed as " + output_filename  + str(idx) +  ".csv.")
        if write:
            return "All calculations successfully completed! Far-field acoustic pressure for " + str(len(observer_locations)) + " observer location(s) saved to corresponding PNG images and CSV file(s)"
        else:
            return "All calculations successfully completed! Far-field acoustic pressure for " + str(len(observer_locations)) + " observer location(s) saved to corresponding PNG images "

#Parallel Implementation
def stationary_parallel(surf_file : str,  output_filename : str, observer_locations : list, source_times : list, mach_number : list, is_permeable : bool, write : bool = True, ambient_temperature : float = 298, gamma : float = 1.4, MW : float = 28.97):

    if "://" in surf_file:
        raise ValueError("Security: Remote file paths are not allowed.")

    if not MPI_AVAILABLE:
        raise RuntimeError("MPI is not available. Please install mpi4py and an MPI implementation to use parallel features.")

    Runiv = 8.314 #Universal gas constant in J/mol . K
    mach_number = np.array(mach_number)
    source_times = np.array(source_times)
    dt = source_times[1]-source_times[0]
    speed_of_sound = np.sqrt(gamma*Runiv*1e3*ambient_temperature/MW)

    #Preprocessing
    preprocessed_data = pd.read_csv(surf_file+'0.csv', usecols = range(7), names = ['y1','y2','y3','n1','n2','n3','dS'], dtype=np.float64, engine='pyarrow')
    filt = preprocessed_data['dS']!=0 #key to Filter rows with on-zero area
    preprocessed_data = preprocessed_data[filt]

    # Optimization: Convert to NumPy arrays for vectorized calculations
    geom_y = preprocessed_data[['y1','y2','y3']].to_numpy()
    geom_n = preprocessed_data[['n1','n2','n3']].to_numpy()
    geom_dS = preprocessed_data['dS'].to_numpy()

    beta = np.sqrt(1-mach_number[0]**2-mach_number[1]**2-mach_number[2]**2)

    p_mean = pd.read_csv(surf_file+'Avg.csv', usecols = range(13,14), names = ['pressure'], dtype=np.float64, engine='pyarrow')
    p_mean = p_mean[filt].reset_index(drop=True)
    rho_mean = pd.read_csv(surf_file+'Avg.csv', usecols = range(8,9), names = ['density'], dtype=np.float64, engine='pyarrow')
    rho_mean = rho_mean[filt].reset_index(drop=True)
    ambient_pressure = p_mean.to_numpy()[:,0]
    ambient_density = rho_mean.to_numpy()[:,0]

    for idx, xo in enumerate(observer_locations):

        #calculation of time independent quantities
        diff = xo - geom_y
        Mr0 = np.dot(diff, mach_number)
        R0 = np.linalg.norm(diff, axis=1)

        # Calculate R - effective acoustic distance
        Rstar = np.sqrt(Mr0**2+(beta*R0)**2)
        R = (-Mr0+Rstar)/(beta**2)

        # Radiation vector
        # Optimized: Simplify r_vec calculation: (-M*R + diff)/R = -M + diff/R
        r_vec = diff / R[:, np.newaxis] - mach_number
        Mr = np.dot(r_vec, -mach_number)

        # Optimized: Combine n and r for parallel distribution (Nx6 array)
        preprocessed_arrays = np.hstack((geom_n, r_vec))

        tau = np.array(R/speed_of_sound) #travelling time of sound from all sources
        t_o = source_times+min(tau) #observer times
        tau_star = tau-min(tau)
        interpolation_weight = (tau_star%dt)/dt
        # Optimized: Vectorized calculation instead of list comprehension
        j_star = (tau_star // dt).astype(int)

        t_range = [int((max(tau)-min(tau))//dt)+2,len(t_o)-1]


        D = (max(j_star)-1)*(max(j_star)>1) #number of void elements to be added at end for satisfying j_adv within range
        acoustic_pressure = np.zeros(len(t_o)+D)
        count = np.zeros(len(t_o)+D)

        # Optimization: Precompute size for bincount/arrays
        len_p_act = np.max(j_star) + 1

        # Optimization: Precompute geometric factors outside the loop
        M2 = np.sum(mach_number**2)
        one_minus_Mr = 1.0 - Mr
        one_minus_Mr_sq = one_minus_Mr**2
        one_minus_Mr_cu = one_minus_Mr**3

        # Optimization: Precompute spline coefficients
        sp_c0, sp_c1, sp_c2, sp_c3 = _precompute_spline_coeffs(interpolation_weight)

        factor_pt1 = geom_dS / (R * one_minus_Mr_sq)
        factor_pt2 = (geom_dS * (Mr - M2)) / (R**2 * one_minus_Mr_cu)
        factor_pq1 = factor_pt1 / speed_of_sound
        factor_pq2 = geom_dS / (R**2 * one_minus_Mr_sq)
        factor_pq3 = factor_pt2
        inv_4pi = 1.0 / (4.0 * np.pi)

        # Optimization: Precompute scaled factors to reduce mults inside loop
        factor_pt1_scaled = factor_pt1 * inv_4pi
        factor_pt2_scaled = factor_pt2 * (speed_of_sound * inv_4pi)
        factor_pq1_scaled = factor_pq1 * inv_4pi
        factor_pq2_scaled = factor_pq2 * inv_4pi
        factor_pq3_scaled = factor_pq3 * inv_4pi

        one_minus_interpolation_weight = 1.0 - interpolation_weight

        # Optimization: Precompute Qn_static for impermeable surfaces
        Qn_static = None
        skip_Qn = False
        pt_static = None

        if not is_permeable:
            # Calculate Qn_static: (-rho0*U0) dot n
            U0_static = speed_of_sound * mach_number
            Qn_static = (-ambient_density * U0_static[0]) * geom_n[:, 0] + \
                        (-ambient_density * U0_static[1]) * geom_n[:, 1] + \
                        (-ambient_density * U0_static[2]) * geom_n[:, 2]
            skip_Qn = True

            # Precompute pt component since Qn is static and Qndot is 0
            # pt = 0 * factor_pt1_scaled + Qn_static * factor_pt2_scaled
            pt_static = Qn_static * factor_pt2_scaled

        # Optimization: Calculate distribution indices once outside the loop
        ave, res = divmod(preprocessed_arrays.shape[0], nproc)
        counts = [ave + 1 if f < res else ave for f in range(nproc)]
        offsets = [sum(counts[:i]) for i in range(nproc)]

        my_start = offsets[rank]
        my_end = my_start + counts[rank]

        # Optimization: Helper to read and slice surface data locally
        def get_local_surface_data(filename, mask, start, end, is_perm, amb_p):
            if is_perm:
                df = pd.read_csv(filename, usecols=[8, 9, 10, 11, 13], names=['density','velocity_x','velocity_y','velocity_z','pressure'], dtype=np.float64, engine='pyarrow')
            else:
                df = pd.read_csv(filename, usecols=range(13,14), names=['pressure'], dtype=np.float64, engine='pyarrow')

            # Apply mask (dS != 0)
            df = df[mask]

            # Subtract ambient pressure
            df['pressure'] = df['pressure'] - amb_p

            # Convert to numpy and slice
            data = df.to_numpy()
            return data[start:end]

        # Optimization: Precompute local slices of static data
        preprocessed_local = preprocessed_arrays[my_start:my_end]
        ambient_density_local = ambient_density[my_start:my_end]

        # Optimization: Slice geometric factors to keep only local data
        factor_pt1_scaled_local = factor_pt1_scaled[my_start:my_end]
        factor_pt2_scaled_local = factor_pt2_scaled[my_start:my_end]
        factor_pq1_scaled_local = factor_pq1_scaled[my_start:my_end]
        factor_pq2_scaled_local = factor_pq2_scaled[my_start:my_end]
        factor_pq3_scaled_local = factor_pq3_scaled[my_start:my_end]

        j_star_local = j_star[my_start:my_end]

        pt_static_local = None
        if pt_static is not None:
            pt_static_local = pt_static[my_start:my_end]

        U0_vec = speed_of_sound * mach_number

        # Initialize t0, t1, t2 using local logic
        surf0 = get_local_surface_data(surf_file+'0.csv', filt, my_start, my_end, is_permeable, ambient_pressure)
        src_t0_local = _calculate_source_terms_local(surf0, preprocessed_local, ambient_density_local, U0_vec, mach_number, is_permeable, skip_Qn)

        surf1 = get_local_surface_data(surf_file+'1.csv', filt, my_start, my_end, is_permeable, ambient_pressure)
        src_t1_local = _calculate_source_terms_local(surf1, preprocessed_local, ambient_density_local, U0_vec, mach_number, is_permeable, skip_Qn)

        surf2 = get_local_surface_data(surf_file+'2.csv', filt, my_start, my_end, is_permeable, ambient_pressure)
        src_t2_local = _calculate_source_terms_local(surf2, preprocessed_local, ambient_density_local, U0_vec, mach_number, is_permeable, skip_Qn)

        # Optimization: Precompute inverse time step factor and initialize loop variables
        inv_2dt = 0.5 / dt
        Lrdot_next = None
        Qndot_next = None

        for j in range(1,len(source_times)-2):
            j_adv_local = j + j_star_local + 1 #advanced time step
            j_cond_local = (j_adv_local >= t_range[0])*(j_adv_local < t_range[1])

            # Optimized: Read and compute locally, skipping MPI
            surf3 = get_local_surface_data(surf_file+str(j+2)+'.csv', filt, my_start, my_end, is_permeable, ambient_pressure)
            src_t3_local = _calculate_source_terms_local(surf3, preprocessed_local, ambient_density_local, U0_vec, mach_number, is_permeable, skip_Qn)

            Lr1 = src_t1_local['Lr']
            Lm1 = src_t1_local['Lm']

            Lr2 = src_t2_local['Lr']
            Lm2 = src_t2_local['Lm']

            # Optimized: Reuse Lrdot calculations from previous iteration
            if Lrdot_next is None:
                Lrdot1 = (-src_t0_local['Lr']+src_t2_local['Lr'])*inv_2dt
            else:
                Lrdot1 = Lrdot_next

            Lrdot2 = (-src_t1_local['Lr']+src_t3_local['Lr'])*inv_2dt
            Lrdot_next = Lrdot2

            # Optimized: Use precomputed spline coefficients
            Lr = sp_c0*src_t0_local['Lr'] + sp_c1*src_t1_local['Lr'] + sp_c2*src_t2_local['Lr'] + sp_c3*src_t3_local['Lr']
            # Optimized: Linear interpolation as L2 + w*(L1-L2)
            Lrdot = Lrdot2 + interpolation_weight * (Lrdot1 - Lrdot2)
            Lm = sp_c0*src_t0_local['Lm'] + sp_c1*src_t1_local['Lm'] + sp_c2*src_t2_local['Lm'] + sp_c3*src_t3_local['Lm']

            if not is_permeable:
                # Optimized: Use precomputed pt_static
                pt = pt_static_local
            else:
                # Optimized: Reuse Qndot calculations from previous iteration
                if Qndot_next is None:
                    Qndot1 = (-src_t0_local['Qn']+src_t2_local['Qn'])*inv_2dt
                else:
                    Qndot1 = Qndot_next

                Qndot2 = (-src_t1_local['Qn']+src_t3_local['Qn'])*inv_2dt
                Qndot_next = Qndot2

                Qn = sp_c0*src_t0_local['Qn'] + sp_c1*src_t1_local['Qn'] + sp_c2*src_t2_local['Qn'] + sp_c3*src_t3_local['Qn']
                # Optimized: Linear interpolation as L2 + w*(L1-L2)
                Qndot = Qndot2 + interpolation_weight * (Qndot1 - Qndot2)

                # Optimized: Use precomputed factors
                pt = Qndot * factor_pt1_scaled_local + Qn * factor_pt2_scaled_local

            # Loading component
            pq = Lrdot * factor_pq1_scaled_local + (Lr - Lm) * factor_pq2_scaled_local + Lr * factor_pq3_scaled_local

            p_local = np.array(pt+pq)
            p_local *= j_cond_local

            # Optimized: Use bincount directly on local data
            p_act = np.bincount(j_star_local, weights=p_local, minlength=len_p_act)
            n_elm = np.bincount(j_star_local, weights=j_cond_local, minlength=len_p_act)


            p_act = comm.gather(p_act, root=0)
            n_elm = comm.gather(n_elm, root=0)

            src_t0_local = src_t1_local
            src_t1_local = src_t2_local
            src_t2_local = src_t3_local


            if rank == 0:

                # Reconstruct full j_adv for indexing on Rank 0
                j_adv_full = j + j_star + 1
                p_sum = sum(p_act)
                n_sum = sum(n_elm)

                start_idx = min(j_adv_full)
                end_idx = max(j_adv_full) + 1

                acoustic_pressure[start_idx:end_idx] += p_sum
                count[start_idx:end_idx] += n_sum

        if rank == 0:
            fig, ax = plt.subplots( nrows=1, ncols=1, figsize = [12,8]  )  # create figure & 1 axis
            ax.plot(t_o[t_range[0]:t_range[1]], acoustic_pressure[t_range[0]:t_range[1]],'b')
            plt.title('Pressure time history at location '+str(xo))
            ax.set_xlabel('time (sec)')
            ax.set_ylabel("$p'$ (Pa)")
            fig.savefig(output_filename + str(idx)+ '.png')   # save the figure to file
            plt.close(fig)
            if write:
                p_df = pd.DataFrame({"t_o": t_o[t_range[0]:t_range[1]], "p'": acoustic_pressure[t_range[0]:t_range[1]]})
                p_df.to_csv(output_filename + str(idx)+ '.csv', index=False)
                print("Far-field acoustic pressure for location " + str(xo) + " has been computed successfully. Output CSV file printed as " + output_filename  + str(idx) +  ".csv.")
    if rank == 0 :
        if write:
            return "All calculations successfully completed! Far-field acoustic pressure for " + str(len(observer_locations)) + " observer location(s) saved to corresponding PNG images and CSV file(s)"
        else:
            return "All calculations successfully completed! Far-field acoustic pressure for " + str(len(observer_locations)) + " observer location(s) saved to corresponding PNG images "




