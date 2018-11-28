#!/usr/bin/env python
"""
Haukkuvahti
version 0.1
"""
from time import localtime, strftime
from math import ceil, floor, pow, sqrt
from pathlib import Path
import struct
import threading
import wave
import collections
import msvcrt
import datetime
import configparser
import sys

import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class Haukkuvahti(object):
    """ Class presentation of Haukkuvahti """
    def __init__(self, thread_lock, strm, n_frames, frame_size, config):
        self.lock = thread_lock
        self.strm = strm
        self.n_frames = n_frames
        self.frame_size = frame_size
        self.peak_report_timeout = 0
        self.n_peak_log_entries = 0
        buffer_length = ceil(RATE / CHUNK * 5)
        self.buffer = collections.deque(maxlen=ceil(buffer_length))
        self.config = config
        self.running = False

    def get_number_of_peak_log_entries(self):
        """ Returns number of entries in the log """
        return self.n_peak_log_entries

    def get_rms(self, block):
        """ Returns RMS amplitude of a wav block """
        # https://stackoverflow.com/a/25871132
        count = len(block) / 2
        block_format = "%dh" % (count)
        shorts = struct.unpack(block_format, block)

        sum_squares = 0.0
        for sample in shorts:
            # sample is a signed short in +/- 32768, normalize it to 1.0
            sum_squares += pow(sample * SHORT_NORMALIZE, 2)

        return sqrt(sum_squares / count)

    def run(self):
        """ Thread function """
        self.running = True
        with open(self.config['PATHS']['csv_log_file'], 'w') as csv_log:
            print('timestamp;max;min;mean', file=csv_log)
        frames = []
        save_stream_request = False
        frame_counter = RECORD_LENGTH_S
        open(self.config['PATHS']['log_file'], 'w').close()

        while self.running:  # Capture loop
            max_vol = 0
            min_vol = 1000
            mean_vol = 0

            chunks = []
            # Capture for (approximately 1 second)
            for _ in range(0, floor(self.n_frames)):
                data = stream.read(self.frame_size)
                chunks.append(data)
                # Calculate 1 second statistics
                rms = self.get_rms(data)
                if rms > max_vol:
                    max_vol = rms
                if rms < min_vol:
                    min_vol = rms
                mean_vol += rms / floor(self.n_frames)
                # If there is a lot of noise make a log entry and request audio saving
                if rms > NOISE_LOG_THRESHOLD:
                    if not save_stream_request:
                        print(strftime("[%H:%M:%S] ",localtime()),end = '', flush = True)
                        print("Noise detected, started recording. Ending in ",
                              end='', flush=True)
                        save_stream_request = True
                    if self.peak_report_timeout == 0:
                        with open(self.config['PATHS']['log_file'], 'a') as log_file:
                            print(strftime("%Y-%m-%d %H:%M:%S",
                                           localtime()) + ' ' + str(rms), file=log_file)
                        self.n_peak_log_entries += 1
                        self.peak_report_timeout = RECORD_LENGTH_S
                        with open(self.config['PATHS']['csv_log_file'], 'a') as csv_log:
                            self.report(csv_log, max_vol, min_vol, mean_vol)

            if self.peak_report_timeout > 0:
                self.peak_report_timeout -= 1

            if save_stream_request is True:
                if frame_counter == RECORD_LENGTH_S:
                    frames = []
                frames.extend(chunks)
                frame_counter -= 1
                if frame_counter > 0:
                    print(str(frame_counter) + ',', end='', flush=True)
                else:
                    print(str(frame_counter) + ' ', end='', flush=True)

            # Save wav file if sufficient time has passed since previous one
            if frame_counter == 0:
                save_stream_request = False
                frame_counter = RECORD_LENGTH_S
                if self.config.getboolean('LOGGING','save_audio'):
                    wav_name = 'Audio_' + \
                        strftime("%Y-%m-%d_%H-%M-%S", localtime()) + '.wav'
                    wav_file = wave.open(wav_name, 'wb')
                    wav_file.setnchannels(2)
                    wav_file.setsampwidth(p.get_sample_size(FORMAT))
                    wav_file.setframerate(RATE)
                    wav_file.writeframes(b''.join(frames))
                    wav_file.close()
                    print("-> Saved audio to file: " + wav_name, end='', flush=True)
                print(" ...continuing monitoring")

    def stop(self):
        """ Stops the thread """
        self.running = False

    def report(self, log_file, max_vol, min_vol, mean_vol,):
        """ Helper function for writing log messages """
        print(strftime("%Y-%m-%d %H:%M:%S", localtime()) + ";"
              + str(max_vol) + ";" + str(min_vol) + ";" + str(mean_vol), file=log_file)

def bytespdate2num(fmt, encoding='utf-8'):
    strconverter = mdates.strpdate2num(fmt)
    def bytesconverter(b):
        s = b.decode(encoding)
        return strconverter(s)
    return bytesconverter

def visualize_peak_log(logfile):
    """ Create a histogram of the log entry timestamps and save it as png """
    _, timestamps, _ = np.loadtxt(logfile, unpack=True,
                                  delimiter=' ',
                                  converters={0: mdates.bytespdate2num("%Y-%m-%d"),
                                              1: mdates.bytespdate2num("%H:%M:%S")})

    if timestamps.size > 1:
        first_stamp = mdates.num2date(timestamps[0])
        last_stamp = mdates.num2date(timestamps[-1])

        bin_range = range(first_stamp.hour, last_stamp.hour + 2)
        date_bins = []
        for h in bin_range:
            date_bins.append(datetime.datetime(1900, 1, 1, h, 0, 0, 0))
        num_bins = mdates.date2num(date_bins)
    else:
        num_bins = 1

    _, ax = plt.subplots(1, 1)
    ax.hist(timestamps, num_bins, rwidth=1, ec='k')
    ax.xaxis.set_major_locator(mdates.HourLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H'))
    plt.title('Number of entires per hour, in total ' + str(timestamps.size))
    plt.savefig(datetime.datetime.now().strftime("%Y-%m-%d") + '-summary.png')
    plt.show()

def create_default_configuration_file():
    config = configparser.ConfigParser()
    config['PATHS'] = {'CSV_LOG_FILE': "log.csv",
                       'LOG_FILE': "log.txt"}
    config['AUDIO'] = {'NOISE_LOG_THRESHOLD': str(0.02),
                       'RECORD_LENGTH': str(5)}
    config['LOGGING'] = {'VISUALIZE_LOG': 'yes',
                         'SAVE_AUDIO': 'yes'}
    with open('settings.ini', 'w') as configfile:
        config.write(configfile)

def read_configuration_file(file):
    config = configparser.ConfigParser()
    config.read(file)
    print({section: dict(config[section]) for section in config.sections()})
    return config

if __name__ == '__main__':
    # pylint: disable=C0103

    config_file = Path("settings.ini")
    if not config_file.is_file():
        print("* Configuration file not found, creating default configuration to settings.ini")
        create_default_configuration_file()
    
    configuration = read_configuration_file(config_file.as_posix())

    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    CHUNKS_PER_SECOND = RATE / CHUNK
    NOISE_LOG_THRESHOLD = float(configuration['AUDIO']['NOISE_LOG_THRESHOLD'])
    RECORD_LENGTH_S = int(configuration['AUDIO']['RECORD_LENGTH'])  # Only full seconds
    SHORT_NORMALIZE = (1.0 / 32768.0)
    try:
        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK)
    except:
        print("* ERROR: Could not find any recording device")
        msvcrt.getch()
        sys.exit(1)


    lock = threading.Lock()
    vahti = Haukkuvahti(lock, stream, CHUNKS_PER_SECOND, CHUNK, configuration)
    print("* Starting")
    t = threading.Thread(target=vahti.run)
    t.start()
    print("* Press any key to stop monitoring")
    msvcrt.getch()
    vahti.stop()
    t.join()
    stream.stop_stream()
    stream.close()
    print("* Monitoring stopped")
    n_entries = vahti.get_number_of_peak_log_entries()
    print("There was "
          + str(n_entries)
          + " entries to log during the monitoring session")
    if (n_entries > 0 and configuration.getboolean('LOGGING','VISUALIZE_LOG')):
        visualize_peak_log(configuration['PATHS']['log_file'])
    print("Press any key to quit")
    msvcrt.getch()