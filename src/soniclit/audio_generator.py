import wave
import struct
import sys
import csv
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample


def write_wav(audio_data: list, output_filename: str, sampling_rate: int, amplitude_scaling: float) -> None:
    """
    Writes audio data to a WAV file.

    Parameters
    ----------
    audio_data : list or array_like
        The audio data to write (normalized between -1 and 1 usually, but here handled as floats to be scaled).
    output_filename : str
        The path of the output WAV file.
    sampling_rate : int
        Sampling frequency in Hz.
    amplitude_scaling : float
        Scaling factor to convert float samples to integer PCM (usually 32767 for 16-bit).

    Returns
    -------
    None
    """
    wav_file = wave.open(output_filename, 'w')
    num_channels = 1
    sample_width = 2
    sampling_rate = sampling_rate
    num_frames = len(audio_data)
    compression_type = "NONE"
    compression_name = "not compressed"
    wav_file.setparams((num_channels,
                       sample_width,
                       sampling_rate,
                       num_frames,
                       compression_type,
                       compression_name))
    audio_frames = []
    for sample in audio_data:
        scaled_sample = int(sample * amplitude_scaling)
        audio_frames.append(struct.pack('h', scaled_sample))

    audio_frames = ''.join(audio_frames)
    wav_file.writeframes(audio_frames)
    wav_file.close()
    print("%s written" % (output_filename))


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("You must supply a filename to generate")
        exit(-1)
    for input_filename in sys.argv[1:]:

        data_list = []
        for time_step, value in csv.reader(open(input_filename, 'U'), delimiter=','):
            try:
                data_list.append(float(value))  # Here you can see that the time column is skipped
            except ValueError:
                pass  # Just skip it

        data_array = np.array(data_list)  # Just organize all your samples into an array
        # Normalize data
        data_array /= np.max(np.abs(data_list))  # Divide all your samples by the max sample value
        filename_base, file_extension = input_filename.rsplit(".", 1)
        resampled_data = resample(data_array, len(data_list))
        # wavfile.write('rec.wav', 16000, resampled_data)  # resampling at 16khz
        wavfile.write('rec.mp3', 20000, resampled_data)  # resampling at 307khz
        print("File written succesfully !")
