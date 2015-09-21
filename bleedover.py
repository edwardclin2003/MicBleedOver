#This code resolves dual channel audio which has mic bleed (speaker can be heard on other channel), or dual microphone setups where both mics pick up people at various amplitude.
#By Edward Lin

#Looks at Voci's JSON speech decodings of audio with dual channels for regions where words are found on both sides at the same time and also looks at the wav file for the power level.  Assign the region to one of the channels which has the most amplitude power. 
#Clears JSON channel which is deemed to be the channel that bled into so the transcript looks good

import os
import sys
import json
import wave
import struct

def bleedremoval(inputwavfile, inputjsonfile, outputjsonfile):
    fptr = open(inputjsonfile)
    fdata = fptr.read()
    fptr.close()
    #open and read header of audio file
    wavptr = wave.open(inputwavfile, 'r')
    tframes = wavptr.getnframes()
    tsampwidth = wavptr.getsampwidth()
    tframerate = wavptr.getframerate()
    rframedata = wavptr.readframes(tframes)
    cchan = wavptr.getnchannels()
    unpstr = '<{0}h'.format(tframes*cchan)
    #store audio samples
    x = list(struct.unpack(unpstr, rframedata))
    del rframedata
    wavptr.close()
    xchan = []
    for xindex in range(cchan):
        xchan.append(x[xindex::cchan])

    fjson = json.loads(fdata)
    utterances = fjson["utterances"]
    wordconvtxtlist = []
    for i in range(cchan):
        wordconvtxtlist.append([])

    #collect words within channels and utterances
    uttcount = 0
    for utt in utterances:
        chan = utt["metadata"]["channel"]
        eventcount = 0
        for event in utt["events"]:
            word = event["word"].lower().replace(".","").replace(",","").replace("?","")
            start = event["start"]
            end = event["end"]
            conf = event["confidence"]

            dif = int((end-start)*tframerate)
            ssam = int(start*tframerate)
            cpower = 0.0
            for d in range(dif):
                cpower = cpower + (xchan[chan][ssam+d]*xchan[chan][ssam+d])
            #store word info by channel
            wordconvtxtlist[chan].append([word, start, end, cpower, uttcount, eventcount])
            eventcount = eventcount + 1
        uttcount = uttcount + 1
    #sort it and keep iterator
    worditerator = []
    maxiterator = []

    #sort by start time
    for i in range(cchan):
        wordconvtxtlist[i].sort(key=lambda tup: tup[1])
        worditerator.append(0)
        maxiterator.append(len(wordconvtxtlist[i]))

    removelist = []
    allwordsprocessed = False
    for c in range(cchan):
         #check if all done
        if worditerator[c] == maxiterator[c]:
            allwordsprocessed = True
            break
    while allwordsprocessed == False:
        allwordsprocessed = False
        #assume 2 channel
        prevtup = wordconvtxtlist[0][worditerator[0]]
        curtup = wordconvtxtlist[1][worditerator[1]]
        if ((curtup[1] < prevtup[1]) and (curtup[2]  > prevtup[1])) or \
           ((curtup[1] >= prevtup[1]) and (curtup[1] < prevtup[2])):
            if prevtup[3] < curtup[3]: # check power and determines which channel loses
                removelist.append([prevtup[0],prevtup[4],prevtup[5]])
                worditerator[0] = worditerator[0] + 1      
            else:
                removelist.append([curtup[1],curtup[4],curtup[5]])
                worditerator[1] = worditerator[1] + 1
        elif ((curtup[1] < prevtup[1]) and (curtup[2] <= prevtup[1])):
            worditerator[1] = worditerator[1] + 1
        elif ((curtup[1] > prevtup[1]) and (curtup[1] >= prevtup[2])):
            worditerator[0] = worditerator[0] + 1

        for c in range(cchan):
             #check if all done
            if worditerator[c] == maxiterator[c]:
                allwordsprocessed = True
                break
 
    #remove from json
    for r in reversed(removelist):
        del fjson["utterances"][r[1]]["events"][r[2]]       

    #dump json
    with open(outputjsonfile, "w") as outfile:
        json.dump(fjson, outfile, sort_keys = True, indent = 4, ensure_ascii=False)

if __name__ == '__main__':
    def usage():
        print("usage: %s <input wav dir> <input json dir> <output json dir>" % sys.argv[0])
        sys.exit(1)

    if len(sys.argv) != 4:
        usage()    

    sourcewavdir = sys.argv[1]
    if sourcewavdir[-1] == "/":
        sourcewavdir = sourcewavdir[:-1]
  
    if not os.path.exists(sourcewavdir):
        print "source wav directory not found"
        sys.exit(1)

    sourcejsondir = sys.argv[2]
    if sourcejsondir[-1] == "/":
        sourcejsondir = sourcejsondir[:-1]

    if not os.path.exists(sourcejsondir):
        print "source json directory not found"
        sys.exit(1)

    destwavdir = sys.argv[3]
    if destwavdir[-1] == "/":
        destwavdir = destwavdir[:-1]

    if not os.path.exists(destwavdir):
        os.makedirs(destwavdir)
        
    listing = sorted(os.listdir(sourcewavdir))
    for l in listing:
        if l.lower().endswith("wav") == True:
            ifile = sourcejsondir + "/" + l[:-3] + "json"
            iwavfile = sourcewavdir + "/" + l
            ofile = destwavdir + "/" + l[:-3] + "json"
            print "writing "+ofile
            bleedremoval(iwavfile, ifile, ofile)

