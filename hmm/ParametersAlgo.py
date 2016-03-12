'''
Created on May 28, 2015

@author: joro
'''

######### PARAMS:
class ParametersAlgo(object):
    
    THRESHOLD_PEAKS = -70

    DEVIATION_IN_SEC = 0.1

    # unit: num frames
    NUMFRAMESPERSECOND = 100
    # same as WINDOWSIZE in wavconfig singing. unit:  seconds. TOOD: read from there automatically
    WINDOW_SIZE = 0.25
    
    # in frames
    CONSONANT_DURATION = NUMFRAMESPERSECOND * 0.1;
    
    ONLY_MIDDLE_STATE = 1
    
    WITH_SHORT_PAUSES = 0
    
    WITH_PADDED_SILENCE = 1
    
    WITH_ORACLE_PHONEMES = 1
    
    WITH_SECTION_ANNOTATIONS = 1
    
    POLYPHONIC = 0
    
    WITH_ORACLE_ONSETS = 0
    ### no onsets at all. 
#     WITH_ORACLE_ONSETS = -1
    
    ONSET_TOLERANCE_WINDOW = 0.02 # seconds
    ONSET_TOLERANCE_WINDOW = 0 # seconds

    
    CUTOFF_BIN_OBS_PROBS = 4 
    