#!/bin/env python
import numpy as np
import matplotlib.pyplot as plt
#import matplotlib.ticker.FuncFormatter
#from sklearn.mixture import GaussianMixture
import argparse 


parser = argparse.ArgumentParser()
parser.add_argument("--nucfreq", help="assembly.consensus.nucfreq", default="assembly.consensus.nucfreq")
parser.add_argument("--png", help="png", default="Coverage.png")
parser.add_argument("--automin", help="autoMinCoverage", default="autoMinCoverage")
parser.add_argument("--automax", help="autoMaxCoverage", default="autoMaxCoverage")
args = parser.parse_args()

nucfreq=args.nucfreq
autoMin=args.automin
autoMax=args.automax


colnames = ["contig", "pos", "A", "C", "G", "T", "deletion", "insertion"]

f = open(nucfreq)
first  = []
second = []
third = []
truepos= []
for line in f:
    line = line.split()
    truepos.append(int(line[1]))
    bases = []
    for basepair in line[2:6]:
        bases.append(int(basepair))
    bases = sorted(bases, reverse=True)
    first.append(bases[0])
    second.append(bases[1])
    third.append(bases[3])
pos = np.array( range(0,len(second)) ) 
first = np.array(first)
second = np.array(second)
third = np.array(third)
truepos = np.array(truepos)
truepos = pos

plt.rc('font', family='serif')

fig, ax = plt.subplots( figsize=(16,9) )
prime, = plt.plot(truepos, first, 'o', color="black", markeredgewidth=0.0, markersize=1, label = "most frequent base pair")
#plt.gca().set_ylim(top=300)
sec, = plt.plot(truepos, second,'o', color="red",   markeredgewidth=0.0, markersize=1, label = "second most frequent base pair")
#tri, = plt.plot(truepos, third,'o', color="green",   markeredgewidth=0.0, markersize=1, label = "forth most frequent base pair")
ax.set_xlabel('BP Position')
ax.set_ylabel('Depth')

ylabels = [format(label, ',.0f') for label in ax.get_yticks()]
xlabels = [format(label, ',.0f') for label in ax.get_xticks()]
ax.set_yticklabels(ylabels)
ax.set_xticklabels(xlabels)

# Hide the right and top spines
ax.spines["right"].set_visible(False)
ax.spines["top"].set_visible(False)
# Only show ticks on the left and bottom spines
ax.yaxis.set_ticks_position('left')
ax.xaxis.set_ticks_position('bottom')

plt.legend()

plt.savefig(args.png)




