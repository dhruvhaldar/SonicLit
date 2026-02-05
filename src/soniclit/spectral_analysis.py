"""
Function library to calculate the power spectra of an independant or a pair of input stationary signals, using common methods including simple FFT, Welch periodogram, etc.

Check out this `StackExchange DSP forum question <https://dsp.stackexchange.com/questions/48216/understanding-fft-fft-size-and-bins>`_ 
for a brief explanation on signal processing methods. You will be able to navigate from there
in case you would like to understand Digital Signal Processing further.

Notes
------
- When you use this module, keep in mind the required scaling of your spectrum. This may have a very large influence on the levels of your spectra
- Performing a Fourier transform on discrete data will give the power contained in discrete frequency 'bins'. The levels of your spectra will depend on how they are scaled. The term 'Power Spectral Density' refers to a power spectrum that has been normalised with the bin size, and hence has the units Pa\ :sup:`2`/Hz. The 'Power Spectrum' has the units Pa\ :sup:`2`.
- The decibel (dB) scale is obtained by normalising the power spectra by a reference pressure. For air, this reference is almost universally considered to be 20 microPascals.

"""

import os
import numpy as np
import scipy.signal as signal


def next_greater_power_of_2(num : int):
    """
    Function to compute the next greater power of 2 for a given input.

    Parameters
    ----------
    num : int
        Input number for which the next greater power of 2 is computed.

    Returns
    -------
    int
        Number which is the next greater power of 2.

    Example
    --------
    >>> next_greater_power_of_2(5)
    
    """
    return 2**(num-1).bit_length()


def sampling_freq(time):
    """
    Function to compute the sampling frequency of an input time series.
    

    Parameters
    ----------
    time : array_like
        Uniformly spaced discrete time series in SI units.

    Returns
    -------
    fs : int
        Sampling frequncy of the input signal, in Hz.

    Example
    --------
    >>> time_series = np.linspace(0, 0.3, 1e5) # time series with 1e5 samples
    >>> fs = sampling_freq(time_series) # an integer value is returned, which we'd like to store

    
    """
    fs = int(1/(time[-1] - time[-2]))
    return fs
 
    
def fft_spectrum(time, sig, save_output : bool = False, out_dir : str = "", db_scale : bool = False, scale_spectrum : bool = True, scale_freq : bool = False):
    """
    Calculates the power spectrum of an input time-domain signal by taking the FFT of the signal and multiplying with its complex conjugate.

    Parameters
    ----------
    time : array_like
        Uniformly spaced discrete time series, in SI units.
    sig : array_like
        Uniformly spaced time-domain signal of physical quantity, in SI units.
    save_output : bool, optional
        Boolean argument to specify whether output CSV file file must be written or not. The default is False.
    out_dir : str, optional (needed only if save_output is `True`)
        Relative path to directory where the results of this calculation will be written as a CSV file. The default is NULL.
    db_scale : bool, optional
        Convert power spectrum to decibel scale or leave unscaled. `True` converts to decibel scale. The default is `False`.
    scale_spectrum : bool, optional
        Scale power spectrum with the signal length. The default is True.
    scale_freq : bool, optional
        Scale power spectrum with the bin size. The default is False.


    Returns
    -------
    freq : array_like
        Discrete frequency values centered on FFT bins, in Hz.
    df : float
        FFT bin size, in Hz.
    psd : array_like
        Power spectrum of the input signal, in Pa\ :sup:`2`/Hz (unscaled) or dB/Hz (scaled w.r.t. reference pressure).

    Notes
    -----
    - As the input is most commonly going to be from probe data written during simulation, this function assumes a real-valued input, and uses the  `numpy.fft.rfft` and `numpy.fft.rfftfreq` functions to calculate the frequency and power components of the signal.
    - The power spectrum is scaled by the length of the signal. If you require an unscaled spectrum, set `scale = False`.
    
    Examples
    --------
    >>> f_fft, df, psd_fft = fft_spectrum(time, sig)
    
    >>> f_fft, df, psd_fft_unscaled = fft_spectrum(time, sig,
                                                                scale_spectrum=False)
    
    >>> f_fft, df, psd_fft_unscaled = fft_spectrum(time, sig, save_output = True,
                                                                 out_dir = "./results/farfield")

    """
    
    fs = sampling_freq(time)
    
    freq = np.fft.rfftfreq(len(time), 1/fs) # discrete central frequencies of the FFT bins
    
    df = fs/len(time)   # bin size
    
    sig = sig - np.mean(sig) # mean-removed part of the signal
    
    sig_fft = np.fft.rfft(sig) # Fourier-transformed signal, real part only
    
    if scale_spectrum == True:
        psd = abs(sig_fft*np.conjugate(sig_fft))/(fs*len(sig))
    else:
        psd = abs(sig_fft*np.conjugate(sig_fft))
    
    if scale_freq == True:
        psd = psd/df
    
    if db_scale == True:
        psd = 10.*np.log10(psd/4e-10)
        #return freq, df, psd
    
    if save_output == True:
        os.makedirs(out_dir, exist_ok=True)
        data = np.column_stack((freq, psd))
        np.savetxt(out_dir+"/fft_spectrum.csv", data, fmt="%.8e", delimiter=",", header="Freq, PSD (Plain FFT)", comments="#")
    
    return freq, df, psd


def welch_spectrum(time, sig, save_output : bool = False, out_dir : str = "", window = 'hann', chunks : int = 4, overlap : float = 0.5,
                   db_scale : bool = False, scale_freq : bool = True):
    """
    Calculates the power spectrum of an input signal using Welch's periodogram method. Unlike the plain FFT method, the signal is cut into chunks for smoothing and faster processing of the PSD.

    Parameters
    ----------
    time : array_like
        Uniformly spaced discrete time series, in SI units.
    sig : array_like
        Uniformly spaced time-domain signal of physical quantity, in SI units.
    save_output : bool, optional
        Boolean argument to specify whether output CSV file file must be written or not. The default is False.
    out_dir : str, optional (needed only if save_output is `True`)
        Relative path to directory where the results of this calculation will be written as a CSV file. The default is NULL.
    window : str or tuple, optional
        The type of windowing. For available windows, check the `SciPy documentation page for the Welch function <https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html>`_. The default is 'hann'.
    chunks : int, optional
        Number of chunks to cut the signal into. FFT and windowing is then performed on each chunk, and the chunks are then averaged to get the PSD. The default is 4.
    overlap : float, optional
        The amount of overlap to be used for the windowing operation (specified as a fraction, so a 75% overlap can be specified as `overlap=0.75`). The default is 0.5.
    db_scale : bool, optional
        Convert power spectrum to decibel scale or leave unscaled. `True` converts to decibel scale. The default is `False`.
    scale_freq : bool, optional
        Scale power spectrum with the bin size. The default is True.
    
    Returns
    -------
    freq : array_like
        Discrete frequency values centered on FFT bins, in Hz.
    df : float
        FFT bin size, in Hz.
    psd : array_like
        Power spectrum of the input signal, in Pa\ :sup:`2`/Hz (scaled) or dB/Hz (scaled w.r.t. reference pressure).
    
    Notes
    -----
    - The default behaviour is to use Hanning windowing with 50% overlap.
    - In most cases, the PSD is reported in the units Pa\ :sup:`2`/Hz, which is the correct form when talking about 'Power Spectral DENSITY'. In case you wish to obtain the 'Power spectrum' and not the power spectral density, pass `scale=False` as an argument during function call.
    
    Examples
    --------
    >>> f_welch, df_welch, psd_welch = welch_spectrum(time, sig)
    
    >>> f_welch_75overlap, df_welch, psd_welch_75overlap = 
            welch_spectrum(time, sig, overlap=0.75)
    
    >>> f_welch_8chunks, df_welch, psd_welch_8chunks = 
            welch_spectrum(time, sig, overlap=0.5, chunks=8)
    
    >>> f_welch, df_welch, psd_welch_unscaled = 
            welch_spectrum(time, sig, scale_spectrum=False)
    
    >>> f_welch, df_welch, psd_welch_unscaled = 
            welch_spectrum(time, sig, save_output=True,
                           out_dir="./results/farfield", scale_spectrum=False)

    """
    
    fs = sampling_freq(time)
    
    nperseg = len(sig) // chunks
    
    nfft = next_greater_power_of_2(nperseg)
    
    df = fs/nfft
    
    if scale_freq == True:
        freq, psd = signal.welch(sig, fs, nperseg=nperseg, noverlap=overlap*nperseg, nfft=nfft,
                          window=window, return_onesided=True, detrend='constant', scaling='density', axis=-1)
    else:
        freq, psd = signal.welch(sig, fs, nperseg=nperseg, noverlap=overlap*nperseg, nfft=nfft,
                          window=window, return_onesided=True, detrend='constant', scaling='spectrum', axis=-1)
    
    
    if db_scale == True:
        psd = 10.*np.log10(psd/4e-10)
    
    if save_output == True:
        os.makedirs(out_dir, exist_ok=True)
        data = np.column_stack((freq, psd))
        np.savetxt(out_dir+"/welch_spectrum.csv", data, fmt="%.8e", delimiter=",", header="Freq, PSD (Welch)", comments="#")
    
    return freq, df, psd
        



def auto_corr(sig, save_output : bool = False, out_dir : str = "", normalised : bool = True):
    """
    Calculates the auto-correlation of a discrete time signal, i.e., the correlation of the signal with a copy of itself, using the SciPy toolbox.
    Whenever possible, an FFT-based calculation is performed because it is more efficient higher effiency. Check out `this <https://stackoverflow.com/questions/57804124/does-numpy-correlate-differ-from-scipy-signal-correlate-if-both-are-used-on-a-1d>`_ StackOverflow thread for some detail.

    Parameters
    ----------
    sig : array_like
        The time series or signal whose auto-correlation needs to be computed.
    save_output : bool, optional
        Boolean argument to specify whether output CSV file file must be written or not. The default is False.
    out_dir : str, optional (needed only if save_output is `True`)
        Relative path to directory where the results of this calculation will be written. The default is NULL.
    normalised : bool, optional
        Boolean argument to specify if a normlaised auto-correlation needs to be computed (see the `Wikipedia page <https://en.wikipedia.org/wiki/Autocorrelation>`_ for detail). The default is True.

    Returns
    -------
    acorr : array_like
        Auto-correlation of the signal.
    acorr_lags : array_like
        Array of lags used to compute the correlation.
    
    Examples
    -------
    >>> acorr, acorr_lags = auto_corr(pres_signal)
    
    >>> acorr, acorr_lags = auto_corr(pres_signal, save_output=True, out_dir="./results/nearfield_correlations")

    """
    sig = sig - np.mean(sig)
    
    acorr = signal.correlate(sig, sig, mode='full', method='auto')
    acorr = acorr[acorr.size//2:]

    if normalised == True:
        sig_var = np.var(sig)
        acorr = acorr / sig_var / len(sig)//2
    
    acorr_lags = signal.correlation_lags(len(sig), len(sig), mode='full')
    acorr_lags = acorr_lags[acorr_lags.size//2:]

    if save_output == True:
        os.makedirs(out_dir, exist_ok=True)
        #data = np.column_stack((freq, cpsd))
        np.savetxt(out_dir+"/auto_correlation.csv", acorr, fmt="%.8e", delimiter=",", header="Auto-correlation", comments="#")
    
    return acorr, acorr_lags


def cross_corr(sig1, sig2, mode : str = 'full', save_output : bool = False, out_dir : str = ""):
    """
    Calculates the cross-correlation of a pair of signals, using the SciPy toolkit.

    Parameters
    ----------
    sig1 : array_like
        Reference signal to correlate against.
    sig2 : array_like
        Signal which is to be correlated against the reference signal.
    mode : str
        String indicating the size of the output. Available options are `'full'`, `'valid'` or `'same'`. The default is `'full'`. For the details, refer to the `SciPy documentation page <https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.correlate.html>`_
    save_output : bool, optional
        Boolean argument to specify whether output CSV file file must be written or not. The default is False.
    out_dir : str, optional
        Relative path to directory where the results of this calculation will be written. The default is NULL.

    Returns
    -------
    xcorr : array_like
        Cross-correlation of signal2 with signal1.
    xcorr_lags : array_like
        Array of lags used to compute the correlation.
    
    Notes
    -----
    - The order in which the signal pair is specified can make a very big difference in the correlation curve. Always keep note of which signal is used as your reference.
    
    Examples
    -------
    >>> xcorr, xcorr_lags = cross_corr(pres_data_1, pres_data_2)
    
    >>> xcorr, xcorr_lags = cross_corr(pres_data_1, pres_data_2, save_output=True, out_dir="./results/nearfield_correlations")


    """
    sig1 = sig1 - np.mean(sig1)
    sig2 = sig2 - np.mean(sig2)
    
    xcorr = signal.correlate(sig1, sig2, mode=mode, method='auto')
    
    xcorr_lags = signal.correlation_lags(len(sig1), len(sig2), mode=mode)
    
    if save_output == True:
        os.makedirs(out_dir, exist_ok=True)
        #data = np.column_stack((freq, cpsd))
        np.savetxt(out_dir+"/cross_correlation.csv", xcorr, fmt="%.8e", delimiter=",", header="Cross-correlation", comments="#")
    
    return xcorr, xcorr_lags


def cross_spectrum(time1, sig1, time2, sig2, save_output : bool = False, out_dir : str = "", window = 'hann', chunks : int = 4, overlap : float = 0.5,
                   scale_freq : bool = True, db_scale : bool = False):
    """
    Calculates the Cross Power Spectrum of a pair of input signals using Welch's method. Principles of windowing and overlap are the same as the standard Welch function :func:`~spectral_analysis.welch_spectrum`.

    Parameters
    ----------
    time1 : array_like
        Uniformly spaced discrete time series of first signal, in SI units.
    sig1 : array_like
        Uniformly spaced time-domain signal of physical quantity of first signal, in SI units.
    time2 : array_like
        Uniformly spaced discrete time series of second signal, in SI units.
    sig2 : array_like
        Uniformly spaced time-domain signal of physical quantity of second signal, in SI units.
    save_output : bool, optional
        Boolean argument to specify whether output CSV file file must be written or not. The default is False.
    out_dir : str, optional (needed only if save_output is `True`)
        Relative path to directory where the results of this calculation will be written. The default is NULL.
    window : str or tuple, optional
        The type of windowing. For available windows, check the `SciPy documentation page for the Welch function <https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html>`_. The default is 'hann'.
    chunks : int, optional
        Number of chunks to cut the signal into. FFT and windowing is then performed on each chunk, and the chunks are then averaged to get the PSD. The default is 4.
    overlap : float, optional
        The amount of overlap to be used for the windowing operation (specified as a fraction, so a 75% overlap can be specified as `overlap=0.75`). The default is 0.5.
    db_scale : bool, optional
        Convert power spectrum to decibel scale or leave unscaled. `True` converts to decibel scale. The default is `False`.
    scale_freq : bool, optional
        Scale power spectrum with the bin size. The default is True.

    Raises
    ------
    ValueError
        When either the two signals do not have the same sampling frequency and/or the same signal length.

    Returns
    -------
    freq : array_like
        Discrete frequency values centered on FFT bins, in Hz.
    cpsd : array_like
        Cross power spectrum of the input signal pair, in Pa\ :sup:`2`/Hz (scaled) or dB/Hz (scaled w.r.t. reference pressure).
    
    Notes
    -----
    - The default behaviour is to use Hanning windowing with 50% overlap.
    
    
    Examples
    --------
    >>> f, cpsd = cross_spectrum(time1, signal1, time2, signal2)
    
    >>> f_75overlap, cpsd_75overlap = 
            cross_spectrum(time1, signal1, time2, signal2, overlap=0.75)
    
    >>> f_6chunks, cpsd_6chunks = 
            cross_spectrum(time1, signal1, time2, signal2, chunks=6)
    
    >>> f_unscaled, cpsd_unscaled = 
            cross_spectrum(time1, signal1, time2, signal2, scale_spectrum=False)
    
    >>> f, cpsd = 
            cross_spectrum(time1, signal1, time2, signal2, save_output=True,
                           out_dir="./results/nearfield", scale_spectrum=False, db_scale=False)

    """
    
    fs1 = sampling_freq(time1)
    fs2 = sampling_freq(time2)
    
    nperseg = len(sig1) // chunks
    
    nfft = next_greater_power_of_2(nperseg)
    
    #df = fs/nfft
    
    try:
        if fs1 != fs2:
            raise ValueError
    except:
        ValueError("The two signals don't have the same sampling frequency. Try again with the correct signal pair.")
        return
    
    try:
        if len(sig1) != len(sig2):
            raise ValueError
    except:
        ValueError("The two signals don't have the same length. Try again with the correct signal pair.")
        return
    
    
    if scale_freq == True:
        freq, cpsd = signal.csd(sig1, sig2, fs1, nperseg=nperseg, noverlap=overlap*nperseg, nfft=nfft,
                         window=window, return_onesided=True, detrend='constant', scaling='density', axis=-1)
    else:
        freq, cpsd = signal.csd(sig1, sig2, fs1, nperseg=nperseg, noverlap=overlap*nperseg, nfft=nfft,
                     window=window, return_onesided=True, detrend='constant', scaling='spectrum', axis=-1)
    
    if db_scale == True:
        cpsd = 10.*np.log10(cpsd/4e-10)
    
    if save_output == True:
        os.makedirs(out_dir, exist_ok=True)
        data = np.column_stack((freq, cpsd))
        np.savetxt(out_dir+"/cross_spectrum.csv", data, fmt="%.8e", delimiter=",", header="Freq, CPSD", comments="#")
    
    
    return freq, cpsd




def cross_spectrum_fft(time1, sig1, time2, sig2, save_output : bool = False, out_dir : str = "",
                       scale_spectrum : bool = True, scale_freq : bool = False, db_scale : bool = False):
    """
    Calculates the Cross Spectrum of a pair of signals using the FFT method and no windowing. The implementation follows the same principles as the :func:`~spectral_analysis.fft_spectrum` function.

    Parameters
    ----------
    time1 : array_like
        Uniformly spaced discrete time series of first signal, in SI units.
    sig1 : array_like
        Uniformly spaced time-domain signal of physical quantity of first signal, in SI units.
    time2 : array_like
        Uniformly spaced discrete time series of second signal, in SI units.
    sig2 : array_like
        Uniformly spaced time-domain signal of physical quantity of second signal, in SI units.
    save_output : bool, optional
        Boolean argument to specify whether output CSV file file must be written or not. The default is False.
    out_dir : str, optional (needed only if save_output is `True`)
        Relative path to directory where the results of this calculation will be written. The default is NULL.
    scale_spectrum : bool, optional
        Scale power spectrum with the signal length. The default is True.
    scale_freq : bool, optional
        Scale power spectrum with the bin size. The default is False.
    db_scale : bool, optional
        Convert power spectrum to decibel scale or leave unscaled. `True` converts to decibel scale. The default is `False`.

    Raises
    ------
    ValueError
        When either the two signals do not have the same sampling frequency and/or the same signal length.

    Returns
    -------
    freq1 : array_like
        Discrete frequency values centered on FFT bins, in Hz.
    cpsd : array_like
        Cross Power spectrum of the input signal pair, in Pa\ :sup:`2`/Hz (scaled) or dB/Hz (scaled w.r.t. reference pressure).
    
    Examples
    --------
    >>> f, cpsd = cross_spectrum_fft(time1, signal1, time2, signal2)
    
    >>> f_unscaled, cpsd_unscaled = 
            cross_spectrum_fft(time1, signal1, time2, signal2, scale_spectrum=False)
    
    >>> f, cpsd = 
            cross_spectrum_fft(time1, signal1, time2, signal2, save_output=True,
                           out_dir="./results/nearfield", scale_spectrum=False, db_scale=False)


    """
    
    fs1 = sampling_freq(time1)
    fs2 = sampling_freq(time1)
    
    try:
        if fs1 != fs2:
            raise ValueError
    except:
        ValueError("The two signals don't have the same sampling frequency. Try again with the correct signal pair.")
        return
    
    try:
        if len(sig1) != len(sig2):
            raise ValueError
    except:
        ValueError("The two signals don't have the same length. Try again with the correct signal pair.")
        return
    
    freq1 = np.fft.rfftfreq(len(time1), 1/fs1) # discrete central frequencies of the FFT bins
    sig1 = sig1 - np.mean(sig1) # mean-removed part of the signal
    sig1_fft = np.fft.rfft(sig1) # Fourier-transformed signal, real part only
    
    #freq2 = np.fft.rfft(time2, 1/fs2) # discrete central frequencies of the FFT bins
    sig2 = sig2 - np.mean(sig2) # mean-removed part of the signal
    sig2_fft = np.fft.rfft(sig2)
    
    if scale_spectrum == True:
        cpsd = abs(sig1_fft*np.conjugate(sig2_fft))/(fs1*len(sig1))
    else:
        cpsd = abs(sig1_fft*np.conjugate(sig2_fft))
    
    if db_scale == True:
        cpsd = 10.*np.log10(cpsd/4e-10)
        
    if save_output == True:
        os.makedirs(out_dir, exist_ok=True)
        data = np.column_stack((freq1, cpsd))
        np.savetxt(out_dir+"/cross_spectrum_fft.csv", data, fmt="%.8e", delimiter=",", header="Freq, CPSD (Plain FFT)", comments="#")
    
    
    return freq1, cpsd





def coherence(time1, sig1, time2, sig2, save_output : bool = False, out_dir : str = "", window = 'hann', chunks : int = 4, overlap : float = 0.5):
    """
    Calculates the coherence between an input pair of time series using the Welch method to estimate the power and cross spectra. This method is based on the same principles as :func:`~spectral_analysis.welch_spectrum`.

    Parameters
    ----------
    time1 : array_like
        Uniformly spaced discrete time series of first signal, in SI units.
    sig1 : array_like
        Uniformly spaced time-domain signal of physical quantity of first signal, in SI units.
    time2 : array_like
        Uniformly spaced discrete time series of second signal, in SI units.
    sig2 : array_like
        Uniformly spaced time-domain signal of physical quantity of second signal, in SI units.
    save_output : bool, optional
        Boolean argument to specify whether output CSV file file must be written or not. The default is False.
    out_dir : str, optional (needed only if save_output is `True`)
        Relative path to directory where the results of this calculation will be written. The default is NULL.
    window : str or tuple, optional
        The type of windowing. For available windows, check the `SciPy documentation page for the Welch function <https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html>`_. The default is 'hann'.
    chunks : int, optional
        Number of chunks to cut the signal into. FFT and windowing is then performed on each chunk, and the chunks are then averaged to get the PSD. The default is 4.
    overlap : float, optional
        The amount of overlap to be used for the windowing operation (specified as a fraction, so a 75% overlap can be specified as `overlap=0.75`). The default is 0.5.
    
    Raises
    ------
    ValueError
        Raised when the two signals do not have the same sampling frequency.

    Returns
    -------
    freq : array_like
        Discrete frequency values centered on FFT bins, in Hz.
    cxy : array_like
        Coherence of the two signals as a function of frequency.
    
    Notes
    -----
    - The default behaviour is to use Hanning windowing with 50% overlap.
    
    
    Examples
    --------
    >>> f, cxy = coherence(time1, signal1, time2, signal2)

    """
    fs1 = sampling_freq(time1)
    fs2 = sampling_freq(time2)
    
    try:
        if fs1 != fs2:
            raise ValueError
    except:
        ValueError("The two signals don't have the same sampling frequency. Try again with the correct signal pair.")
        return
    
    nperseg = len(sig1) // chunks
    
    nfft = next_greater_power_of_2(nperseg)
    
    
    freq, cxy = signal.coherence(sig1, sig2, fs1, nperseg=nperseg, noverlap=overlap*nperseg, nfft=nfft,
                     window=window, detrend='constant', axis=-1)
    
    #if save_output == True:
    #    os.makedirs(out_dir, exist_ok=True)
    #    data = np.column_stack((freq, cxy))
    #    np.savetxt(out_dir+"/signal_coherence.csv", data, fmt="%.8e", delimiter=",", header="Freq, Coherence", comments="#")
    
    return freq, cxy


def coherence_fft(time1, sig1, time2, sig2, save_output : bool = False, out_dir : str = ""):
    """
    Calculates the coherence between an input pair of time series using FFtTs of the individual power spectra and the cross spectra. This method is based on the same principles as :func:`~spectral_analysis.fft_spectrum`.

    Parameters
    ----------
    time1 : array_like
        Uniformly spaced discrete time series of first signal, in SI units.
    sig1 : array_like
        Uniformly spaced time-domain signal of physical quantity of first signal, in SI units.
    time2 : array_like
        Uniformly spaced discrete time series of second signal, in SI units.
    sig2 : array_like
        Uniformly spaced time-domain signal of physical quantity of second signal, in SI units.
    save_output : bool, optional
        Boolean argument to specify whether output CSV file file must be written or not. The default is False.
    out_dir : str, optional (needed only if save_output is `True`)
        Relative path to directory where the results of this calculation will be written. The default is NULL.

    Raises
    ------
    ValueError
        Raised when the two signals do not have the same sampling frequency.

    Returns
    -------
    freq1 : array_like
        Discrete frequency values centered on FFT bins, in Hz.
    cxy : array_like
        Coherence of the two signals as a function of frequency.
    
    Examples
    --------
    >>> f, cxy = coherence_fft(time1, signal1, time2, signal2)

    """
    
    fs1 = sampling_freq(time1)
    fs2 = sampling_freq(time2)
    
    try:
        if fs1 != fs2:
            raise ValueError
    except:
        ValueError("The two signals don't have the same sampling frequency. Try again with the correct signal pair.")
        return
    
    freq1, df1, psd1 = fft_spectrum(time1, sig1)
    freq2, df2, psd2 = fft_spectrum(time2, sig2)
    
    
    cfreq, cpsd = cross_spectrum_fft(time1, sig1, time2, sig2)
    
    cxy = cpsd**2/(psd1*psd2)
    
    #if save_output == True:
    #    os.makedirs(out_dir, exist_ok=True)
    #    data = np.column_stack((freq1, cxy))
    #    np.savetxt(out_dir+"/signal_coherence_fft.csv", data, fmt="%.8e", delimiter=",", header="Freq, Coherence", comments="#")
    
    return freq1, cxy


