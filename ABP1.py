import os

snake_dir = os.path.dirname(workflow.snakefile) + "/"
shell.executable("/bin/bash")
#shell.prefix("source %s/env_python2.cfg; set -eo pipefail; " % SNAKEMAKE_DIR)
shell.prefix("source %s/env_python2.cfg; set -eo pipefail; " % snake_dir)

#
# script locations and configurations 
#
configFile = "abp.config.json"
configfile:
	configFile	

MINCOV=config["MINCOV"]
MAXCOV=config["MAXCOV"]
MINTOTAL=config["MINTOTAL"]

blasr = snake_dir + "software/blasr/bin/blasr"
sourceblasr = "source {}env_blasr.cfg".format( snake_dir ) # get the balsr enviorment from the balsr env file
blasr43 = snake_dir + "software/blasr/bin/blasr43"
samtobas = snake_dir + "software/blasr/bin/samtobas"
quiver = snake_dir + "software/quiver/quiver"
quiver_source = snake_dir + "software/quiver/setup_quiver.sh"
base = snake_dir + "scripts/"
scriptsDir = '/net/eichler/vol5/home/mchaisso/projects/AssemblyByPhasing/scripts/abp'
python3 = snake_dir + "env_python3.cfg"
#
#
#

print(snake_dir)
print("MINCOV:{}\nMAXCOV:{}\nMINTOTAL:{}".format(MINCOV, MAXCOV, MINTOTAL))

rule all:	
	input:
		dupbed="ref.fasta.bed",
		pdf='CC/mi.cuts.gml.pdf',
		groups=dynamic("group.{n}.vcf"),
		png="Coverage.png",
		depth="snvs/depth.tsv",

#
# This realigns reads with match/mismatch parameters that make it more
# likely to align a PSV as a mismatch rather than paired insertion and
# deletion.
#
minaln="500"
if(os.path.exists("reads.orig.bam")):
	rule preprocess_reads:
		input:
			'reads.orig.bam'
		output:
			'reads.bas.h5'
		shell:
			'samtools view -h {input} | {samtobasi} /dev/stdin {output}'

	rule realign_reads:
		input:
			reads = 'reads.orig.bam',
			ref='ref.fasta',
		output:
			"reads.bam"
		threads:
			8
		shell: 
			"""
			{sourceblasr}
			# the grep line removes references to previous alignment references 
			samtools view -h {input.reads} | \
				grep -v "^@SQ" | \
				blasr /dev/stdin {input.ref} \
				-clipping soft \
				-passthrough \
				-streaming \
				-fileType sam \
				-sam \
				-out /dev/stdout \
				-nproc {threads} -bestn 1 \
				-mismatch 3 -insertion 9 -deletion 9 \
				-minAlignLength {minaln} | \
				 samtools view -bS -F 4 - | \
				 samtools sort -m 4G -T tmp -o {output}
				
				
				#pbsamstream - | \
				# the above sets tlen in the sam to zero for some reason. 
				#-m 4 
			"""

elif(os.path.exists("reads.orig.fasta")):
    rule realign_reads_fasta:
        input:
            basreads='reads.orig.fasta', 
            ref='ref.fasta'
        output:
            "reads.bam"
        shell: 
            """
			{sourceblasr}
			blasr {input.basreads} {input.ref}  \
					-sam -preserveReadTitle -clipping subread -out /dev/stdout \
					-nproc {threads} -bestn 1 \
                    -mismatch 3 -insertion 9 -deletion 9 \
                    -minAlignLength {minaln} | \
                     samtools view -bS -F 4 - | \
                     samtools sort -m 4G -T tmp -o {output}
            """

elif(os.path.exists("reads.fofn")):
    rule get_reads_that_map:
        input:
            basreads='reads.fofn', 
            ref='ref.fasta'
        output:
            "reads.bam"
        threads: 8
        shell: 
            """
			{sourceblasr}
			blasr {input.basreads} {input.ref}  \
					-sam -preserveReadTitle -clipping none -out /dev/stdout \
					-nproc {threads} -bestn 1 \
                    -mismatch 3 -insertion 9 -deletion 9 \
                    -minAlignLength {minaln} | \
                     samtools view -bS -F 4 - | \
                     samtools sort -m 4G -T tmp -o {output}
            """

else:
	print("NO INPUT READS!!!")
	exit()


rule index_realigned_reads:
	input:
		"reads.bam"		
	output:
		"reads.bam.bai"	
	shell:
		'samtools index {input}'	

#
# get fasta from bam
#
rule reads_to_fasta:
    input:
        "reads.bam"
    output:
        "reads.fasta"
    shell:
        '''samtools view {input} | awk '{{ print ">"$1; print $10; }}' > {output}'''



#
# get a depth profile and reads in a fasta format
#
rule depthFromBam:
    input:
        reads="reads.fasta",
        bam="reads.bam",
    output:
        depth="snvs/depth.tsv"
    shell:
        """
        samtools depth -aa {input.bam} > {output.depth}
        """



#
#
# lets just look at teh het profile
#
rule hetProfile:
    input:
        reads="reads.bam",
        ref="ref.fasta"	,
    output: 
        nucfreq="snvs/nofilter.consensus.nucfreq",
    shell:
        """
		samtools mpileup -q 0 -Q 0 {input.reads} | \
				{base}/MpileupToFreq.py  /dev/stdin | \
				{base}/PrintHetFreq.py 0 \
				--maxCount 100 \
				--minTotal 0 \
				> {output.nucfreq}

        """
rule thresholdProfile:
    input:
        nucfreq="snvs/nofilter.consensus.nucfreq",
    output: 
        png="Coverage.png",
    shell:
        """
		source {python3}
		{base}/autoThreshold.py --nucfreq {input.nucfreq} --plot {output.png} 
        """

#
# Given the alignments, count the frequency of each base at every
# position, and estimate the SNVs from this frequency. 
#
rule create_SNVtable_from_reads:
	input:
		reads="reads.bam",
		ref="ref.fasta"	,
	output: 
		snv="snvs/assembly.consensus.fragments.snv",
		vcf="snvs/assembly.consensus.nucfreq.vcf",
		nucfreq="snvs/assembly.consensus.nucfreq",
		filt="snvs/assembly.consensus.nucfreq.filt",
		frag="snvs/assembly.consensus.fragments",
	shell:
		"""
		echo "Sam to nucfreq"
		samtools mpileup -q 0 -Q 0 {input.reads} | \
				{base}/MpileupToFreq.py  /dev/stdin | \
				{base}/PrintHetFreq.py {MINCOV} \
				--maxCount {MINCOV} \
				--minTotal {MINTOTAL} \
				> {output.nucfreq}
		
		echo "filter nucfreq"
		samtools view -h {input.reads} | \
				{base}/readToSNVList  \
				--nft {output.nucfreq} \
				--sam /dev/stdin \
				--ref {input.ref} \
				--minFraction 0.01 \
				--minCoverage {MINCOV} \
				--out {output.frag} \
				--nftOut {output.filt}
		
		echo "filtered to vcf"
		{scriptsDir}/FreqToSimpleVCF.py --freq {output.filt} \
				--ref {input.ref} \
				--out {output.vcf} 
		
		echo "vcf to snv"
		{scriptsDir}/FragmentsToSNVList.py  \
				--fragment \
				--frags {output.frag} \
				--vcf {output.vcf} \
				--out {output.snv}


		"""


#
# Create a matrix with one row per read, and one column per PSV.  
#  . - read is ref base
#  1 - read is PSV
#  n - no signal (indel or read ended)
#
rule SNVtable_to_SNVmatrix:
    input:
        snv="snvs/assembly.consensus.fragments.snv"	
    output:
        mat="snvs/assembly.consensus.fragments.snv.mat",
        snvsPos="snvs/assembly.consensus.fragments.snv.pos"
    shell:
       '{scriptsDir}/FragmentSNVListToMatrix.py {input.snv} --named --pos {output.snvsPos} --mat {output.mat}'  

#
# create duplicaitons.fasta
# this was moved to the pre processing step 
#

#
# Set up the ground truth if it exists.  Map the collapsed sequence
#
if( os.path.exists("duplications.fasta") and os.path.getsize("duplications.fasta") > 0 ):
	rule depthOnDuplications:
		input:
			reads="reads.fasta",
			ref = ancient( "duplications.fasta" ),
		output:
			bam = "dup/reads.dup.bam",
			depth="dup/dup_depth.tsv",
		threads:8
		shell:
			"""
			{sourceblasr}
			blasr -sam  \
					-nproc {threads} -out /dev/stdout \
					-minAlignLength 500 -preserveReadTitle -clipping subread \
					{input.reads} {input.ref} | \
					samtools view -bSh -F 4 - | \
					samtools sort -T tmp -o {output.bam}
			
			samtools depth -aa {output.bam} > {output.depth}
			"""

	rule realignReads_to_Dups:
		input:
			depth="dup/dup_depth.tsv",
			reads = "reads.fasta",
			genome = ancient( "duplications.fasta" ),
		output:
			"dup/reads.dups.m4",
		threads: 8 
		shell:
			'{sourceblasr}; blasr {input.reads} {input.genome} -m 4 -bestn 1 -preserveReadTitle -out {output} -nproc {threads}'

	rule orderMatByalignments: #get more explanation
		input:
			"snvs/assembly.consensus.fragments.snv.mat",
			"dup/reads.dups.m4"
		output:
			"snvs/assembly.consensus.fragments.snv.mat.categorized"
		shell:
			'{scriptsDir}/sorting/OrderMatByAlignments.py {input}  > {output}'

else:
	rule ifNoDuplicationsFasta:
		input:
			"snvs/assembly.consensus.fragments.snv.mat"
		output:
			"snvs/assembly.consensus.fragments.snv.mat.categorized"
		shell:
			"""
			# this adds a fake catigory on the end
			cat {input} | awk '{{ print $1"\t"$2"\tall"}}' > {output}
			"""


#
# This finds PSVs that are connected by a sufficient number of
# sequences, and creates the PSV graph. This will have merged components.
#
rule createPSVgraph:
	input:
		matrix="snvs/assembly.consensus.fragments.snv.mat.categorized",
		vcf="snvs/assembly.consensus.nucfreq.vcf"
	output:
		graph="CC/mi.gml",
		adj="CC/mi.adj",
		mi="CC/mi.mi",
	shell:
		"""
		{scriptsDir}/PairedSNVs.py {input.matrix} --minCov {MINCOV} --maxCov {MAXCOV} \
				--mi {output.mi} --graph {output.graph} --adj {output.adj} \
				--minNShared 5 --minLRT 1.5 --vcf {input.vcf}
		"""


#
# generate repulsion edges 
#
rule GenerateRepulsion:
	input:
		graph="CC/mi.gml",
		mi="CC/mi.mi",
	output:
		rep = "CC/mi.repulsion",
	shell:
		"""
		{base}/GenerateRepulsion.py --shared 5 --lrt 1.5 --max 3 --gml {input.graph} --mi {input.mi} --out {output.rep}
		"""

runIters = True
runIters = False
posFile = "CC/mi.gml"
if(runIters and os.path.exists(posFile)):
	print("Going to export iterations of CC for debugging")
	#showIters = " --exportEachIteration --layout {} ".format(posFile)	
	showIters = " --exportEachIteration "
	convert = "convert extraCCplots/iteration.*.png extraCCplots/all_cc_iterations.pdf"
else:
	showIters = ""
	convert = ""
#
# Run correlation clustering to try and spearate out the graph.  Swap
# is a 'simulated annealing' type parameters. The factor parameter
# controls for how many negative edges are added for every positive edge.
#
rule correlationClustering:
	input:
		graph="CC/mi.gml",
		rep = "CC/mi.repulsion",
	output:
		out="CC/mi.cuts.gml",
		sites="CC/mi.gml.sites",
		cuts="CC/mi.gml.cuts",
	shell:
		"""	
		mkdir -p extraCCplots
		rm -rf extraCCplots/*

		{scriptsDir}/MinDisagreeClusterByComponent.py  \
			--graph {input.graph} \
			--repulsion {input.rep} \
			--niter 10000 --swap 1000000 --factor 1 \
			--plotRepulsion {showIters} \
			--cuts {output.cuts} --sites {output.sites} --out {output.out}
			#--seed \
	
		# it running all iteraitons convert them into a booklet
		{convert}
		
		"""



rule index_ref_fasta:
	input:
		"ref.fasta"
	output:
		"ref.fasta.fai"
	shell:
		'samtools faidx {input}'


#
# Correlation clustering defines a set of cuts that separate out
# connected components.  This takes the cuts and makes a vcf file for
# each component.
#
rule makeCutsInPSVgraph:
	input:
		refIdx="ref.fasta.fai",
		cuts="CC/mi.gml.cuts",
		snvsPos="snvs/assembly.consensus.fragments.snv.pos",
		vcf="snvs/assembly.consensus.nucfreq.vcf"	
	output:
		vcfs=dynamic("group.{n}.vcf"), 
	params:
		comps="CC/mi.comps.txt", 
	shell:
		"""
		rm -rf group.*
		{scriptsDir}/CutsToPhasedVCF.py {input.cuts} {input.snvsPos} {input.vcf} \
				--minComponent 4 \
				--ref {input.refIdx} \
				--summary {params.comps}
		"""


#
# makes a gephi version of the plot, 
# much nice imo 
#
rule gephi:
	input:
		cuts="CC/mi.cuts.gml"
	output:
		pdf="CC/mi.cuts.gml.pdf",
	run:
		shell("mkdir -p extraCCplots")
		shell("source {python3}; {base}/gephi/gephi.sh {input.cuts} mi.cuts.gml" )
		shell("mv mi.cuts.gml.pdf {output.pdf}")
		collapse = os.path.basename(os.getcwd()) + ".pdf"
		shell("cp " + output["pdf"] + " " + collapse)



