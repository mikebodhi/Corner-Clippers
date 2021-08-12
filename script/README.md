corner_clippers.py is a python script that is used to identify neutrino events as corner clippers. It adds a 'isclip' tag to every neutrnio event that in a .i3 file.
This tag is viewable in steamshovel and allows for the corner-clipping events to be filtered out by filtering for events where frame['isclip'] != true

HOW IT WORKS:
1) corner_clippers.py, trained_corner_clippers_final.joblib, and GeoCalibDetectorStatus_AVG_55697-57531_PASS2_SPE_withScaledNoise.i3.gz must all be downloaded and included in the
directory that contains the .i3 file(s) that you want to identify corner clippers in.
2) It is called in the command line w/ the .i3 files taken as arguments. Ex call: python corner_clippers.py YOUR_FILENAME1.i3 YOUR_FILENAME2.i3 ...
3) This call will then take the event frames from ALL input files and combine them into ONE new file, no_cc_YOUR_FILENAME1.i3, with the added tag 'isclip' that has a boolean value
which can be used to filter out corner-clippers event from view and/or analysis.

INTENDED USE:

While multiple .i3 files can be used as input for the script, it is intended that only 1 file be used as input per 1 call to corner_clippers.py. This is because the new file that
is created will be named no_cc_YOUR_FILENAME1.i3 where YOUR_FILENAME1 is the name of the first input file passed as an argument, so you must remember which other files you passed
as arguments so that you do not pass them as arguments again later. In addition, all frames from all files are combined into the 1 output file with no distinction between which
frames belonged to which file, so that is why calling corner_clippers.py is intended to have only 1 input file per function call. This allows for it to be used in bash scripting,
where you want to identify corner clippers in all .i3 files in a directory but want them to remain distinct, so corner_clippers.py can be called inside a loop in a bash script
that loops through all .i3 files in the CWD and will create new, identifiable .i3 files for each unique file in the directory.

VERSIONS OF EVERYTHING THAT I HAD:

Python: 3.7.5

joblib :1.0.1

numpy: 1.21.1

pandas: 1.3.1

scikit-learn: 0.24.1

scipy: 1.7.1

^not sure if these are exact requirements, i.e having python 3.7.0 instead of 3.7.5 may not break corner_clippers.py, but just in case anything does go wrong I figured I should
include what versions I had just in case
