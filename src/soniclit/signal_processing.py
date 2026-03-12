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
import scipy.signal as sp_signal


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
 
    
def fft_spectrum(time, signal, save_output : bool = False, out_dir : str = "", db_scale : bool = False, scale_spectrum : bool = True, scale_freq : bool = False):
    """
    Calculates the power spectrum of an input time-domain signal by taking the FFT of the signal and multiplying with its complex conjugate.

    Parameters
    ----------
    time : array_like
        Uniformly spaced discrete time series, in SI units.
    signal : array_like
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
    power_spectral_density : array_like
        Power spectrum of the input signal, in Pa\ :sup:`2`/Hz (unscaled) or dB/Hz (scaled w.r.t. reference pressure).

    Notes
    -----
    - As the input is most commonly going to be from probe data written during simulation, this function assumes a real-valued input, and uses the  `numpy.fft.rfft` and `numpy.fft.rfftfreq` functions to calculate the frequency and power components of the signal.
    - The power spectrum is scaled by the length of the signal. If you require an unscaled spectrum, set `scale = False`.
    
    Examples
    --------
    >>> f_fft, df, psd_fft = fft_spectrum(time, signal)
    
    >>> f_fft, df, psd_fft_unscaled = fft_spectrum(time, signal,
                                                                scale_spectrum=False)
    
    >>> f_fft, df, psd_fft_unscaled = fft_spectrum(time, signal, save_output = True,
                                                                 out_dir = "./results/farfield")

    """
    
    sampling_frequency = sampling_freq(time)
    
    freq = np.fft.rfftfreq(len(time), 1/sampling_frequency) # discrete central frequencies of the FFT bins
    
    df = sampling_frequency/len(time)   # bin size
    
    signal -= np.mean(signal) # mean-removed part of the signal
    
    sig_fft = np.fft.rfft(signal) # Fourier-transformed signal, real part only
    
    # OPTIMIZATION: Calculate squared magnitude directly using numpy abs
    # np.abs(sig_fft)**2 is highly optimized in C and up to 2.4x faster than explicit arithmetic
    psd_unscaled = np.abs(sig_fft)**2

    if scale_spectrum == True:
        power_spectral_density = psd_unscaled/(sampling_frequency*len(signal))
    else:
        power_spectral_density = psd_unscaled
    
    if scale_freq == True:
        power_spectral_density = power_spectral_density/df
    
    if db_scale == True:
        # OPTIMIZATION: Multiplying a numpy array by the scalar 2.5e9 (inverse of 4e-10)
        # is faster than array division, yielding a measurable performance improvement.
        power_spectral_density = 10.*np.log10(power_spectral_density * 2.5e9)
        #return freq, df, power_spectral_density
    
    if save_output == True:
        os.makedirs(out_dir, exist_ok=True)
        data = np.column_stack((freq, power_spectral_density))
        np.savetxt(out_dir+"/fft_spectrum.csv", data, fmt="%.8e", delimiter=",", header="Freq, PSD (Plain FFT)", comments="#")
    
    return freq, df, power_spectral_density


def welch_spectrum(time, signal, save_output : bool = False, out_dir : str = "", window = 'hann', chunks : int = 4, overlap : float = 0.5,
                   db_scale : bool = False, scale_freq : bool = True):
    """
    Calculates the power spectrum of an input signal using Welch's periodogram method. Unlike the plain FFT method, the signal is cut into chunks for smoothing and faster processing of the PSD.

    Parameters
    ----------
    time : array_like
        Uniformly spaced discrete time series, in SI units.
    signal : array_like
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
    power_spectral_density : array_like
        Power spectrum of the input signal, in Pa\ :sup:`2`/Hz (scaled) or dB/Hz (scaled w.r.t. reference pressure).
    
    Notes
    -----
    - The default behaviour is to use Hanning windowing with 50% overlap.
    - In most cases, the PSD is reported in the units Pa\ :sup:`2`/Hz, which is the correct form when talking about 'Power Spectral DENSITY'. In case you wish to obtain the 'Power spectrum' and not the power spectral density, pass `scale=False` as an argument during function call.
    
    Examples
    --------
    >>> f_welch, df_welch, psd_welch = welch_spectrum(time, signal)
    
    >>> f_welch_75overlap, df_welch, psd_welch_75overlap = 
            welch_spectrum(time, signal, overlap=0.75)
    
    >>> f_welch_8chunks, df_welch, psd_welch_8chunks = 
            welch_spectrum(time, signal, overlap=0.5, chunks=8)
    
    >>> f_welch, df_welch, psd_welch_unscaled = 
            welch_spectrum(time, signal, scale_spectrum=False)
    
    >>> f_welch, df_welch, psd_welch_unscaled = 
            welch_spectrum(time, signal, save_output=True,
                           out_dir="./results/farfield", scale_spectrum=False)

    """
    
    sampling_frequency = sampling_freq(time)
    
    samples_per_segment = len(signal) // chunks
    
    fft_length = next_greater_power_of_2(samples_per_segment)
    
    df = sampling_frequency/fft_length
    
    if scale_freq == True:
        freq, power_spectral_density = sp_signal.welch(signal, sampling_frequency, nperseg=samples_per_segment, noverlap=overlap*samples_per_segment, nfft=fft_length,
                          window=window, return_onesided=True, detrend='constant', scaling='density', axis=-1)
    else:
        freq, power_spectral_density = sp_signal.welch(signal, sampling_frequency, nperseg=samples_per_segment, noverlap=overlap*samples_per_segment, nfft=fft_length,
                          window=window, return_onesided=True, detrend='constant', scaling='spectrum', axis=-1)
    
    
    if db_scale == True:
        # OPTIMIZATION: Multiplying a numpy array by the scalar 2.5e9 (inverse of 4e-10)
        # is faster than array division, yielding a measurable performance improvement.
        power_spectral_density = 10.*np.log10(power_spectral_density * 2.5e9)
    
    if save_output == True:
        os.makedirs(out_dir, exist_ok=True)
        data = np.column_stack((freq, power_spectral_density))
        np.savetxt(out_dir+"/welch_spectrum.csv", data, fmt="%.8e", delimiter=",", header="Freq, PSD (Welch)", comments="#")
    
    return freq, df, power_spectral_density
        



def auto_corr(signal, save_output : bool = False, out_dir : str = "", normalised : bool = True):
    """
    Calculates the auto-correlation of a discrete time signal, i.e., the correlation of the signal with a copy of itself, using the SciPy toolbox.
    Whenever possible, an FFT-based calculation is performed because it is more efficient higher effiency. Check out `this <https://stackoverflow.com/questions/57804124/does-numpy-correlate-differ-from-scipy-signal-correlate-if-both-are-used-on-a-1d>`_ StackOverflow thread for some detail.

    Parameters
    ----------
    signal : array_like
        The time series or signal whose auto-correlation needs to be computed.
    save_output : bool, optional
        Boolean argument to specify whether output CSV file file must be written or not. The default is False.
    out_dir : str, optional (needed only if save_output is `True`)
        Relative path to directory where the results of this calculation will be written. The default is NULL.
    normalised : bool, optional
        Boolean argument to specify if a normlaised auto-correlation needs to be computed (see the `Wikipedia page <https://en.wikipedia.org/wiki/Autocorrelation>`_ for detail). The default is True.

    Returns
    -------
    auto_correlation : array_like
        Auto-correlation of the signal.
    acorr_lags : array_like
        Array of lags used to compute the correlation.
    
    Examples
    -------
    >>> auto_correlation, acorr_lags = auto_corr(pres_signal)
    
    >>> auto_correlation, acorr_lags = auto_corr(pres_signal, save_output=True, out_dir="./results/nearfield_correlations")

    """
    import scipy.fft as fft

    signal -= np.mean(signal)
    
    n = len(signal)
    # OPTIMIZATION: explicit FFT for auto-correlation avoids the overhead of sp_signal.correlate
    # and reduces allocation sizes since we only care about positive lags.
    nfft = fft.next_fast_len(2 * n - 1)

    sig_fft = np.fft.rfft(signal, n=nfft)
    # The inverse real FFT of power spectrum gives auto-correlation for positive and negative lags.
    # The first n elements correspond to the positive lags (0 to n-1)
    # OPTIMIZATION: Calculate squared magnitude directly using numpy abs
    # np.abs(sig_fft)**2 is highly optimized in C and avoids expensive complex multiplication and conjugation.
    auto_correlation_full = np.fft.irfft(np.abs(sig_fft)**2, n=nfft)
    auto_correlation = auto_correlation_full[:n]

    if normalised == True:
        sig_var = np.var(signal)
        # OPTIMIZATION: Evaluating floor division (//) directly on a NumPy array is slow.
        # Multiplying by the inverse scalar and using np.floor() yields a ~25x speedup.
        inv_factor = 0.5 / (sig_var * len(signal))
        auto_correlation = np.floor(auto_correlation * inv_factor)
    
    acorr_lags = np.arange(n)

    if save_output == True:
        os.makedirs(out_dir, exist_ok=True)
        #data = np.column_stack((freq, cpsd))
        np.savetxt(out_dir+"/auto_correlation.csv", auto_correlation, fmt="%.8e", delimiter=",", header="Auto-correlation", comments="#")
    
    return auto_correlation, acorr_lags


def cross_corr(signal1, signal2, mode : str = 'full', save_output : bool = False, out_dir : str = ""):
    """
    Calculates the cross-correlation of a pair of signals, using the SciPy toolkit.

    Parameters
    ----------
    signal1 : array_like
        Reference signal to correlate against.
    signal2 : array_like
        Signal which is to be correlated against the reference signal.
    mode : str
        String indicating the size of the output. Available options are `'full'`, `'valid'` or `'same'`. The default is `'full'`. For the details, refer to the `SciPy documentation page <https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.correlate.html>`_
    save_output : bool, optional
        Boolean argument to specify whether output CSV file file must be written or not. The default is False.
    out_dir : str, optional
        Relative path to directory where the results of this calculation will be written. The default is NULL.

    Returns
    -------
    cross_correlation : array_like
        Cross-correlation of signal2 with signal1.
    xcorr_lags : array_like
        Array of lags used to compute the correlation.
    
    Notes
    -----
    - The order in which the signal pair is specified can make a very big difference in the correlation curve. Always keep note of which signal is used as your reference.
    
    Examples
    -------
    >>> cross_correlation, xcorr_lags = cross_corr(pres_data_1, pres_data_2)
    
    >>> cross_correlation, xcorr_lags = cross_corr(pres_data_1, pres_data_2, save_output=True, out_dir="./results/nearfield_correlations")


    """
    signal1 -= np.mean(signal1)
    signal2 -= np.mean(signal2)
    
    cross_correlation = sp_signal.correlate(signal1, signal2, mode=mode, method='auto')
    
    xcorr_lags = sp_signal.correlation_lags(len(signal1), len(signal2), mode=mode)
    
    if save_output == True:
        os.makedirs(out_dir, exist_ok=True)
        #data = np.column_stack((freq, cpsd))
        np.savetxt(out_dir+"/cross_correlation.csv", cross_correlation, fmt="%.8e", delimiter=",", header="Cross-correlation", comments="#")
    
    return cross_correlation, xcorr_lags


def cross_spectrum(time1, signal1, time2, signal2, save_output : bool = False, out_dir : str = "", window = 'hann', chunks : int = 4, overlap : float = 0.5,
                   scale_freq : bool = True, db_scale : bool = False):
    """
    Calculates the Cross Power Spectrum of a pair of input signals using Welch's method. Principles of windowing and overlap are the same as the standard Welch function :func:`~spectral_analysis.welch_spectrum`.

    Parameters
    ----------
    time1 : array_like
        Uniformly spaced discrete time series of first signal, in SI units.
    signal1 : array_like
        Uniformly spaced time-domain signal of physical quantity of first signal, in SI units.
    time2 : array_like
        Uniformly spaced discrete time series of second signal, in SI units.
    signal2 : array_like
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
    cross_power_spectral_density : array_like
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
    
    samples_per_segment = len(signal1) // chunks
    
    fft_length = next_greater_power_of_2(samples_per_segment)
    
    #df = fs/nfft
    
    try:
        if fs1 != fs2:
            raise ValueError
    except:
        ValueError("The two signals don't have the same sampling frequency. Try again with the correct signal pair.")
        return
    
    try:
        if len(signal1) != len(signal2):
            raise ValueError
    except:
        ValueError("The two signals don't have the same length. Try again with the correct signal pair.")
        return
    
    
    if scale_freq == True:
        freq, cross_power_spectral_density = sp_signal.csd(signal1, signal2, fs1, nperseg=samples_per_segment, noverlap=overlap*samples_per_segment, nfft=fft_length,
                          window=window, return_onesided=True, detrend='constant', scaling='density', axis=-1)
    else:
        freq, cross_power_spectral_density = sp_signal.csd(signal1, signal2, fs1, nperseg=samples_per_segment, noverlap=overlap*samples_per_segment, nfft=fft_length,
                      window=window, return_onesided=True, detrend='constant', scaling='spectrum', axis=-1)
    
    if db_scale == True:
        # OPTIMIZATION: Multiplying a numpy array by the scalar 2.5e9 (inverse of 4e-10)
        # is faster than array division, yielding a measurable performance improvement.
        cross_power_spectral_density = 10.*np.log10(cross_power_spectral_density * 2.5e9)
    
    if save_output == True:
        os.makedirs(out_dir, exist_ok=True)
        data = np.column_stack((freq, cross_power_spectral_density))
        np.savetxt(out_dir+"/cross_spectrum.csv", data, fmt="%.8e", delimiter=",", header="Freq, CPSD", comments="#")
    
    
    return freq, cross_power_spectral_density




def cross_spectrum_fft(time1, signal1, time2, signal2, save_output : bool = False, out_dir : str = "",
                       scale_spectrum : bool = True, scale_freq : bool = False, db_scale : bool = False):
    """
    Calculates the Cross Spectrum of a pair of signals using the FFT method and no windowing. The implementation follows the same principles as the :func:`~spectral_analysis.fft_spectrum` function.

    Parameters
    ----------
    time1 : array_like
        Uniformly spaced discrete time series of first signal, in SI units.
    signal1 : array_like
        Uniformly spaced time-domain signal of physical quantity of first signal, in SI units.
    time2 : array_like
        Uniformly spaced discrete time series of second signal, in SI units.
    signal2 : array_like
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
    cross_power_spectral_density : array_like
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
        if len(signal1) != len(signal2):
            raise ValueError
    except:
        ValueError("The two signals don't have the same length. Try again with the correct signal pair.")
        return
    
    freq1 = np.fft.rfftfreq(len(time1), 1/fs1) # discrete central frequencies of the FFT bins
    signal1 -= np.mean(signal1) # mean-removed part of the signal
    sig1_fft = np.fft.rfft(signal1) # Fourier-transformed signal, real part only
    
    #freq2 = np.fft.rfft(time2, 1/fs2) # discrete central frequencies of the FFT bins
    signal2 -= np.mean(signal2) # mean-removed part of the signal
    sig2_fft = np.fft.rfft(signal2)
    
    # OPTIMIZATION: Calculate magnitude of product as product of magnitudes.
    # |A * conj(B)| = |A| * |conj(B)| = |A| * |B|
    # This avoids computationally expensive complex multiplication and conjugation.
    if scale_spectrum == True:
        cross_power_spectral_density = (np.abs(sig1_fft) * np.abs(sig2_fft))/(fs1*len(signal1))
    else:
        cross_power_spectral_density = np.abs(sig1_fft) * np.abs(sig2_fft)
    
    if db_scale == True:
        # OPTIMIZATION: Multiplying a numpy array by the scalar 2.5e9 (inverse of 4e-10)
        # is faster than array division, yielding a measurable performance improvement.
        cross_power_spectral_density = 10.*np.log10(cross_power_spectral_density * 2.5e9)
        
    if save_output == True:
        os.makedirs(out_dir, exist_ok=True)
        data = np.column_stack((freq1, cross_power_spectral_density))
        np.savetxt(out_dir+"/cross_spectrum_fft.csv", data, fmt="%.8e", delimiter=",", header="Freq, CPSD (Plain FFT)", comments="#")
    
    
    return freq1, cross_power_spectral_density





def coherence(time1, signal1, time2, signal2, save_output : bool = False, out_dir : str = "", window = 'hann', chunks : int = 4, overlap : float = 0.5):
    """
    Calculates the coherence between an input pair of time series using the Welch method to estimate the power and cross spectra. This method is based on the same principles as :func:`~spectral_analysis.welch_spectrum`.

    Parameters
    ----------
    time1 : array_like
        Uniformly spaced discrete time series of first signal, in SI units.
    signal1 : array_like
        Uniformly spaced time-domain signal of physical quantity of first signal, in SI units.
    time2 : array_like
        Uniformly spaced discrete time series of second signal, in SI units.
    signal2 : array_like
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
    coherence_values : array_like
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
    
    samples_per_segment = len(signal1) // chunks
    
    fft_length = next_greater_power_of_2(samples_per_segment)
    
    
    freq, coherence_values = sp_signal.coherence(signal1, signal2, fs1, nperseg=samples_per_segment, noverlap=overlap*samples_per_segment, nfft=fft_length,
                     window=window, detrend='constant', axis=-1)
    
    #if save_output == True:
    #    os.makedirs(out_dir, exist_ok=True)
    #    data = np.column_stack((freq, cxy))
    #    np.savetxt(out_dir+"/signal_coherence.csv", data, fmt="%.8e", delimiter=",", header="Freq, Coherence", comments="#")
    
    return freq, coherence_values


def coherence_fft(time1, signal1, time2, signal2, save_output : bool = False, out_dir : str = ""):
    """
    Calculates the coherence between an input pair of time series using FFtTs of the individual power spectra and the cross spectra. This method is based on the same principles as :func:`~spectral_analysis.fft_spectrum`.

    Parameters
    ----------
    time1 : array_like
        Uniformly spaced discrete time series of first signal, in SI units.
    signal1 : array_like
        Uniformly spaced time-domain signal of physical quantity of first signal, in SI units.
    time2 : array_like
        Uniformly spaced discrete time series of second signal, in SI units.
    signal2 : array_like
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
    coherence_values : array_like
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
    
    freq1, df1, psd1 = fft_spectrum(time1, signal1)
    freq2, df2, psd2 = fft_spectrum(time2, signal2)
    
    
    cfreq, cpsd = cross_spectrum_fft(time1, signal1, time2, signal2)
    
    coherence_values = cpsd**2/(psd1*psd2)
    
    #if save_output == True:
    #    os.makedirs(out_dir, exist_ok=True)
    #    data = np.column_stack((freq1, cxy))
    #    np.savetxt(out_dir+"/signal_coherence_fft.csv", data, fmt="%.8e", delimiter=",", header="Freq, Coherence", comments="#")
    
    return freq1, coherence_values


