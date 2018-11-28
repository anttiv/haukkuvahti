Haukkuvahti
===========

A python script that can be used to monitor a microphone and keep log of events (sound level exceeding a specified limit). Currently Haukkuvahti only works on Windows machines.

Dependencies
------------
Haukkuvahti depends on following third-party libraries

* matplotlib (version 2.2.2)
* numpy (version 1.14.2)
* PyAudio (0.2.9)

Usage
-----

The script is ran from command line:

    python ./haukkuvahti.py

During first run a settings file settings.ini is created. From the settings file several options can be configured:

* Event visualization as a histogram after session has ended
* Whether audio samples of detected events are saved
* Length of saved audio sample
* Event detection threshold
* Paths for log files

When running Haukkuvahti listens to a microphone and monitors the sound level. When the sound level exceeds a specified limit, Haukkuvahti logs an event. Logged events are printed to command line.

Haukkuvahti makes two separate log files, a csv-formatted log file and a plain text file.

The CSV file keeps track of detected minimum, maximum and mean noise level during events.

The plain text file contaings timestamped events and noise level which triggered the event.

For "poor man's online surveillance" the log files can be configured to be saved on a cloud storage (e.g. Google Drive).

License
-------

(Third-pary libraries under their own licenses)

MIT License

Copyright (c) 2018 Antti Virta

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.