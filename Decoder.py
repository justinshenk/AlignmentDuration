'''
Created on Oct 27, 2014

@author: joro
'''
import os
import sys
import logging


parentDir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0]) ), os.path.pardir)) 

pathUtils = os.path.join(parentDir, 'utilsLyrics')
sys.path.append(pathUtils )
from Utilz import writeListOfListToTextFile, writeListToTextFile


import numpy

# TODO: read from models
numMixtures = 9
numDimensions = 25

# TODO: read from feat extraction parameters
NUM_FRAMES_PERSECOND = 100.0

# if false, use transition probabilities from htkModels
WITH_DURATIONS= True
ONLY_MIDDLE_STATE = False

#WITH_DURATIONS= False
#ONLY_MIDDLE_STATE = False



if WITH_DURATIONS:
    pathHMM = os.path.join(parentDir, 'HMMDuration')
else:
    pathHMM = os.path.join(parentDir, 'HMM')


if pathHMM not in sys.path:    
    sys.path.append(pathHMM)

# if WITH_DURATIONS:
#     from hmm.continuous.DurationPdf import MINIMAL_PROB

from hmm.Path import Path
from hmm.continuous.GMHMM  import GMHMM

print 'SYS PATH is: ', sys.path


class Decoder(object):
    '''
    holds structures used in decoding and decoding result
    '''


    def __init__(self, lyricsWithModels, ALPHA = 1, numStates=None, withModels=True):
        '''
        Constructor
        '''
        self.lyricsWithModels = lyricsWithModels
        
        '''
        of class HMM
        '''
        self.hmmNetwork = []
                

        self._constructHmmNetwork(numStates, ALPHA, withModels)
        
        # Path class object
        self.path = None
        
    def _constructHmmNetwork(self,  numStates, ALPHA, withModels ):
        '''
        top level-function: costruct self.hmmNEtwork that confirms to guyz's code 
        '''
        
    #     sequencePhonemes = sequencePhonemes[0:4]
        
        
        ######## construct transition matrix
        #######
        if not WITH_DURATIONS:
            transMAtrix = self._constructTransMatrixHMMNetwork(self.lyricsWithModels.phonemesNetwork)

#        DEBUG
#  writeListOfListToTextFile(transMAtrix, None , '/Users/joro/Documents/Phd/UPF/voxforge/myScripts/AlignmentStep/transMatrix')
        
        # construct means, covars, and all the rest params
        #########
       
        if numStates == None:
            numStates = len(self.lyricsWithModels.statesNetwork) 
        
        means, covars, weights, pi = self._constructHMMNetworkParameters(numStates,  withModels)
        
        if  WITH_DURATIONS:
            self.hmmNetwork = GMHMM(numStates,numMixtures,numDimensions,None,means,covars,weights,pi,init_type='user',verbose=True)
            self.hmmNetwork.setALPHA(ALPHA)
        else:
            self.hmmNetwork = GMHMM(numStates,numMixtures,numDimensions,transMAtrix,means,covars,weights,pi,init_type='user',verbose=True)


        
    def  _constructTransMatrixHMMNetwork(self, sequencePhonemes):
        '''
        tranform other htkModel params to  format of gyuz's hmm class
        take from sequencePhonemes' attached htk models the transprobs.
        '''
        # just for initialization totalNumPhonemes
        totalNumStates = 0
        for phoneme in sequencePhonemes:
            currNumStates = phoneme.htkModel.tmat.numStates - 2
            totalNumStates += currNumStates
            
        transMAtrix = numpy.zeros((totalNumStates, totalNumStates), dtype=numpy.double)
        
        
        counterOverallStateNum = 0 
        
        for phoneme in sequencePhonemes:
            currNumStates =   phoneme.htkModel.tmat.numStates - 2
            
    #         disregard 1st and last states from transMat because they are the non-emitting states
            currTransMat = getTransMatrixForPhoneme(phoneme)
            
            transMAtrix[counterOverallStateNum : counterOverallStateNum + currNumStates, counterOverallStateNum : counterOverallStateNum + currNumStates ] = currTransMat
           
            # transition probability to next state
            #         TODO: here multiply by [0,1] matrix next state. check if it exists
            nextStateTransition = 1
            
            if (counterOverallStateNum + currNumStates) < transMAtrix.shape[1]:
                val = currTransMat[-2,-1] * nextStateTransition
                transMAtrix[counterOverallStateNum + currNumStates -1, counterOverallStateNum + currNumStates] =  val
    
    
            # increment in final trans matrix  
            counterOverallStateNum +=currNumStates
            
            
        return transMAtrix
    

    
    def _constructHMMNetworkParameters(self,  numStates,  withModels=True, sequenceStates=None):
        '''
        tranform other htkModel params to  format of gyuz's hmm class
        '''
        
       
        
        means = numpy.empty((numStates, numMixtures, numDimensions))
        
        # init covars
        covars = [[ numpy.matrix(numpy.eye(numDimensions,numDimensions)) for j in xrange(numMixtures)] for i in xrange(numStates)]
        
        weights = numpy.ones((numStates,numMixtures),dtype=numpy.double)
        
        # start probs : allow to start only at first state
        pi = numpy.zeros((numStates), dtype=numpy.double)
        
        # avoid log(0) 
#         pi.fill(MINIMAL_PROB)
        pi.fill(sys.float_info.min)
        
        pi[0] = 1
        
#         pi = numpy.ones( (numStates)) *(1.0/numStates)
        
        if not withModels:
            return None, None, None, pi

        
        sequenceStates = self.lyricsWithModels.statesNetwork
         
        if sequenceStates==None:
            sys.exit('no state sequence')
               
        for i in range(len(sequenceStates) ):
            state  = sequenceStates[i] 
            
            for (numMixture, weight, mixture) in state.mixtures:
                
                weights[i,numMixture-1] = weight
                
                means[i,numMixture-1,:] = mixture.mean.vector
                
                variance_ = mixture.var.vector
                for k in  range(len( variance_) ):
                    covars[i][numMixture-1][k,k] = variance_[k]
        return means, covars, weights, pi
    
            
      
        
        
    def duration2numFrameDuration(self, observationFeatures):
        '''
        helper method. 
        setDuration HowManyFrames for each state in hmm
        '''
        # TODO: read from score
#         self.bpm = 60
#         durationMinUnit = (1. / (self.bpm/60) ) * (1. / MINIMAL_DURATION_UNIT) 
#         numFramesPerMinUnit = NUM_FRAMES_PERSECOND * durationMinUnit
        totalDur = self.lyricsWithModels.getTotalDuration()
        numFramesPerMinUnit   = float(len(observationFeatures)) / float(totalDur)
        numFramesDurationsList = []
        
        for  i, stateWithDur_ in enumerate (self.lyricsWithModels.statesNetwork):
            # numFrames per phoneme
            numFramesPerState = round(float(stateWithDur_.duration) * numFramesPerMinUnit)
            numFramesDurationsList.append(numFramesPerState)
            stateWithDur_.setDurationInFrames(numFramesPerState)
            
        return numFramesDurationsList
        
        


        
    
    def decodeAudio( self, observationFeatures, usePersistentFiles, URI_recording_noExt):
        ''' decode path for given exatrcted features for audio
        HERE is decided which decoding scheme (based on WITH_DURATION parameter)
        '''
        self.hmmNetwork.setPersitentFiles( usePersistentFiles, URI_recording_noExt )
        # double check that features are in same dimension as model
        if observationFeatures.shape[1] != numDimensions:
            sys.exit("dimension of feature vector should be {} but is {} ".format(numDimensions, observationFeatures.shape[1]) )
#         observationFeatures = observationFeatures[0:100,:]
        
        if  WITH_DURATIONS:
            listDurations = self.duration2numFrameDuration(observationFeatures)
        
            self.hmmNetwork.setDurForStates(listDurations) 
        
#         if os.path.exists(PATH_CHI) and os.path.exists(PATH_PSI): 
#             chiBackPointer = numpy.loadtxt(PATH_CHI)
#             psiBackPointer = numpy.loadtxt(PATH_PSI)
#                
#         else:

        # standard viterbi forced alignment
        if not WITH_DURATIONS:
            path_, psi, delta = self.hmmNetwork._viterbiForced(observationFeatures)
            self.path =  Path(None, None)
            self.path.setPatRaw(path_)
            
        # duration-HMM
        else:
        
            chiBackPointer, psiBackPointer = self.hmmNetwork._viterbiForcedDur(observationFeatures)
        
#             writeListOfListToTextFile(chiBackPointer, None , PATH_CHI)
#             writeListOfListToTextFile(psiBackPointer, None , PATH_PSI)
                
            self.path =  Path(chiBackPointer, psiBackPointer)
            print "\n"
         # DEBUG
#         self.path.printDurations()
#         writeListToTextFile(self.path.pathRaw, None , '/tmp/path')
        
    
  
    

    def path2ResultWordList(self):
        '''
        makes sense of path indices : maps numbers to states and phonemes, uses self.lyricsWithModels.statesNetwork and lyricsWithModels.listWords) 
        to be called after decoding
        '''
        # indices in pathRaw
        self.path._path2stateIndices()
        
        #sanity check
        numStates = len(self.lyricsWithModels.statesNetwork)
        numdecodedStates = len(self.path.indicesStateStarts)
        
        if numStates != numdecodedStates:
            logging.warn("detected path has {} states, but stateNetwork transcript has {} states".format( numdecodedStates, numStates ) )
            # num misssed states in the beginning of the path
            howManyMissedStates = numStates - numdecodedStates
            # WORKAROUND: assume missed states start at time 0
            for i in range(howManyMissedStates):
                self.path.indicesStateStarts[:0] = [0]
            
        detectedWordList = []
        
        for word_ in self.lyricsWithModels.listWords:
            countFirstState = word_.syllables[0].phonemes[0].numFirstState

            lastPhoneme = word_.syllables[-1].phonemes[-1]
            if lastPhoneme.ID != 'sp':
                sys.exit('In Decode. \n last state for word {} is not sp. Sorry - not implemented.'.format(word_.text))
            
            countLastState = lastPhoneme.numFirstState

            detectedWord = self._constructTimeStampsForWord( word_, countFirstState, countLastState)
           
            detectedWordList.append( detectedWord)
        return detectedWordList
    
    
    def _constructTimeStampsForWord(self,  word_, countFirstState, countLastState):
        '''
        helper method
        '''
        currWordBeginFrame = self.path.indicesStateStarts[countFirstState]
        currWordEndFrame = self.path.indicesStateStarts[countLastState]
    #             # debug:
    #             print self.pathRaw[currWordBeginFrame]
    # timestamp:
        startTs = float(currWordBeginFrame) / NUM_FRAMES_PERSECOND
        endTs = float(currWordEndFrame) / NUM_FRAMES_PERSECOND
        
        detectedWord = [startTs, endTs, word_.text]
        print detectedWord
        
        return detectedWord
    
def getTransMatrixForPhoneme( phoneme):
    '''
    read the trans matrix from model. 
    3x3 or 1x1 matrix for emitting states only as numpy array
    '''
    vector_ = phoneme.htkModel.tmat.vector
    currTransMat = numpy.reshape(vector_ ,(len(vector_ )**0.5, len(vector_ )**0.5))

    #         disregard 1st and last states from transMat because they are the non-emitting states
    return currTransMat[1:-1,1:-1]
        