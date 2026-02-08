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


#Functions for calculation of FWH source terms from surface pressure, mass and momentum flux data

#Serial Implementation
def calculate_source_terms_serial(surf_file : str, preprocessed_data, ambient_pressure, ambient_density, speed_of_sound, mach_number, f, is_permeable):
    """
    Calculates FWH source terms (Qn, Lm, Lr) from surface data (Serial implementation).

    Parameters
    ----------
    surf_file : str
        Path prefix for surface files.
    preprocessed_data : pandas.DataFrame
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

    Returns
    -------
    pandas.DataFrame
        DataFrame containing Qn, Lm, Lr terms.
    """
    if is_permeable == True:
        surface_data = pd.read_csv(surf_file, usecols = range(8,14), names = ['density','velocity_x','velocity_y','velocity_z','temperature','pressure'])
    else:
        surface_data = pd.read_csv(surf_file, usecols = range(13,14), names = ['pressure'])
    
    preprocessed_data = preprocessed_data[['n1','n2','n3','r1','r2','r3']]
    
    surface_data = surface_data[f]
    U0 = speed_of_sound*mach_number
    surface_data['pressure'] = surface_data['pressure']-ambient_pressure
    
    Out = pd.DataFrame()
    
    if is_permeable == True:
        Out['Qn'] = (-ambient_density*U0[0]+surface_data['density']*(surface_data['velocity_x']))*preprocessed_data['n1'] + (-ambient_density*U0[1]+surface_data['density']*(surface_data['velocity_y']))*preprocessed_data['n2'] + (-ambient_density*U0[2]+surface_data['density']*(surface_data['velocity_z']))*preprocessed_data['n3']
        L1 = surface_data['pressure']*preprocessed_data['n1'] + surface_data['density']*(surface_data['velocity_x']-U0[0])*((surface_data['velocity_x'])*preprocessed_data['n1']+(surface_data['velocity_y'])*preprocessed_data['n2']+(surface_data['velocity_z'])*preprocessed_data['n3'])
        L2 = surface_data['pressure']*preprocessed_data['n2'] + surface_data['density']*(surface_data['velocity_y']-U0[1])*((surface_data['velocity_x'])*preprocessed_data['n1']+(surface_data['velocity_y'])*preprocessed_data['n2']+(surface_data['velocity_z'])*preprocessed_data['n3'])
        L3 = surface_data['pressure']*preprocessed_data['n3'] + surface_data['density']*(surface_data['velocity_z']-U0[2])*((surface_data['velocity_x'])*preprocessed_data['n1']+(surface_data['velocity_y'])*preprocessed_data['n2']+(surface_data['velocity_z'])*preprocessed_data['n3'])
        
    else:
        Out['Qn'] = (-ambient_density*U0[0])*preprocessed_data['n1'] + (-ambient_density*U0[1])*preprocessed_data['n2'] + (-ambient_density*U0[2])*preprocessed_data['n3']
        L1 = surface_data['pressure']*preprocessed_data['n1']
        L2 = surface_data['pressure']*preprocessed_data['n2']
        L3 = surface_data['pressure']*preprocessed_data['n3']
    
    Out['Lm'] = -L1*mach_number[0] - L2*mach_number[1] - L3*mach_number[2]
    Out['Lr'] = L1*preprocessed_data['r1'] + L2*preprocessed_data['r2'] + L3*preprocessed_data['r3']
    
    return Out

#Parallel Implementation
def calculate_source_terms_parallel(surf_file : str, preprocessed_data, ambient_pressure, ambient_density, speed_of_sound, mach_number, f, is_permeable):
    """
    Calculates FWH source terms (Qn, Lm, Lr) from surface data (Parallel implementation).

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

    Returns
    -------
    pandas.DataFrame
        DataFrame containing Qn, Lm, Lr terms.
    
    Raises
    ------
    RuntimeError
        If MPI is not available.
    """
    if not MPI_AVAILABLE:
        raise RuntimeError("MPI is not available. Please install mpi4py and an MPI implementation to use parallel features.")

    if is_permeable == True:
        surface_data = pd.read_csv(surf_file, usecols = range(8,14), names = ['density','velocity_x','velocity_y','velocity_z','temperature','pressure'])
    else:
        surface_data = pd.read_csv(surf_file, usecols = range(13,14), names = ['pressure'])
    
    preprocessed_data = preprocessed_data[['n1','n2','n3','r1','r2','r3']].to_numpy()
    out = np.zeros([len(preprocessed_data),3])
    
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
    outS = [out[index0[i]:index0[i]+c[i],:] for i in range(nproc)]
    rho0S = [ambient_density[index0[i]:index0[i]+c[i]] for i in range(nproc)]
    preS = comm.scatter(preS, root=0)
    surfS = comm.scatter(surfS, root=0)
    outS = comm.scatter(outS, root=0)
    rho0S = comm.scatter(rho0S, root=0)
    
    U0 = comm.bcast(U0, root=0)
    is_permeable = comm.bcast(is_permeable, root=0)
    mach_number = comm.bcast(mach_number, root=0)
        
    
    if is_permeable == True:
        outS[:,0] = (-rho0S*U0[0]+surfS[:,0]*(surfS[:,1]))*preS[:,0] + (-rho0S*U0[1]+surfS[:,0]*(surfS[:,2]))*preS[:,1] + (-rho0S*U0[2]+surfS[:,0]*(surfS[:,3]))*preS[:,2]
        L1 = surfS[:,5]*preS[:,0] + surfS[:,0]*(surfS[:,1]-U0[0])*((surfS[:,1])*preS[:,0]+(surfS[:,2])*preS[:,1]+(surfS[:,3])*preS[:,2])
        L2 = surfS[:,5]*preS[:,1] + surfS[:,0]*(surfS[:,2]-U0[1])*((surfS[:,1])*preS[:,0]+(surfS[:,2])*preS[:,1]+(surfS[:,3])*preS[:,2])
        L3 = surfS[:,5]*preS[:,2] + surfS[:,0]*(surfS[:,3]-U0[2])*((surfS[:,1])*preS[:,0]+(surfS[:,2])*preS[:,1]+(surfS[:,3])*preS[:,2])
        
    else:
        outS[:,0] = (-rho0S*U0[0])*preS[:,0] + (-rho0S*U0[1])*preS[:,1] + (-rho0S*U0[2])*preS[:,2]
        L1 = surfS[:,0]*preS[:,0]
        L2 = surfS[:,0]*preS[:,1]
        L3 = surfS[:,0]*preS[:,2]
    
    outS[:,1] = -L1*mach_number[0] - L2*mach_number[1] - L3*mach_number[2]
    outS[:,2] = L1*preS[:,3] + L2*preS[:,4] + L3*preS[:,5]
    
    
    outS = comm.gather(outS, root=0)
    outS = comm.bcast(outS,root=0)
    
    Out = pd.DataFrame(np.concatenate(outS),columns=['Qn','Lm','Lr'])
    
    return Out



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
        preprocessed_data = pd.read_csv(surf_file+'0.csv', usecols = range(7), names = ['y1','y2','y3','n1','n2','n3','dS'])
        filt = preprocessed_data['dS']!=0 #key to Filter rows with on-zero area
        preprocessed_data = preprocessed_data[filt]


        beta = np.sqrt(1-mach_number[0]**2-mach_number[1]**2-mach_number[2]**2)

        p_mean = pd.read_csv(surf_file+'Avg.csv', usecols = range(13,14), names = ['pressure'])
        p_mean = p_mean[filt].reset_index(drop=True)
        rho_mean = pd.read_csv(surf_file+'Avg.csv', usecols = range(8,9), names = ['density'])
        rho_mean = rho_mean[filt].reset_index(drop=True)
        ambient_pressure = p_mean.to_numpy()[:,0]
        ambient_density = rho_mean.to_numpy()[:,0]

        for idx, xo in enumerate(observer_locations):

            #calculation of time independent quantities
            Mr0 = mach_number[0]*(xo[0]-preprocessed_data['y1'])+mach_number[1]*(xo[1]-preprocessed_data['y2'])+mach_number[2]*(xo[2]-preprocessed_data['y3'])
            R0 = np.sqrt((xo[0]-preprocessed_data['y1'])**2+(xo[1]-preprocessed_data['y2'])**2+(xo[2]-preprocessed_data['y3'])**2)

            # Calculate R - effective acoustic distance
            Rstar = np.sqrt(Mr0**2+(beta*R0)**2)
            R = (-Mr0+Rstar)/(beta**2)

            # Radiation vector
            preprocessed_data['r1'] = (-mach_number[0]*R + (xo[0]-preprocessed_data['y1']))/R
            preprocessed_data['r2'] = (-mach_number[1]*R + (xo[1]-preprocessed_data['y2']))/R
            preprocessed_data['r3'] = (-mach_number[2]*R + (xo[2]-preprocessed_data['y3']))/R
            Mr = -mach_number[0]*preprocessed_data['r1'] -mach_number[1]*preprocessed_data['r2'] -mach_number[2]*preprocessed_data['r3']

            tau = np.array(R/speed_of_sound) #travelling time of sound from all sources
            t_o = source_times+min(tau) #observer times
            tau_star = tau-min(tau)
            interpolation_weight = (tau_star%dt)/dt
            j_star = np.array([int(k//dt) for k in tau_star])

            t_range = [int((max(tau)-min(tau))//dt)+2,len(t_o)-1]
            p_key = np.zeros_like(t_o)
            p_key[t_range[0]:t_range[1]] = 1


            D = (max(j_star)-1)*(max(j_star)>1) #number of void elements to be added at end for satisfying j_adv within range
            acoustic_pressure = np.zeros(len(t_o)+D)
            count = np.zeros(len(t_o)+D)

            src_t0 = calculate_source_terms_serial(surf_file+'0.csv', preprocessed_data, ambient_pressure, ambient_density, speed_of_sound, mach_number, filt, is_permeable)
            src_t1 = calculate_source_terms_serial(surf_file+'1.csv', preprocessed_data, ambient_pressure, ambient_density, speed_of_sound, mach_number, filt, is_permeable)
            src_t2 = calculate_source_terms_serial(surf_file+'2.csv', preprocessed_data, ambient_pressure, ambient_density, speed_of_sound, mach_number, filt, is_permeable)


            for j in range(1,len(source_times)-2):
                j_adv = j+j_star+1 #advanced time step
                j_cond = (j_adv >= t_range[0])*(j_adv < t_range[1])

                p_act =np.zeros(max(j_star)+1)
                n_elm = np.zeros(max(j_star)+1)
                src_t3 = calculate_source_terms_serial(surf_file+str(j+2)+'.csv', preprocessed_data, ambient_pressure, ambient_density, speed_of_sound, mach_number, filt, is_permeable)
                Qndot1 = (-src_t0['Qn']+src_t2['Qn'])/(2*dt)
                Qn1 = src_t1['Qn']
                Qndot2 = (-src_t1['Qn']+src_t3['Qn'])/(2*dt)
                Qn2 = src_t2['Qn']
                Lrdot1 = (-src_t0['Lr']+src_t2['Lr'])/(2*dt)
                Lr1 = src_t1['Lr']
                Lm1 = src_t1['Lm']
                Lrdot2 = (-src_t1['Lr']+src_t3['Lr'])/(2*dt)
                Lr2 = src_t2['Lr']
                Lm2 = src_t2['Lm']
                Qn = cubic_spline(interpolation_weight,src_t0['Qn'],src_t1['Qn'],src_t2['Qn'],src_t3['Qn'])
                Qndot = (1-interpolation_weight)*Qndot2+interpolation_weight*Qndot1
                Lr = cubic_spline(interpolation_weight,src_t0['Lr'],src_t1['Lr'],src_t2['Lr'],src_t3['Lr'])
                Lrdot = (1-interpolation_weight)*Lrdot2+interpolation_weight*Lrdot1
                Lm = cubic_spline(interpolation_weight,src_t0['Lm'],src_t1['Lm'],src_t2['Lm'],src_t3['Lm'])

                pt1 = (Qndot/(R*(1-Mr)**2))*preprocessed_data['dS']
                pt2 = ((Qn*speed_of_sound*(Mr-sum(mach_number**2)))/(R**2*(1-Mr)**3))*preprocessed_data['dS']
                # Thickness component
                pt = (pt1 + pt2)/(4*np.pi)

                pq1 =(1/speed_of_sound)*(Lrdot/(R*(1-Mr)**2))*preprocessed_data['dS']
                pq2 = ((Lr-Lm)/(R**2*(1-Mr)**2))*preprocessed_data['dS']
                pq3 = ((Lr*(Mr-sum(mach_number**2)))/(R**2*(1-Mr)**3))*preprocessed_data['dS']

                # Loading component
                pq = (pq1+pq2+pq3)/(4*np.pi)
                p = pt+pq
                p *= j_cond


                np.add.at(p_act, j_star, p.values)
                np.add.at(n_elm, j_star, j_cond)

                acoustic_pressure[min(j_adv):max(j_adv)+1] += p_act
                count[min(j_adv):max(j_adv)+1] += n_elm

                src_t0 = src_t1.copy()
                src_t1 = src_t2.copy()
                src_t2 = src_t3.copy()


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
    preprocessed_data = pd.read_csv(surf_file+'0.csv', usecols = range(7), names = ['y1','y2','y3','n1','n2','n3','dS'])
    filt = preprocessed_data['dS']!=0 #key to Filter rows with on-zero area
    preprocessed_data = preprocessed_data[filt]


    beta = np.sqrt(1-mach_number[0]**2-mach_number[1]**2-mach_number[2]**2)

    p_mean = pd.read_csv(surf_file+'Avg.csv', usecols = range(13,14), names = ['pressure'])
    p_mean = p_mean[filt].reset_index(drop=True)
    rho_mean = pd.read_csv(surf_file+'Avg.csv', usecols = range(8,9), names = ['density'])
    rho_mean = rho_mean[filt].reset_index(drop=True)
    ambient_pressure = p_mean.to_numpy()[:,0]
    ambient_density = rho_mean.to_numpy()[:,0]

    for idx, xo in enumerate(observer_locations):

        #calculation of time independent quantities
        Mr0 = mach_number[0]*(xo[0]-preprocessed_data['y1'])+mach_number[1]*(xo[1]-preprocessed_data['y2'])+mach_number[2]*(xo[2]-preprocessed_data['y3'])
        R0 = np.sqrt((xo[0]-preprocessed_data['y1'])**2+(xo[1]-preprocessed_data['y2'])**2+(xo[2]-preprocessed_data['y3'])**2)

        # Calculate R - effective acoustic distance
        Rstar = np.sqrt(Mr0**2+(beta*R0)**2)
        R = (-Mr0+Rstar)/(beta**2)

        # Radiation vector
        preprocessed_data['r1'] = (-mach_number[0]*R + (xo[0]-preprocessed_data['y1']))/R
        preprocessed_data['r2'] = (-mach_number[1]*R + (xo[1]-preprocessed_data['y2']))/R
        preprocessed_data['r3'] = (-mach_number[2]*R + (xo[2]-preprocessed_data['y3']))/R
        Mr = -mach_number[0]*preprocessed_data['r1'] -mach_number[1]*preprocessed_data['r2'] -mach_number[2]*preprocessed_data['r3']

        tau = np.array(R/speed_of_sound) #travelling time of sound from all sources
        t_o = source_times+min(tau) #observer times
        tau_star = tau-min(tau)
        interpolation_weight = (tau_star%dt)/dt
        j_star = np.array([int(k//dt) for k in tau_star])

        t_range = [int((max(tau)-min(tau))//dt)+2,len(t_o)-1]
        p_key = np.zeros_like(t_o)
        p_key[t_range[0]:t_range[1]] = 1


        D = (max(j_star)-1)*(max(j_star)>1) #number of void elements to be added at end for satisfying j_adv within range
        acoustic_pressure = np.zeros(len(t_o)+D)
        count = np.zeros(len(t_o)+D)

        src_t0 = calculate_source_terms_parallel(surf_file+'0.csv', preprocessed_data, ambient_pressure, ambient_density, speed_of_sound, mach_number, filt, is_permeable)
        src_t1 = calculate_source_terms_parallel(surf_file+'1.csv', preprocessed_data, ambient_pressure, ambient_density, speed_of_sound, mach_number, filt, is_permeable)
        src_t2 = calculate_source_terms_parallel(surf_file+'2.csv', preprocessed_data, ambient_pressure, ambient_density, speed_of_sound, mach_number, filt, is_permeable)


        for j in range(1,len(source_times)-2):
            j_adv = j+j_star+1 #advanced time step
            j_cond = (j_adv >= t_range[0])*(j_adv < t_range[1])

            p_act =np.zeros(max(j_star)+1)
            n_elm = np.zeros(max(j_star)+1)
            src_t3 = calculate_source_terms_parallel(surf_file+str(j+2)+'.csv', preprocessed_data, ambient_pressure, ambient_density, speed_of_sound, mach_number, filt, is_permeable)
            Qndot1 = (-src_t0['Qn']+src_t2['Qn'])/(2*dt)
            Qn1 = src_t1['Qn']
            Qndot2 = (-src_t1['Qn']+src_t3['Qn'])/(2*dt)
            Qn2 = src_t2['Qn']
            Lrdot1 = (-src_t0['Lr']+src_t2['Lr'])/(2*dt)
            Lr1 = src_t1['Lr']
            Lm1 = src_t1['Lm']
            Lrdot2 = (-src_t1['Lr']+src_t3['Lr'])/(2*dt)
            Lr2 = src_t2['Lr']
            Lm2 = src_t2['Lm']
            Qn = cubic_spline(interpolation_weight,src_t0['Qn'],src_t1['Qn'],src_t2['Qn'],src_t3['Qn'])
            Qndot = (1-interpolation_weight)*Qndot2+interpolation_weight*Qndot1
            Lr = cubic_spline(interpolation_weight,src_t0['Lr'],src_t1['Lr'],src_t2['Lr'],src_t3['Lr'])
            Lrdot = (1-interpolation_weight)*Lrdot2+interpolation_weight*Lrdot1
            Lm = cubic_spline(interpolation_weight,src_t0['Lm'],src_t1['Lm'],src_t2['Lm'],src_t3['Lm'])

            pt1 = (Qndot/(R*(1-Mr)**2))*preprocessed_data['dS']
            pt2 = ((Qn*speed_of_sound*(Mr-sum(mach_number**2)))/(R**2*(1-Mr)**3))*preprocessed_data['dS']
            # Thickness component
            pt = (pt1 + pt2)/(4*np.pi)

            pq1 =(1/speed_of_sound)*(Lrdot/(R*(1-Mr)**2))*preprocessed_data['dS']
            pq2 = ((Lr-Lm)/(R**2*(1-Mr)**2))*preprocessed_data['dS']
            pq3 = ((Lr*(Mr-sum(mach_number**2)))/(R**2*(1-Mr)**3))*preprocessed_data['dS']

            # Loading component
            pq = (pq1+pq2+pq3)/(4*np.pi)
            p = np.array(pt+pq)
            p *= j_cond

            n_local = int(len(p)/nproc)
            ave, res = divmod(p.size, nproc)
            c = [ave + 1 if f < res else ave for f in range(nproc)]
            c = np.array(c)
            index0 = [sum(c[:i]) for i in range(len(c))]

            Psplit = [p[index0[i]:index0[i]+c[i]] for i in range(nproc)]
            Jsplit = [j_star[index0[i]:index0[i]+c[i]] for i in range(nproc)]
            cond = [j_cond[index0[i]:index0[i]+c[i]] for i in range(nproc)]

            Psplit = comm.scatter(Psplit, root=0)
            Jsplit = comm.scatter(Jsplit, root=0)
            cond = comm.scatter(cond, root=0)
            p_act = comm.bcast(p_act, root=0)
            n_elm = comm.bcast(n_elm, root=0)
            #j_star = comm.bcast(j_star, root=0)

            np.add.at(p_act, Jsplit, Psplit)
            np.add.at(n_elm, Jsplit, cond)


            p_act = comm.gather(p_act, root=0)
            n_elm = comm.gather(n_elm, root=0)


            if rank == 0:

                acoustic_pressure[min(j_adv):max(j_adv)+1] += sum(p_act)
                count[min(j_adv):max(j_adv)+1] += sum(n_elm)

                src_t0 = src_t1.copy()
                src_t1 = src_t2.copy()
                src_t2 = src_t3.copy()

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




