import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from time import time
from mpi4py import MPI

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
rank = comm.Get_rank()

#Function for cubic spline interpolation
def cubicSpline(w,f0,f1,f2,f3):
	
	out = -(w*(1-w)*(1+w)/6)*f0 + (w*(1+w)*(2-w)/2)*f1 + ((1-w)*(1+w)*(2-w)/2)*f2 - (w*(1-w)*(2-w)/6)*f3
	return out


#Functions for calculation of FWH source terms from surface pressure, mass and momentum flux data

#Serial Implementation
def Serial_source(surf_file : str, pre, p0, rho0, c0, Ma, f, perm):

	if perm == True:
		surf = pd.read_csv(surf_file, usecols = range(8,14), names = ['rho','u1','u2','u3','T','p'])
		read_time = time()
	else:
		surf = pd.read_csv(surf_file, usecols = range(13,14), names = ['p'])
		read_time = time()
	
	pre = pre[['n1','n2','n3','r1','r2','r3']]
	
	surf = surf[f]
	surf.reset_index(drop=True)
	U0 = c0*Ma
	surf['p'] = surf['p']-p0
	
	Out = pd.DataFrame()
	
	if perm == True:
		Out['Qn'] = (-rho0*U0[0]+surf['rho']*(surf['u1']))*pre['n1'] + (-rho0*U0[1]+surf['rho']*(surf['u2']))*pre['n2'] + (-rho0*U0[2]+surf['rho']*(surf['u3']))*pre['n3']
		L1 = surf['p']*pre['n1'] + surf['rho']*(surf['u1']-U0[0])*((surf['u1'])*pre['n1']+(surf['u2'])*pre['n2']+(surf['u3'])*pre['n3'])
		L2 = surf['p']*pre['n2'] + surf['rho']*(surf['u2']-U0[1])*((surf['u1'])*pre['n1']+(surf['u2'])*pre['n2']+(surf['u3'])*pre['n3'])
		L3 = surf['p']*pre['n3'] + surf['rho']*(surf['u3']-U0[2])*((surf['u1'])*pre['n1']+(surf['u2'])*pre['n2']+(surf['u3'])*pre['n3'])
		
	else:
		Out['Qn'] = (-rho0*U0[0])*pre['n1'] + (-rho0*U0[1])*pre['n2'] + (-rho0*U0[2])*pre['n3']
		L1 = surf['p']*pre['n1']
		L2 = surf['p']*pre['n2']
		L3 = surf['p']*pre['n3']	
	
	Out['Lm'] = -L1*Ma[0] - L2*Ma[1] - L3*Ma[2]
	Out['Lr'] = L1*pre['r1'] + L2*pre['r2'] + L3*pre['r3']	
	
	return Out

#Parallel Implementation
def Parallel_source(surf_file : str, pre, p0, rho0, c0, Ma, f, perm):

	if perm == True:
		surf = pd.read_csv(surf_file, usecols = range(8,14), names = ['rho','u1','u2','u3','T','p'])
		read_time = time()
	else:
		surf = pd.read_csv(surf_file, usecols = range(13,14), names = ['p'])
		read_time = time()
	
	pre = pre[['n1','n2','n3','r1','r2','r3']].to_numpy()
	out = np.zeros([len(pre),3])
	
	surf = surf[f]
	surf.reset_index(drop=True)
	U0 = c0*Ma
	surf['p'] = surf['p']-p0
	surf = surf.to_numpy()
	
	ave, res = divmod(pre[:,0].size, nproc)
	c = [ave + 1 if f < res else ave for f in range(nproc)]
	c = np.array(c)
	index0 = [sum(c[:i]) for i in range(len(c))]
	
	preS = [pre[index0[i]:index0[i]+c[i],:] for i in range(nproc)]
	surfS = [surf[index0[i]:index0[i]+c[i],:] for i in range(nproc)]
	outS = [out[index0[i]:index0[i]+c[i],:] for i in range(nproc)]
	rho0S = [rho0[index0[i]:index0[i]+c[i]] for i in range(nproc)]
	preS = comm.scatter(preS, root=0)
	surfS = comm.scatter(surfS, root=0)
	outS = comm.scatter(outS, root=0)
	rho0S = comm.scatter(rho0S, root=0)
	
	U0 = comm.bcast(U0, root=0)
	perm = comm.bcast(perm, root=0)
	Ma = comm.bcast(Ma, root=0)
    	
	
	if perm == True:
		outS[:,0] = (-rho0S*U0[0]+surfS[:,0]*(surfS[:,1]))*preS[:,0] + (-rho0S*U0[1]+surfS[:,0]*(surfS[:,2]))*preS[:,1] + (-rho0S*U0[2]+surfS[:,0]*(surfS[:,3]))*preS[:,2]
		L1 = surfS[:,5]*preS[:,0] + surfS[:,0]*(surfS[:,1]-U0[0])*((surfS[:,1])*preS[:,0]+(surfS[:,2])*preS[:,1]+(surfS[:,3])*preS[:,2])
		L2 = surfS[:,5]*preS[:,1] + surfS[:,0]*(surfS[:,2]-U0[1])*((surfS[:,1])*preS[:,0]+(surfS[:,2])*preS[:,1]+(surfS[:,3])*preS[:,2])
		L3 = surfS[:,5]*preS[:,2] + surfS[:,0]*(surfS[:,3]-U0[2])*((surfS[:,1])*preS[:,0]+(surfS[:,2])*preS[:,1]+(surfS[:,3])*preS[:,2])
		
	else:
		outS[:,0] = (-rho0S*U0[0])*preS[:,0] + (-rho0S*U0[1])*preS[:,1] + (-rho0S*U0[2])*preS[:,2]
		L1 = surfS[:,0]*preS[:,0]
		L2 = surfS[:,0]*preS[:,1]
		L3 = surfS[:,0]*preS[:,2]	
	
	outS[:,1] = -L1*Ma[0] - L2*Ma[1] - L3*Ma[2]
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
def stationary_serial(surf_file : str,  out_file : str, obs_loc : list, t_src : list, Ma : list, perm : bool, write : bool = True, Ta : float = 298, gamma : float = 1.4, MW : float = 28.97):
    	
    	Runiv = 8.314 #Universal gas constant in J/mol . K
    	Ma = np.array(Ma)
    	t_src = np.array(t_src)
    	dt = t_src[1]-t_src[0]
    	c0 = np.sqrt(gamma*Runiv*1e3*Ta/MW)

    	#Preprocessing
    	df_pre = pd.read_csv(surf_file+'0.csv', usecols = range(7), names = ['y1','y2','y3','n1','n2','n3','dS'])
    	filt = df_pre['dS']!=0 #key to Filter rows with on-zero area
    	df_pre = df_pre[filt]
    	df_pre.reset_index(drop=True)
    	
    	
    	beta = np.sqrt(1-Ma[0]**2-Ma[1]**2-Ma[2]**2)
    	
    	p_mean = pd.read_csv(surf_file+'Avg.csv', usecols = range(13,14), names = ['p'])
    	p_mean = p_mean[filt].reset_index(drop=True)
    	rho_mean = pd.read_csv(surf_file+'Avg.csv', usecols = range(8,9), names = ['rho'])
    	rho_mean = rho_mean[filt].reset_index(drop=True)	
    	p0 = p_mean.to_numpy()[:,0]
    	rho0 = rho_mean.to_numpy()[:,0]
    	
    	for idx, xo in enumerate(obs_loc):
    		
    		#calculation of time independent quantities
    		Mr0 = Ma[0]*(xo[0]-df_pre['y1'])+Ma[1]*(xo[1]-df_pre['y2'])+Ma[2]*(xo[2]-df_pre['y3'])
    		R0 = np.sqrt((xo[0]-df_pre['y1'])**2+(xo[1]-df_pre['y2'])**2+(xo[2]-df_pre['y3'])**2)
    		
    		# Calculate R - effective acoustic distance
    		Rstar = np.sqrt(Mr0**2+(beta*R0)**2)
    		R = (-Mr0+Rstar)/(beta**2)
    	
    		# Radiation vector
    		df_pre['r1'] = (-Ma[0]*R + (xo[0]-df_pre['y1']))/R
    		df_pre['r2'] = (-Ma[1]*R + (xo[1]-df_pre['y2']))/R
    		df_pre['r3'] = (-Ma[2]*R + (xo[2]-df_pre['y3']))/R
    		Mr = -Ma[0]*df_pre['r1'] -Ma[1]*df_pre['r2'] -Ma[2]*df_pre['r3'] 
    		
    		tau = np.array(R/c0) #travelling time of sound from all sources
    		t_o = t_src+min(tau) #observer times 
    		tau_star = tau-min(tau)
    		w = (tau_star%dt)/dt
    		j_star = np.array([int(k//dt) for k in tau_star])
    		
    		t_range = [int((max(tau)-min(tau))//dt)+2,len(t_o)-1]
    		p_key = np.zeros_like(t_o)
    		p_key[t_range[0]:t_range[1]] = 1
    		
    		
    		D = (max(j_star)-1)*(max(j_star)>1) #number of void elements to be added at end for satisfying j_adv within range
    		p_acous = np.zeros(len(t_o)+D)
    		count = np.zeros(len(t_o)+D)
    		
    		src_t0 = Serial_source(surf_file+'0.csv', df_pre, p0, rho0, c0, Ma, filt, perm)
    		src_t1 = Serial_source(surf_file+'1.csv', df_pre, p0, rho0, c0, Ma, filt, perm)
    		src_t2 = Serial_source(surf_file+'2.csv', df_pre, p0, rho0, c0, Ma, filt, perm)
    		
    		
    		for j in range(1,len(t_src)-2):
    			j_adv = j+j_star+1 #advanced time step
    			j_cond = (j_adv >= t_range[0])*(j_adv < t_range[1])
    			
    			p_act =np.zeros(max(j_star)+1)
    			n_elm = np.zeros(max(j_star)+1)
    			src_t3 = Serial_source(surf_file+str(j+2)+'.csv', df_pre, p0, rho0, c0, Ma, filt, perm)
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
    			Qn = cubicSpline(w,src_t0['Qn'],src_t1['Qn'],src_t2['Qn'],src_t3['Qn'])
    			Qndot = (1-w)*Qndot2+w*Qndot1
    			Lr = cubicSpline(w,src_t0['Lr'],src_t1['Lr'],src_t2['Lr'],src_t3['Lr'])
    			Lrdot = (1-w)*Lrdot2+w*Lrdot1
    			Lm = cubicSpline(w,src_t0['Lm'],src_t1['Lm'],src_t2['Lm'],src_t3['Lm'])
    			
    			pt1 = (Qndot/(R*(1-Mr)**2))*df_pre['dS']
    			pt2 = ((Qn*c0*(Mr-sum(Ma**2)))/(R**2*(1-Mr)**3))*df_pre['dS']
    			# Thickness component
    			pt = (pt1 + pt2)/(4*np.pi)
    			
    			pq1 =(1/c0)*(Lrdot/(R*(1-Mr)**2))*df_pre['dS']
    			pq2 = ((Lr-Lm)/(R**2*(1-Mr)**2))*df_pre['dS']
    			pq3 = ((Lr*(Mr-sum(Ma**2)))/(R**2*(1-Mr)**3))*df_pre['dS']
    			
    			# Loading component
    			pq = (pq1+pq2+pq3)/(4*np.pi)
    			p = pt+pq
    			p *= j_cond
    			
    			
    			for i in range(len(j_star)):
    				p_act[j_star[i]] += p.iloc[i]
    				n_elm[j_star[i]] += 1*j_cond[i]
    				
    			p_acous[min(j_adv):max(j_adv)+1] += p_act
    			count[min(j_adv):max(j_adv)+1] += n_elm 
    			
    			src_t0 = src_t1.copy()
    			src_t1 = src_t2.copy()
    			src_t2 = src_t3.copy()
    		
    		
    		fig, ax = plt.subplots( nrows=1, ncols=1, figsize = [12,8] )  # create figure & 1 axis
    		ax.plot(t_o[t_range[0]:t_range[1]], p_acous[t_range[0]:t_range[1]],'b')
    		plt.title('Pressure time history at location '+str(xo))
    		ax.set_xlabel('time (sec)')
    		ax.set_ylabel("$p'$ (Pa)")
    		fig.savefig(out_file + str(idx)+ '.png')   # save the figure to file
    		plt.close(fig) 
    		if write :
    			p_df = pd.DataFrame({"t_o": t_o[t_range[0]:t_range[1]], "p'": p_acous[t_range[0]:t_range[1]]})
    			p_df.to_csv(out_file + str(idx)+ '.csv', index=False)
    			print("Far-field acoustic pressure for location " + str(xo) + " has been computed successfully. Output CSV file printed as " + out_file  + str(idx) +  ".csv.")
    	if write:
    		return "All calculations successfully completed! Far-field acoustic pressure for " + str(len(obs_loc)) + " observer location(s) saved to corresponding PNG images and CSV file(s)"
    	else:
    		return "All calculations successfully completed! Far-field acoustic pressure for " + str(len(obs_loc)) + " observer location(s) saved to corresponding PNG images "

#Parallel Implementation
def stationary_parallel(surf_file : str,  out_file : str, obs_loc : list, t_src : list, Ma : list, perm : bool, write : bool = True, Ta : float = 298, gamma : float = 1.4, MW : float = 28.97):

	
    	Runiv = 8.314 #Universal gas constant in J/mol . K
    	Ma = np.array(Ma)
    	t_src = np.array(t_src)
    	dt = t_src[1]-t_src[0]
    	c0 = np.sqrt(gamma*Runiv*1e3*Ta/MW)
    	
    	#Preprocessing
    	df_pre = pd.read_csv(surf_file+'0.csv', usecols = range(7), names = ['y1','y2','y3','n1','n2','n3','dS'])
    	filt = df_pre['dS']!=0 #key to Filter rows with on-zero area
    	df_pre = df_pre[filt]
    	df_pre.reset_index(drop=True)
    	
    	
    	beta = np.sqrt(1-Ma[0]**2-Ma[1]**2-Ma[2]**2)
    	
    	p_mean = pd.read_csv(surf_file+'Avg.csv', usecols = range(13,14), names = ['p'])
    	p_mean = p_mean[filt].reset_index(drop=True)
    	rho_mean = pd.read_csv(surf_file+'Avg.csv', usecols = range(8,9), names = ['rho'])
    	rho_mean = rho_mean[filt].reset_index(drop=True)	
    	p0 = p_mean.to_numpy()[:,0]
    	rho0 = rho_mean.to_numpy()[:,0]
    	
    	for idx, xo in enumerate(obs_loc):
    		
    		#calculation of time independent quantities
    		Mr0 = Ma[0]*(xo[0]-df_pre['y1'])+Ma[1]*(xo[1]-df_pre['y2'])+Ma[2]*(xo[2]-df_pre['y3'])
    		R0 = np.sqrt((xo[0]-df_pre['y1'])**2+(xo[1]-df_pre['y2'])**2+(xo[2]-df_pre['y3'])**2)
    		
    		# Calculate R - effective acoustic distance
    		Rstar = np.sqrt(Mr0**2+(beta*R0)**2)
    		R = (-Mr0+Rstar)/(beta**2)
    	
    		# Radiation vector
    		df_pre['r1'] = (-Ma[0]*R + (xo[0]-df_pre['y1']))/R
    		df_pre['r2'] = (-Ma[1]*R + (xo[1]-df_pre['y2']))/R
    		df_pre['r3'] = (-Ma[2]*R + (xo[2]-df_pre['y3']))/R
    		Mr = -Ma[0]*df_pre['r1'] -Ma[1]*df_pre['r2'] -Ma[2]*df_pre['r3'] 
    		
    		tau = np.array(R/c0) #travelling time of sound from all sources
    		t_o = t_src+min(tau) #observer times 
    		tau_star = tau-min(tau)
    		w = (tau_star%dt)/dt
    		j_star = np.array([int(k//dt) for k in tau_star])
    		
    		t_range = [int((max(tau)-min(tau))//dt)+2,len(t_o)-1]
    		p_key = np.zeros_like(t_o)
    		p_key[t_range[0]:t_range[1]] = 1
    		
    		
    		D = (max(j_star)-1)*(max(j_star)>1) #number of void elements to be added at end for satisfying j_adv within range
    		p_acous = np.zeros(len(t_o)+D)
    		count = np.zeros(len(t_o)+D)
    		
    		src_t0 = Parallel_source(surf_file+'0.csv', df_pre, p0, rho0, c0, Ma, filt, perm)
    		src_t1 = Parallel_source(surf_file+'1.csv', df_pre, p0, rho0, c0, Ma, filt, perm)
    		src_t2 = Parallel_source(surf_file+'2.csv', df_pre, p0, rho0, c0, Ma, filt, perm)
    		
    		
    		for j in range(1,len(t_src)-2):
    			j_adv = j+j_star+1 #advanced time step
    			j_cond = (j_adv >= t_range[0])*(j_adv < t_range[1])
    			
    			p_act =np.zeros(max(j_star)+1)
    			n_elm = np.zeros(max(j_star)+1)
    			src_t3 = Parallel_source(surf_file+str(j+2)+'.csv', df_pre, p0, rho0, c0, Ma, filt, perm)
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
    			Qn = cubicSpline(w,src_t0['Qn'],src_t1['Qn'],src_t2['Qn'],src_t3['Qn'])
    			Qndot = (1-w)*Qndot2+w*Qndot1
    			Lr = cubicSpline(w,src_t0['Lr'],src_t1['Lr'],src_t2['Lr'],src_t3['Lr'])
    			Lrdot = (1-w)*Lrdot2+w*Lrdot1
    			Lm = cubicSpline(w,src_t0['Lm'],src_t1['Lm'],src_t2['Lm'],src_t3['Lm'])
    			
    			pt1 = (Qndot/(R*(1-Mr)**2))*df_pre['dS']
    			pt2 = ((Qn*c0*(Mr-sum(Ma**2)))/(R**2*(1-Mr)**3))*df_pre['dS']
    			# Thickness component
    			pt = (pt1 + pt2)/(4*np.pi)
    			
    			pq1 =(1/c0)*(Lrdot/(R*(1-Mr)**2))*df_pre['dS']
    			pq2 = ((Lr-Lm)/(R**2*(1-Mr)**2))*df_pre['dS']
    			pq3 = ((Lr*(Mr-sum(Ma**2)))/(R**2*(1-Mr)**3))*df_pre['dS']
    			
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
    			
    			for i in range(len(Jsplit)):
    				
    				p_act[Jsplit[i]] += Psplit[i]
    				n_elm[Jsplit[i]] += 1*cond[i]
    			
    			
    			p_act = comm.gather(p_act, root=0)
    			n_elm = comm.gather(n_elm, root=0)
    			
    			
    			if rank == 0:
    				
    				p_acous[min(j_adv):max(j_adv)+1] += sum(p_act) 
    				count[min(j_adv):max(j_adv)+1] += sum(n_elm) 

    				src_t0 = src_t1.copy()
    				src_t1 = src_t2.copy()
    				src_t2 = src_t3.copy()
    		
    		if rank == 0:
    			fig, ax = plt.subplots( nrows=1, ncols=1, figsize = [12,8]  )  # create figure & 1 axis
    			ax.plot(t_o[t_range[0]:t_range[1]], p_acous[t_range[0]:t_range[1]],'b')
    			plt.title('Pressure time history at location '+str(xo))
    			ax.set_xlabel('time (sec)')
    			ax.set_ylabel("$p'$ (Pa)")
    			fig.savefig(out_file + str(idx)+ '.png')   # save the figure to file
    			plt.close(fig) 
    			if write:
    				p_df = pd.DataFrame({"t_o": t_o[t_range[0]:t_range[1]], "p'": p_acous[t_range[0]:t_range[1]]})
    				p_df.to_csv(out_file + str(idx)+ '.csv', index=False)
    				print("Far-field acoustic pressure for location " + str(xo) + " has been computed successfully. Output CSV file printed as " + out_file  + str(idx) +  ".csv.")
    	if rank == 0 :
    		if write:
    			return "All calculations successfully completed! Far-field acoustic pressure for " + str(len(obs_loc)) + " observer location(s) saved to corresponding PNG images and CSV file(s)"
    		else:
    			return "All calculations successfully completed! Far-field acoustic pressure for " + str(len(obs_loc)) + " observer location(s) saved to corresponding PNG images "
    		


    		

