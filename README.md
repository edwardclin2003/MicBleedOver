This program takes a VOCI speech decoding JSON (speech recognition output) and a dual channel audio file, then finds locations where the microphone bleed over occurs and cleans up the JSON decoding according to which channel has more power in those regions so words don't show up on both channels.

Usage: python bleedover.py <input wav dir> <input JSON dir> <output JSON dir>

The wav filename and JSON filename must both exist (in the wav dir and the JSON dir) for this program to work.  The only difference is that one extension is .wav and the other is .json.

No JSON files will be provided for this repo cuz Voci decoding format is proprietary.  However the approach to removing mic bleed used in this program is effective.

Conceptually the code does the following:
1. Run speech recognition across both audio channels.
2. Find regions where words are found on both channels at the same time.
3. Track the power levels for those regions and select the channel that has the most power
4. Fix the speech recognition output according to the power heuristic.  You may also fix the audio file itself with some modification of the code.
