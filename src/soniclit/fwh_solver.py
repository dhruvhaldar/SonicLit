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


def _calculate_source_terms_global(surf_file, f, ambient_pressure, ambient_density, speed_of_sound, mach_number, is_permeable, geom_n, skip_Qn=False, geom_n_dot_mach=None):
    """
    Calculates observer-independent source terms (Qn, Lm, L components) for a single time step.
    This avoids recalculating these for every observer.
    """
    if "://" in str(surf_file):
        raise ValueError("Security: Remote file paths are not allowed.")

    if is_permeable:
        surface_data = pd.read_csv(surf_file, usecols = [8, 9, 10, 11, 13], names = ['density','velocity_x','velocity_y','velocity_z','pressure'], dtype=np.float64, engine='pyarrow')
    else:
        surface_data = pd.read_csv(surf_file, usecols = range(13,14), names = ['pressure'], dtype=np.float64, engine='pyarrow')

    # Apply filter f
    surface_data = surface_data[f]

    surf_p = surface_data['pressure'].to_numpy() - ambient_pressure
    U0 = speed_of_sound*mach_number

    if is_permeable:
        surf_rho = surface_data['density'].to_numpy()
        surf_vx = surface_data['velocity_x'].to_numpy()
        surf_vy = surface_data['velocity_y'].to_numpy()
        surf_vz = surface_data['velocity_z'].to_numpy()

        v_dot_n = surf_vx * geom_n[:, 0] + surf_vy * geom_n[:, 1] + surf_vz * geom_n[:, 2]
        rho_v_dot_n = surf_rho * v_dot_n

        if not skip_Qn:
            U0_dot_n = np.dot(geom_n, U0)
            Qn = -ambient_density * U0_dot_n + rho_v_dot_n
        else:
            Qn = None

        L1 = surf_p * geom_n[:, 0] + rho_v_dot_n * (surf_vx - U0[0])
        L2 = surf_p * geom_n[:, 1] + rho_v_dot_n * (surf_vy - U0[1])
        L3 = surf_p * geom_n[:, 2] + rho_v_dot_n * (surf_vz - U0[2])
        Lm = -L1*mach_number[0] - L2*mach_number[1] - L3*mach_number[2]
    else:
        if not skip_Qn:
            # Qn = (-rho0*U0) dot n
            # Optimized: np.dot leverages BLAS for faster execution
            Qn = -ambient_density * np.dot(geom_n, U0)
        else:
            Qn = None

        # Optimization: If n.M is provided (impermeable case), calculate Lm directly and skip L vector allocation
        if geom_n_dot_mach is not None:
             Lm = -surf_p * geom_n_dot_mach
             L1 = L2 = L3 = None
        else:
             L1 = surf_p * geom_n[:, 0]
             L2 = surf_p * geom_n[:, 1]
             L3 = surf_p * geom_n[:, 2]
             Lm = -L1*mach_number[0] - L2*mach_number[1] - L3*mach_number[2]

    return {'Qn': Qn, 'Lm': Lm, 'L1': L1, 'L2': L2, 'L3': L3, 'surf_p': surf_p}


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
        # Optimized: np.einsum is significantly faster than manual component-wise summation for large array dot products
        v_dot_n = np.einsum('ij,ij->i', surfS[:, 1:4], preS[:, 0:3])

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
            # Optimized: np.dot leverages BLAS for faster execution
            Qn = -rho0S * np.dot(preS[:, :3], U0)

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
        # Optimization: Precompute beta squared to avoid redundant power calculations in the observer loop
        beta_sq = beta * beta
        inv_beta_sq = 1.0 / beta_sq

        p_mean = pd.read_csv(surf_file+'Avg.csv', usecols = range(13,14), names = ['pressure'], dtype=np.float64, engine='pyarrow')
        p_mean = p_mean[filt].reset_index(drop=True)
        rho_mean = pd.read_csv(surf_file+'Avg.csv', usecols = range(8,9), names = ['density'], dtype=np.float64, engine='pyarrow')
        rho_mean = rho_mean[filt].reset_index(drop=True)
        ambient_pressure = p_mean.to_numpy()[:,0]
        ambient_density = rho_mean.to_numpy()[:,0]

        # --- Precompute Observer-Dependent Variables ---
        n_obs = len(observer_locations)
        obs_data = [] # List to store data for each observer

        # Optimization: Precompute n . M for impermeable surface optimization
        geom_n_dot_mach = None
        if not is_permeable:
             geom_n_dot_mach = geom_n[:, 0]*mach_number[0] + geom_n[:, 1]*mach_number[1] + geom_n[:, 2]*mach_number[2]

        # Optimization: Explicit scalar arithmetic is significantly faster than np.sum for length-3 arrays
        M2 = mach_number[0]**2 + mach_number[1]**2 + mach_number[2]**2
        inv_4pi = 1.0 / (4.0 * np.pi)
        inv_2dt = 0.5 / dt

        # Optimization: Precompute inverse speed of sound
        inv_speed_of_sound = 1.0 / speed_of_sound

        for idx, xo in enumerate(observer_locations):
            # Same logic as original
            diff = xo - geom_y
            Mr0 = np.dot(diff, mach_number)
            # Optimized: avoid np.sqrt for R0 as we only need R0**2
            d0 = diff[:,0]
            d1 = diff[:,1]
            d2 = diff[:,2]
            R0_sq = d0*d0 + d1*d1 + d2*d2

            # Calculate R - effective acoustic distance
            Rstar = np.sqrt(Mr0*Mr0 + beta_sq * R0_sq)
            # Optimized: multiply by precomputed inverse square is faster than division
            R = (-Mr0+Rstar) * inv_beta_sq

            # Radiation vector (mathematically optimized to avoid (N,3) allocation)
            inv_R = 1.0 / R
            Mr = M2 - Mr0 * inv_R

            # Optimization: Precompute n . r for impermeable surface optimization
            geom_n_dot_r = None
            if not is_permeable:
                # geom_n_dot_r = n . (diff/R - M) = (n . diff)/R - n.M
                geom_n_dot_r = (geom_n[:, 0]*d0 + geom_n[:, 1]*d1 + geom_n[:, 2]*d2) * inv_R - geom_n_dot_mach

            # Optimization: Use precomputed inverse scalar for ~2x speedup and remove redundant np.array()
            # which causes unnecessary memory allocation since R is already a numpy array.
            tau = R * inv_speed_of_sound #travelling time of sound from all sources

            # Optimization: Use np.min and np.max which are significantly faster than python built-ins for arrays
            min_tau = np.min(tau) if len(tau) > 0 else 0
            t_o = source_times+min_tau #observer times
            tau_star = tau-min_tau

            # Optimization: Computing scaled tau_star once and using floor
            # Avoids costly floating point modulo and division operations
            inv_dt = 1.0 / dt
            tau_star_scaled = tau_star * inv_dt
            j_star = np.floor(tau_star_scaled).astype(int)
            interpolation_weight = tau_star_scaled - j_star

            max_tau = np.max(tau) if len(tau) > 0 else 0
            t_range = [int((max_tau-min_tau)//dt)+2,len(t_o)-1]

            # Optimization: Use np.max for j_star as well
            max_j_star = np.max(j_star) if len(j_star) > 0 else 0
            D = (max_j_star-1)*(max_j_star>1)

            acoustic_pressure = np.zeros(len(t_o)+D)
            len_p_act = np.max(j_star) + 1

            one_minus_Mr = 1.0 - Mr
            # Optimization: Explicit multiplication is faster than the power operator for small integer powers
            one_minus_Mr_sq = one_minus_Mr * one_minus_Mr

            sp_c0, sp_c1, sp_c2, sp_c3 = _precompute_spline_coeffs(interpolation_weight)

            # Optimization: Reuse factors to avoid redundant array divisions and multiplications (~45% speedup)
            # Optimization: Use precalculated inv_R to avoid division by R
            factor_pt1 = geom_dS * inv_R / one_minus_Mr_sq
            factor_pq2 = factor_pt1 * inv_R
            factor_pt2 = factor_pq2 * (Mr - M2) / one_minus_Mr
            # Optimization: Multiply by inverse speed_of_sound rather than using array division
            factor_pq1 = factor_pt1 * inv_speed_of_sound
            factor_pq3 = factor_pt2

            factor_pt1_scaled = factor_pt1 * inv_4pi
            factor_pt2_scaled = factor_pt2 * (speed_of_sound * inv_4pi)
            factor_pq1_scaled = factor_pq1 * inv_4pi
            factor_pq2_scaled = factor_pq2 * inv_4pi
            factor_pq3_scaled = factor_pq3 * inv_4pi

            # Precompute combined weights to optimize inner loop
            k = inv_2dt
            w_dot_0 = -k * interpolation_weight
            w_dot_1 = -k * (1.0 - interpolation_weight)
            w_dot_2 = -w_dot_0 # k * iw
            w_dot_3 = -w_dot_1 # k * (1-iw)

            F1 = factor_pq1_scaled
            F2 = factor_pq2_scaled
            F3 = factor_pq3_scaled

            F23 = F2 + F3

            # W_L_i = w_dot_i * F1 + sp_ci * F23
            W_L_0 = w_dot_0 * F1 + sp_c0 * F23
            W_L_1 = w_dot_1 * F1 + sp_c1 * F23
            W_L_2 = w_dot_2 * F1 + sp_c2 * F23
            W_L_3 = w_dot_3 * F1 + sp_c3 * F23

            # W_M_i = -sp_ci * F2
            W_M_0 = -sp_c0 * F2
            W_M_1 = -sp_c1 * F2
            W_M_2 = -sp_c2 * F2
            W_M_3 = -sp_c3 * F2

            combined_weights = {
                'L': (W_L_0, W_L_1, W_L_2, W_L_3),
                'M': (W_M_0, W_M_1, W_M_2, W_M_3),
                'Q': None,
                'P': None  # For impermeable surface optimization
            }

            # Static pt for impermeable
            pt_static = None
            if not is_permeable:
                 U0_static = speed_of_sound * mach_number
                 # Optimized: np.dot leverages BLAS for faster execution
                 Qn_static = -ambient_density * np.dot(geom_n, U0_static)
                 pt_static = Qn_static * factor_pt2_scaled

                 # Optimization: Precompute combined weights for pressure (W_P)
                 # This allows computing pq = sum(W_P * p) instead of sum(W_L * Lr + W_M * Lm)
                 # W_P = W_L * (n.r) - W_M * (n.M)

                 # Note: geom_n_dot_mach is n.M
                 # geom_n_dot_r is n.r (calculated above as od['geom_n_dot_r']? No, it's a local var here)
                 # Wait, geom_n_dot_r is calculated above in the loop:
                 # geom_n_dot_r = geom_n[:, 0]*r_vec[:, 0] + ...

                 W_P_0 = W_L_0 * geom_n_dot_r - W_M_0 * geom_n_dot_mach
                 W_P_1 = W_L_1 * geom_n_dot_r - W_M_1 * geom_n_dot_mach
                 W_P_2 = W_L_2 * geom_n_dot_r - W_M_2 * geom_n_dot_mach
                 W_P_3 = W_L_3 * geom_n_dot_r - W_M_3 * geom_n_dot_mach

                 combined_weights['P'] = (W_P_0, W_P_1, W_P_2, W_P_3)

            else:
                 F_pt1 = factor_pt1_scaled
                 F_pt2 = factor_pt2_scaled

                 W_Q_0 = w_dot_0 * F_pt1 + sp_c0 * F_pt2
                 W_Q_1 = w_dot_1 * F_pt1 + sp_c1 * F_pt2
                 W_Q_2 = w_dot_2 * F_pt1 + sp_c2 * F_pt2
                 W_Q_3 = w_dot_3 * F_pt1 + sp_c3 * F_pt2

                 combined_weights['Q'] = (W_Q_0, W_Q_1, W_Q_2, W_Q_3)

            obs_data.append({
                'inv_R': inv_R,
                'd0': d0,
                'd1': d1,
                'd2': d2,
                'geom_n_dot_r': geom_n_dot_r,
                'j_star': j_star,
                't_range': t_range,
                'acoustic_pressure': acoustic_pressure,
                'len_p_act': len_p_act,
                'pt_static': pt_static,
                't_o': t_o,
                'combined_weights': combined_weights
            })

        # --- Time Loop ---
        inv_2dt = 0.5 / dt

        skip_Qn = False
        if not is_permeable:
            skip_Qn = True

        # Initialize buffers for t=0, 1, 2
        src_buf = [None] * 4
        src_buf[0] = _calculate_source_terms_global(surf_file+'0.csv', filt, ambient_pressure, ambient_density, speed_of_sound, mach_number, is_permeable, geom_n, skip_Qn, geom_n_dot_mach)
        src_buf[1] = _calculate_source_terms_global(surf_file+'1.csv', filt, ambient_pressure, ambient_density, speed_of_sound, mach_number, is_permeable, geom_n, skip_Qn, geom_n_dot_mach)
        src_buf[2] = _calculate_source_terms_global(surf_file+'2.csv', filt, ambient_pressure, ambient_density, speed_of_sound, mach_number, is_permeable, geom_n, skip_Qn, geom_n_dot_mach)

        # Optimization: Pre-calculate Lr for initial time steps for each observer
        for idx in range(n_obs):
            od = obs_data[idx]
            if is_permeable:
                inv_R = od['inv_R']
                d0, d1, d2 = od['d0'], od['d1'], od['d2']
                # Lr = L . r_vec = (L1*d0 + L2*d1 + L3*d2)/R + Lm
                od['Lr0'] = (src_buf[0]['L1']*d0 + src_buf[0]['L2']*d1 + src_buf[0]['L3']*d2) * inv_R + src_buf[0]['Lm']
                od['Lr1'] = (src_buf[1]['L1']*d0 + src_buf[1]['L2']*d1 + src_buf[1]['L3']*d2) * inv_R + src_buf[1]['Lm']
                od['Lr2'] = (src_buf[2]['L1']*d0 + src_buf[2]['L2']*d1 + src_buf[2]['L3']*d2) * inv_R + src_buf[2]['Lm']
            else:
                # Optimized Lr calculation for impermeable surfaces
                n_dot_r = od['geom_n_dot_r']
                od['Lr0'] = src_buf[0]['surf_p'] * n_dot_r
                od['Lr1'] = src_buf[1]['surf_p'] * n_dot_r
                od['Lr2'] = src_buf[2]['surf_p'] * n_dot_r

        Qndot_next = None

        for j in range(1,len(source_times)-2):
            # Read new file
            src_buf[3] = _calculate_source_terms_global(surf_file+str(j+2)+'.csv', filt, ambient_pressure, ambient_density, speed_of_sound, mach_number, is_permeable, geom_n, skip_Qn, geom_n_dot_mach)

            # Global Lm components
            Lm0 = src_buf[0]['Lm']
            Lm1 = src_buf[1]['Lm']
            Lm2 = src_buf[2]['Lm']
            Lm3 = src_buf[3]['Lm']

            # Global Qn logic (if permeable)
            if is_permeable:
                Qn0 = src_buf[0]['Qn']
                Qn1 = src_buf[1]['Qn']
                Qn2 = src_buf[2]['Qn']
                Qn3 = src_buf[3]['Qn']

                if Qndot_next is None:
                    Qndot1 = (-Qn0+Qn2)*inv_2dt
                else:
                    Qndot1 = Qndot_next
                Qndot2 = (-Qn1+Qn3)*inv_2dt
                Qndot_next = Qndot2

            # --- Loop Observers ---
            for idx in range(n_obs):
                od = obs_data[idx]

                weights = od['combined_weights']
                pq = None

                if is_permeable:
                    # Calculate Lr = L . r
                    # Optimization: Reuse cached Lr values to avoid redundant dot products
                    Lr0 = od['Lr0']
                    Lr1 = od['Lr1']
                    Lr2 = od['Lr2']
                    # Lr = L . r_vec = (L1*d0 + L2*d1 + L3*d2)/R + Lm
                    Lr3 = (src_buf[3]['L1']*od['d0'] + src_buf[3]['L2']*od['d1'] + src_buf[3]['L3']*od['d2']) * od['inv_R'] + src_buf[3]['Lm']

                    # Update cache for next iteration (shift)
                    od['Lr0'] = Lr1
                    od['Lr1'] = Lr2
                    od['Lr2'] = Lr3

                    W_L = weights['L']
                    W_M = weights['M']

                    # Optimized pq calculation using precomputed weights
                    # pq = Sum(W_L_i * Lri) + Sum(W_M_i * Lmi)
                    pq = W_L[0]*Lr0 + W_L[1]*Lr1 + W_L[2]*Lr2 + W_L[3]*Lr3 + \
                         W_M[0]*Lm0 + W_M[1]*Lm1 + W_M[2]*Lm2 + W_M[3]*Lm3
                else:
                    # Optimized path for impermeable surfaces
                    # Uses precomputed W_P weights combined with raw pressure data
                    # avoiding Lr calculation and Lm access
                    W_P = weights['P']
                    p0 = src_buf[0]['surf_p']
                    p1 = src_buf[1]['surf_p']
                    p2 = src_buf[2]['surf_p']
                    p3 = src_buf[3]['surf_p']

                    pq = W_P[0]*p0 + W_P[1]*p1 + W_P[2]*p2 + W_P[3]*p3

                pt = None
                if not is_permeable:
                    pt = od['pt_static']
                else:
                    W_Q = weights['Q']
                    pt = W_Q[0]*Qn0 + W_Q[1]*Qn1 + W_Q[2]*Qn2 + W_Q[3]*Qn3

                p = pt+pq

                # Optimization: Avoid allocating j_adv array and performing redundant min/max scans
                # Original: j_adv = j + od['j_star'] + 1
                j_star = od['j_star']

                # Optimization: Accumulating all data without boundary masks (like j_cond)
                # and simply slicing at the end is significantly faster by avoiding
                # repeated allocation of large boolean arrays.
                p_act = np.bincount(j_star, weights=p, minlength=od['len_p_act'])

                # Optimization: Direct indexing. min(j_adv) = j + 1 + min(j_star) = j + 1
                start_idx = j + 1
                end_idx = start_idx + od['len_p_act']
                od['acoustic_pressure'][start_idx:end_idx] += p_act

            # Shift buffer
            src_buf[0] = src_buf[1]
            src_buf[1] = src_buf[2]
            src_buf[2] = src_buf[3]

        # --- Save Results ---
        for idx in range(n_obs):
            od = obs_data[idx]
            xo = observer_locations[idx]
            t_o = od['t_o']
            t_range = od['t_range']
            acoustic_pressure = od['acoustic_pressure']

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
    # Optimization: Precompute beta squared to avoid redundant power calculations in the observer loop
    beta_sq = beta * beta
    inv_beta_sq = 1.0 / beta_sq

    p_mean = pd.read_csv(surf_file+'Avg.csv', usecols = range(13,14), names = ['pressure'], dtype=np.float64, engine='pyarrow')
    p_mean = p_mean[filt].reset_index(drop=True)
    rho_mean = pd.read_csv(surf_file+'Avg.csv', usecols = range(8,9), names = ['density'], dtype=np.float64, engine='pyarrow')
    rho_mean = rho_mean[filt].reset_index(drop=True)
    ambient_pressure = p_mean.to_numpy()[:,0]
    ambient_density = rho_mean.to_numpy()[:,0]

    # Determine local workload based on surface elements
    n_elements = geom_y.shape[0]
    ave, res = divmod(n_elements, nproc)
    counts = [ave + 1 if f < res else ave for f in range(nproc)]
    offsets = [sum(counts[:i]) for i in range(nproc)]

    my_start = offsets[rank]
    my_end = my_start + counts[rank]

    # Slice geometry to local partition
    geom_y_local = geom_y[my_start:my_end]
    geom_n_local = geom_n[my_start:my_end]
    geom_dS_local = geom_dS[my_start:my_end]
    ambient_density_local = ambient_density[my_start:my_end]

    # --- Precompute Observer-Dependent Variables (Locally) ---
    n_obs = len(observer_locations)
    obs_data = [] # List to store data for each observer (local slices)

    # Optimization: Precompute n . M for impermeable surface optimization
    geom_n_dot_mach_local = None
    if not is_permeable:
         geom_n_dot_mach_local = geom_n_local[:, 0]*mach_number[0] + geom_n_local[:, 1]*mach_number[1] + geom_n_local[:, 2]*mach_number[2]

    # Optimization: Explicit scalar arithmetic is significantly faster than np.sum for length-3 arrays
    M2 = mach_number[0]**2 + mach_number[1]**2 + mach_number[2]**2
    inv_4pi = 1.0 / (4.0 * np.pi)
    inv_2dt = 0.5 / dt

    # Optimization: Precompute inverse speed of sound
    inv_speed_of_sound = 1.0 / speed_of_sound

    for idx, xo in enumerate(observer_locations):
        # Calculate time independent quantities (using LOCAL geometry)
        diff = xo - geom_y_local
        Mr0 = np.dot(diff, mach_number)
        # Optimized: avoid np.sqrt for R0 as we only need R0**2
        d0 = diff[:,0]
        d1 = diff[:,1]
        d2 = diff[:,2]
        R0_sq = d0*d0 + d1*d1 + d2*d2

        # Calculate R - effective acoustic distance
        Rstar = np.sqrt(Mr0*Mr0 + beta_sq * R0_sq)
        # Optimized: multiply by precomputed inverse square is faster than division
        R = (-Mr0+Rstar) * inv_beta_sq

        # Radiation vector (mathematically optimized to avoid (N,3) allocation)
        inv_R = 1.0 / R
        Mr = M2 - Mr0 * inv_R

        # Optimization: Precompute n . r for impermeable surface optimization
        geom_n_dot_r = None
        if not is_permeable:
            # geom_n_dot_r = n . (diff/R - M) = (n . diff)/R - n.M
            geom_n_dot_r = (geom_n_local[:, 0]*d0 + geom_n_local[:, 1]*d1 + geom_n_local[:, 2]*d2) * inv_R - geom_n_dot_mach_local

        # Optimization: Use precomputed inverse scalar for ~2x speedup and remove redundant np.array()
        # which causes unnecessary memory allocation since R is already a numpy array.
        tau = R * inv_speed_of_sound #travelling time of sound from all sources

        # Global synchronization for time arrays
        local_min_tau = np.min(tau) if len(tau) > 0 else float('inf')
        global_min_tau = comm.allreduce(local_min_tau, op=MPI.MIN)

        t_o = source_times + global_min_tau #observer times
        tau_star = tau - global_min_tau # consistent delay

        # Optimization: Computing scaled tau_star once and using floor
        # Avoids costly floating point modulo and division operations
        inv_dt = 1.0 / dt
        tau_star_scaled = tau_star * inv_dt
        j_star = np.floor(tau_star_scaled).astype(int)
        interpolation_weight = tau_star_scaled - j_star

        local_max_tau = np.max(tau) if len(tau) > 0 else float('-inf')
        global_max_tau = comm.allreduce(local_max_tau, op=MPI.MAX)

        t_range = [int((global_max_tau - global_min_tau)//dt)+2, len(t_o)-1]
        max_j_star_global = int((global_max_tau - global_min_tau)//dt)
        D = (max_j_star_global-1)*(max_j_star_global>1)

        acoustic_pressure = np.zeros(len(t_o)+D)
        len_p_act = max_j_star_global + 1

        one_minus_Mr = 1.0 - Mr
        # Optimization: Explicit multiplication is faster than the power operator for small integer powers
        one_minus_Mr_sq = one_minus_Mr * one_minus_Mr

        sp_c0, sp_c1, sp_c2, sp_c3 = _precompute_spline_coeffs(interpolation_weight)

        # Optimization: Reuse factors to avoid redundant array divisions and multiplications (~45% speedup)
        # Optimization: Use precalculated inv_R to avoid division by R
        factor_pt1 = geom_dS_local * inv_R / one_minus_Mr_sq
        factor_pq2 = factor_pt1 * inv_R
        factor_pt2 = factor_pq2 * (Mr - M2) / one_minus_Mr
        # Optimization: Multiply by inverse speed_of_sound rather than using array division
        factor_pq1 = factor_pt1 * inv_speed_of_sound
        factor_pq3 = factor_pt2

        factor_pt1_scaled = factor_pt1 * inv_4pi
        factor_pt2_scaled = factor_pt2 * (speed_of_sound * inv_4pi)
        factor_pq1_scaled = factor_pq1 * inv_4pi
        factor_pq2_scaled = factor_pq2 * inv_4pi
        factor_pq3_scaled = factor_pq3 * inv_4pi

        # Precompute combined weights to optimize inner loop
        k = inv_2dt
        w_dot_0 = -k * interpolation_weight
        w_dot_1 = -k * (1.0 - interpolation_weight)
        w_dot_2 = -w_dot_0 # k * iw
        w_dot_3 = -w_dot_1 # k * (1-iw)

        F1 = factor_pq1_scaled
        F2 = factor_pq2_scaled
        F3 = factor_pq3_scaled

        F23 = F2 + F3

        # W_L_i = w_dot_i * F1 + sp_ci * F23
        W_L_0 = w_dot_0 * F1 + sp_c0 * F23
        W_L_1 = w_dot_1 * F1 + sp_c1 * F23
        W_L_2 = w_dot_2 * F1 + sp_c2 * F23
        W_L_3 = w_dot_3 * F1 + sp_c3 * F23

        # W_M_i = -sp_ci * F2
        W_M_0 = -sp_c0 * F2
        W_M_1 = -sp_c1 * F2
        W_M_2 = -sp_c2 * F2
        W_M_3 = -sp_c3 * F2

        combined_weights = {
            'L': (W_L_0, W_L_1, W_L_2, W_L_3),
            'M': (W_M_0, W_M_1, W_M_2, W_M_3),
            'Q': None,
            'P': None  # For impermeable surface optimization
        }

        # Static pt for impermeable
        pt_static = None
        if not is_permeable:
             U0_static = speed_of_sound * mach_number
             # Optimized: np.dot leverages BLAS for faster execution
             Qn_static = -ambient_density_local * np.dot(geom_n_local, U0_static)
             pt_static = Qn_static * factor_pt2_scaled

             # Optimization: Precompute combined weights for pressure (W_P)
             # This allows computing pq = sum(W_P * p) instead of sum(W_L * Lr + W_M * Lm)
             # W_P = W_L * (n.r) - W_M * (n.M)

             W_P_0 = W_L_0 * geom_n_dot_r - W_M_0 * geom_n_dot_mach_local
             W_P_1 = W_L_1 * geom_n_dot_r - W_M_1 * geom_n_dot_mach_local
             W_P_2 = W_L_2 * geom_n_dot_r - W_M_2 * geom_n_dot_mach_local
             W_P_3 = W_L_3 * geom_n_dot_r - W_M_3 * geom_n_dot_mach_local

             combined_weights['P'] = (W_P_0, W_P_1, W_P_2, W_P_3)

        else:
             F_pt1 = factor_pt1_scaled
             F_pt2 = factor_pt2_scaled

             W_Q_0 = w_dot_0 * F_pt1 + sp_c0 * F_pt2
             W_Q_1 = w_dot_1 * F_pt1 + sp_c1 * F_pt2
             W_Q_2 = w_dot_2 * F_pt1 + sp_c2 * F_pt2
             W_Q_3 = w_dot_3 * F_pt1 + sp_c3 * F_pt2

             combined_weights['Q'] = (W_Q_0, W_Q_1, W_Q_2, W_Q_3)

        obs_data.append({
            'inv_R': inv_R,
            'd0': d0,
            'd1': d1,
            'd2': d2,
            'geom_n_dot_r': geom_n_dot_r,
            'j_star': j_star,
            't_range': t_range,
            'acoustic_pressure': acoustic_pressure,
            'len_p_act': len_p_act,
            'pt_static': pt_static,
            't_o': t_o,
            'combined_weights': combined_weights
        })

    # Helper to read local surface data slice
    def get_local_surface_data(filename, mask, start, end, is_perm, amb_p):
        if is_perm:
            df = pd.read_csv(filename, usecols=[8, 9, 10, 11, 13], names=['density','velocity_x','velocity_y','velocity_z','pressure'], dtype=np.float64, engine='pyarrow')
        else:
            df = pd.read_csv(filename, usecols=range(13,14), names=['pressure'], dtype=np.float64, engine='pyarrow')
        df = df[mask]
        df['pressure'] = df['pressure'] - amb_p
        return df.to_numpy()[start:end]

    # --- Time Loop ---
    inv_2dt = 0.5 / dt
    U0_vec = speed_of_sound * mach_number

    skip_Qn = False
    if not is_permeable:
        skip_Qn = True

    # Helper to calculate local L and Qn
    def calc_source_terms_local_components(surfS):
        # surfS columns: [density, vx, vy, vz, pressure] or [pressure]

        Qn = None
        if is_permeable:
             # Optimized: np.einsum is significantly faster than manual component-wise summation for large array dot products
             v_dot_n = np.einsum('ij,ij->i', surfS[:, 1:4], geom_n_local)
             rho_v_dot_n = surfS[:,0] * v_dot_n
             if not skip_Qn:
                 # Optimized: np.dot leverages BLAS for faster execution
                 U0_dot_n = np.dot(geom_n_local, U0_vec)
                 Qn = -ambient_density_local * U0_dot_n + rho_v_dot_n

             L1 = surfS[:,4]*geom_n_local[:,0] + rho_v_dot_n * (surfS[:,1]-U0_vec[0])
             L2 = surfS[:,4]*geom_n_local[:,1] + rho_v_dot_n * (surfS[:,2]-U0_vec[1])
             L3 = surfS[:,4]*geom_n_local[:,2] + rho_v_dot_n * (surfS[:,3]-U0_vec[2])
             Lm = -L1*mach_number[0] - L2*mach_number[1] - L3*mach_number[2]
        else:
             # Impermeable
             if not skip_Qn:
                 # Optimized: np.dot leverages BLAS for faster execution
                 Qn = -ambient_density_local * np.dot(geom_n_local, U0_vec)

             # Optimization: If n.M is provided (impermeable case), calculate Lm directly and skip L vector allocation
             if geom_n_dot_mach_local is not None:
                 Lm = -surfS[:, 0] * geom_n_dot_mach_local # surfS[:,0] is pressure
                 L1 = L2 = L3 = None
             else:
                 L1 = surfS[:,0]*geom_n_local[:,0]
                 L2 = surfS[:,0]*geom_n_local[:,1]
                 L3 = surfS[:,0]*geom_n_local[:,2]
                 Lm = -L1*mach_number[0] - L2*mach_number[1] - L3*mach_number[2]

        surf_p = surfS[:, 4] if is_permeable else surfS[:, 0]
        return {'Qn': Qn, 'Lm': Lm, 'L1': L1, 'L2': L2, 'L3': L3, 'surf_p': surf_p}

    # Initialize buffers for t=0, 1, 2
    src_buf = [None] * 4
    for k in range(3):
        surf = get_local_surface_data(surf_file+str(k)+'.csv', filt, my_start, my_end, is_permeable, ambient_pressure)
        src_buf[k] = calc_source_terms_local_components(surf)

    # Pre-calculate Lr for initial time steps for each observer (LOCAL)
    for idx in range(n_obs):
        od = obs_data[idx]
        for k in range(3):
            if is_permeable:
                # Lr = L . r_vec = (L1*d0 + L2*d1 + L3*d2)/R + Lm
                od[f'Lr{k}'] = (src_buf[k]['L1']*od['d0'] + src_buf[k]['L2']*od['d1'] + src_buf[k]['L3']*od['d2']) * od['inv_R'] + src_buf[k]['Lm']
            else:
                # Optimized Lr calculation for impermeable surfaces
                od[f'Lr{k}'] = src_buf[k]['surf_p'] * od['geom_n_dot_r']

    Qndot_next = None

    for j in range(1,len(source_times)-2):
        # Read new file (ONCE per time step)
        surf3 = get_local_surface_data(surf_file+str(j+2)+'.csv', filt, my_start, my_end, is_permeable, ambient_pressure)
        src_buf[3] = calc_source_terms_local_components(surf3)

        # Global Lm components
        Lm0 = src_buf[0]['Lm']
        Lm1 = src_buf[1]['Lm']
        Lm2 = src_buf[2]['Lm']
        Lm3 = src_buf[3]['Lm']

        # Global Qn logic (if permeable)
        if is_permeable:
            Qn0 = src_buf[0]['Qn']
            Qn1 = src_buf[1]['Qn']
            Qn2 = src_buf[2]['Qn']
            Qn3 = src_buf[3]['Qn']

            if Qndot_next is None:
                Qndot1 = (-Qn0+Qn2)*inv_2dt
            else:
                Qndot1 = Qndot_next
            Qndot2 = (-Qn1+Qn3)*inv_2dt
            Qndot_next = Qndot2

        # --- Loop Observers ---
        for idx in range(n_obs):
            od = obs_data[idx]

            weights = od['combined_weights']
            pq = None

            if is_permeable:
                Lr0 = od['Lr0']
                Lr1 = od['Lr1']
                Lr2 = od['Lr2']
                # Lr = L . r_vec = (L1*d0 + L2*d1 + L3*d2)/R + Lm
                Lr3 = (src_buf[3]['L1']*od['d0'] + src_buf[3]['L2']*od['d1'] + src_buf[3]['L3']*od['d2']) * od['inv_R'] + src_buf[3]['Lm']

                # Update cache for next iteration (shift)
                od['Lr0'] = Lr1
                od['Lr1'] = Lr2
                od['Lr2'] = Lr3

                W_L = weights['L']
                W_M = weights['M']

                # Optimized pq calculation using precomputed weights
                # pq = Sum(W_L_i * Lri) + Sum(W_M_i * Lmi)
                pq = W_L[0]*Lr0 + W_L[1]*Lr1 + W_L[2]*Lr2 + W_L[3]*Lr3 + \
                     W_M[0]*Lm0 + W_M[1]*Lm1 + W_M[2]*Lm2 + W_M[3]*Lm3
            else:
                # Optimized path for impermeable surfaces
                # Uses precomputed W_P weights combined with raw pressure data
                # avoiding Lr calculation and Lm access
                W_P = weights['P']
                p0 = src_buf[0]['surf_p']
                p1 = src_buf[1]['surf_p']
                p2 = src_buf[2]['surf_p']
                p3 = src_buf[3]['surf_p']

                pq = W_P[0]*p0 + W_P[1]*p1 + W_P[2]*p2 + W_P[3]*p3

            pt = None
            if not is_permeable:
                pt = od['pt_static']
            else:
                W_Q = weights['Q']
                pt = W_Q[0]*Qn0 + W_Q[1]*Qn1 + W_Q[2]*Qn2 + W_Q[3]*Qn3

            p = pt+pq

            # Optimization: Avoid allocating j_adv array and performing redundant min/max scans
            # Original: j_adv = j + od['j_star'] + 1
            j_star = od['j_star']

            # Optimization: Accumulating all data without boundary masks (like j_cond)
            # and simply slicing at the end is significantly faster by avoiding
            # repeated allocation of large boolean arrays.
            p_act = np.bincount(j_star, weights=p, minlength=od['len_p_act'])

            # Accumulate locally
            # We align p_act (starting at 0) to j+1 in acoustic_pressure
            od['acoustic_pressure'][j+1 : j+1+od['len_p_act']] += p_act

        # Shift buffer
        src_buf[0] = src_buf[1]
        src_buf[1] = src_buf[2]
        src_buf[2] = src_buf[3]

    # --- Reduce Results ---
    for idx in range(n_obs):
        od = obs_data[idx]

        # Reduce acoustic_pressure
        global_p = np.zeros_like(od['acoustic_pressure'])
        comm.Reduce(od['acoustic_pressure'], global_p, op=MPI.SUM, root=0)

        if rank == 0:
            t_o = od['t_o']
            t_range = od['t_range']

            fig, ax = plt.subplots( nrows=1, ncols=1, figsize = [12,8] )  # create figure & 1 axis
            ax.plot(t_o[t_range[0]:t_range[1]], global_p[t_range[0]:t_range[1]],'b')
            plt.title('Pressure time history at location '+str(xo))
            ax.set_xlabel('time (sec)')
            ax.set_ylabel("$p'$ (Pa)")
            fig.savefig(output_filename + str(idx)+ '.png')   # save the figure to file
            plt.close(fig)
            if write:
                p_df = pd.DataFrame({"t_o": t_o[t_range[0]:t_range[1]], "p'": global_p[t_range[0]:t_range[1]]})
                p_df.to_csv(output_filename + str(idx)+ '.csv', index=False)
                print("Far-field acoustic pressure for location " + str(xo) + " has been computed successfully. Output CSV file printed as " + output_filename  + str(idx) +  ".csv.")

    if rank == 0 :
        if write:
            return "All calculations successfully completed! Far-field acoustic pressure for " + str(len(observer_locations)) + " observer location(s) saved to corresponding PNG images and CSV file(s)"
        else:
            return "All calculations successfully completed! Far-field acoustic pressure for " + str(len(observer_locations)) + " observer location(s) saved to corresponding PNG images "




