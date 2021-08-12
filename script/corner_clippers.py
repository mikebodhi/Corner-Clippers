#Imports modules
import numpy as np
import pandas as pd
import sklearn
import icecube
import sys
import glob
import joblib
from icecube import dataio, dataclasses, icetray
from I3Tray import *
import sys

def load_geometry():
    #Loads detector geometry file
    geofile = dataio.I3File('GeoCalibDetectorStatus_AVG_55697-57531_PASS2_SPE_withScaledNoise.i3.gz')

    #Saves geometry frame from geofile and then saves DOM geometry (position) information in geometry
    gframe = geofile.pop_frame(icetray.I3Frame.Geometry)
    geometry = gframe['I3Geometry']
    
    return geometry

def get_dom_info(geometry):
    
    #outer_keys/outer_doms will hold the OMKeys/DOM positions for DOMs located in the outer strings, defined by outer_strings
    outer_keys = []
    outer_strings = [1,2,3,4,5,6,7,13,14,21,22,30,31,40,41,50,51,59,60,67,68,72,73,74,75,76,77,78]

    #inner_strings holds the string indices that are not included in the outer strings, but also does not include deepcore
    inner_strings = [8,9,10,11,12,15,16,17,18,19,20,23,24,25,26,27,28,29,32,33,34,35,36,37,38,39,42,43,44,45,46,47,48,49,52,53,
                     54,55,56,57,58,61,62,63,64,65,66,69,70,71]

    #gets the positional information and OMKeys for each DOM
    dom_pos = [j.position for i,j in geometry.omgeo]
    geo_keys = [i for i in geometry.omgeo.keys()]

    #loops through all strings in the inner_strings and adds the first&last DOM positional info/OMkey to outer keys & doms since
    #events can clip on the top and bottom of the detector
    for i in range(len(geo_keys)):
        
        for j in inner_strings:
            
            if geo_keys[i][0] == j and (geo_keys[i][0] == 1 or geo_keys[i][1] == 60):
                
                outer_keys.append(geo_keys[i])

    #Adds all outer DOM positional info/OMkeys to their lists 
    for i in range(len(geo_keys)):
        
        for j in outer_strings:
            
            #<= 60 condition is to make sure that only the 60 DOMs per string are counted, some have more than 60
            if geo_keys[i][0] == j and geo_keys[i][1] <= 60:
                
                outer_keys.append(geo_keys[i])
                
    return outer_keys, geo_keys, dom_pos

#this method will get the values for the 4 features used to define an event
#Radial Center of gravity (cogr): defined by Tessa Carver in her thesis
#Veritcal Center of gravity (cogz): also defined by Tessa Carver in her thesis
#ratio: the ratio of photoelectrons (PEs) detected in the outer DOMs divided by the total number of PEs seen for the whole event
#total PE: corner clippers should have a lower total PE count than normal events
def get_vals(frame, pulses, outer_keys, geo_keys, dom_pos):
    
    #placeholders for the numerator in cogr and cogz, instantiates outer_PEs
    r_numerator = 0
    z_numerator = 0
    outer_PEs = 0
    
    #gets the pulse series that all event info will be taken from (STRHVInIcePulses)
    pulsemap = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, pulses)
    outer_strings = [1,2,3,4,5,6,7,13,14,21,22,30,31,40,41,50,51,59,60,67,68,72,73,74,75,76,77,78]

    #saves all pulses registered by the DOMs in all_pulses then gets total_PE by summing the charge in every pulse
    all_pulses = [p for i,j in pulsemap for p in j]
    total_PE = sum([p.charge for p in all_pulses])
    
    #loops through every OMkey that registered a pulse
    for om, thesepulses in pulsemap:
        
        #gets the total number of PEs seen by that DOM
        qt = sum([pulse.charge for pulse in thesepulses])
        
        #if the dom is included in the outer_doms, adds the PEs seen to the outer_PEs
        if om in outer_keys or om.string in outer_strings:
            outer_PEs += qt
        
        index = geo_keys.index(om)
        
        #calculates the numerator used in cogr and cogz
        r_numerator += qt*np.sqrt(dom_pos[index][0]**2 + dom_pos[index][1]**2)
        z_numerator += qt*dom_pos[index][2]
        
    cogr = r_numerator/total_PE
    cogz = z_numerator/total_PE
    ratio = outer_PEs/total_PE
    
    #returns all 4 values
    return cogr, ratio , cogz, total_PE

#method that will predict whether an event is a corner clipper of not using the trained random forest
def primary_cut(frame, pulses):
    
    geometry = load_geometry()
    outer_keys, geo_keys, dom_pos = get_dom_info(geometry)
    #loads in trained random forest
    ranfor = joblib.load('trained_corner_clippers_final.joblib')
    #gets the values of the 4 features and then predicts based on them
    CoG_r, ratio, CoG_z, total_charge = get_vals(frame,pulses, outer_keys, geo_keys, dom_pos)
    X = np.array([CoG_r,ratio,CoG_z,total_charge])
    X = X.reshape(1,-1)
    y_pred = ranfor.predict(X)
    
    #if y_pred equals 1, then the event is a corner clipper, and assigns an 'isclip' label to the event that is true
    if y_pred == 1:
        
        frame['isclip'] = icetray.I3Bool(True)
    
    else:
        #if not, the event is not a corner clipper so 'isclip' is false for the event
        frame['isclip'] = icetray.I3Bool(False)
        
    return True

#takes *.i3 files from the command line and will search all of the events in every file for corner clippers.
#Will then create ONE file 'no_cornerclippers.i3.gz' that adds a 'isclip' tag that is filterable in steamshovel and has a true/false value.
def main():

    input_files = []

    for i, arg in enumerate(sys.argv):
        
        if i == 0:
            continue
        else:
            input_files.append(arg)

    tray = I3Tray()
    tray.Add('I3Reader', FilenameList=input_files)
    tray.Add(primary_cut, pulses='SRTHVInIcePulses') 
    tray.Add('I3Writer', 'EventWriter',
	FileName='no_cc_' + input_files[0],
        Streams=[icetray.I3Frame.TrayInfo,
        icetray.I3Frame.DAQ,
        icetray.I3Frame.Physics,
        icetray.I3Frame.Stream('S')],
        DropOrphanStreams=[icetray.I3Frame.DAQ], )
    tray.AddModule('TrashCan','can')
    tray.Execute()
    tray.Finish()
    return

if __name__ == "__main__":
    main()
    sys.exit()
