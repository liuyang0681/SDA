#!/usr/bin/env Rscript
library(ggplot2)
library(scales)
library(RColorBrewer)
library(plyr)
library(gridExtra)
library(ggrepel)
library(grid)
library(gtable)
#install.packages("svglite")
suppressPackageStartupMessages(library("argparse"))

script.dir <- dirname(sys.frame(1)$ofile)
setwd(script.dir)
source("ggplot_theme.R")

genome = "Yoruban_feb_2018"
genome = "CHM13"
genome = "Mitchell_CHM1_V2"


asmdir = sprintf("~/Desktop/data/genomeWide/%s/LocalAssemblies/", genome)
refdir = "~/Desktop/work/assemblies/hg38/"
plotsdir = sprintf( "~/Desktop/data/genomeWide/%s/plots/", genome)
if( ! dir.exists(plotsdir)){
  dir.create(plotsdir)
}

# create parser object
parser <- ArgumentParser()
parser$add_argument("-r", "--refdir", default=refdir, help="Input tsv file")
parser$add_argument("-a", "--asmdir", default=asmdir, help="destination folder")
parser$add_argument("-p", "--plotsdir", default=plotsdir, help=" list of unresolved seg dups")
args <- parser$parse_args()

refdir = args$refdir
asmdir = args$asmdir 
segdir = args$segdir
plotsdir = args$plotsdir



file = paste0(refdir, "careAboutGenes.txt")
importantGenes = read.table(file, header=F)
#importantGenes = c("NPIPA5", "CYP4F", "GOLGA8", "GTF2H2", "DEFA5", "HERC2P3", "CXADPR2", "ZNF705G", "BOLA2")
geneRegex = paste(importantGenes$V1, collapse = '|')
geneRegex

m=1
h=15*m
w=35*m
#
# function to save plots 
#
col2=c("#b20000","#000000")  
names(col2) <- (c(FALSE, TRUE))

mysave <- function(name, p){
  ggsave(name, plot = p,  width = w, height = h, units = "cm")
}

file = paste0(asmdir, "betterBlasrMap/mapped.pd")
mapped = read.table(file, header=T)

mapped$clonePerID = mapped$perID_by_matches 
#mapped$referencePerID = mapped$X4
mapped$length = mapped$query_end - mapped$query_start
#mapped$frac_in_aln = (mapped$query_end - mapped$query_start) / mapped$query_length
mapped$referenceLength = mapped$bestEnd - mapped$bestStart

mapped$validated = FALSE
mapped[mapped$clonePerID >= 99.8 & mapped$referencePerID <= 99.8 & mapped$frac_in_aln >= 0.9,
       ]$validated = TRUE

summary(mapped[mapped$validated, "length"])
sum(mapped$validated)





validated = mapped[mapped$validated,]
file2 = paste0(asmdir, "betterBlasrMap/validated.genes.bed")
genes = read.table(file2, header=F)
genes = genes[, c("V4", "V7")]
colnames(genes) = c("query_name", "Gene")
genes = genes[grep("LOC", genes$Gene, invert=TRUE),]
genes <- ddply(genes, .(query_name), summarize,
               Gene=paste(unique(Gene),collapse=", ") )

valGenes = merge(validated, genes, by="query_name", all.x=T)
valGenes = valGenes[order(valGenes$referencePerID), ]
valGenes$ID = NA
valGenes$GeneShow = NA
counter = 1
maxShownGenes = 15
for(i in 1:length(valGenes$Gene)){
  if( counter <= maxShownGenes & !is.na(valGenes[i,]$Gene) ){
    valGenes[i,]$ID = as.character(counter)
    valGenes[i,]$GeneShow = valGenes[i,]$Gene
    counter = counter + 1
  }
  else if(grepl(geneRegex, valGenes[i,]$Gene)){ # prints if evan thinks it is an important gene
    print(valGenes[i,]$Gene)
    valGenes[i,]$ID = as.character(counter)
    valGenes[i,]$GeneShow = valGenes[i,]$Gene
    counter = counter + 1
  }
}


textSize = 60
theme_set(theme_classic(base_size = textSize))

valGenes$ID
mysize = 3
start = round( min(valGenes$referenceLength, valGenes$query_length)/1000 ) -1
valGenes2 = valGenes[!is.na(valGenes$ID),] 
valGenes2$shortGene = gsub(",.*","", valGenes2$GeneShow)
valGenes2$key = paste(paste(valGenes2$ID, valGenes2$shortGene, sep = "\t\t"), round(valGenes2$perID_by_matches,2), sep = "\t\t")




bot = max(95, min(valGenes2$referencePerID) -.5)
top = 100







plots = list()
plots[[1]] =  ggplot(mapped) + geom_point(aes(length, clonePerID, color=validated)) 

plots[[2]] = ggplot(mapped) + geom_point(aes(referenceLength, referencePerID, color=validated))
#coord_cartesian( ylim = c(bot,top)) 

plots[[3]] = ggplot(mapped) + geom_point(aes(referencePerID, clonePerID, color = validated)) +
  coord_cartesian(xlim=c(bot,top), ylim = c(bot,top)) +
  geom_abline(intercept = 0, slope = 1)










plots[[4]] = ggplot() +
  geom_segment(data=valGenes, aes(x=referenceLength, xend=length, y=referencePerID, yend=clonePerID), alpha = 0.25, color="blue") +
  geom_point(data=valGenes, aes(x=referenceLength, y=referencePerID), color=col2[[1]], size=mysize) +
  geom_point(data=valGenes, aes(x=length, y=clonePerID), color=col2[[2]], size=mysize) +
  geom_label_repel(data=valGenes2, aes(x=referenceLength, y=referencePerID, label=ID),
                  size=mysize, fontface="bold" ,#color="black",
                  arrow = arrow(length = unit(0.005, 'npc')),
                  point.padding = .25,
                  box.padding = .5,
                  #ylim=c(NA, 99.8),
                  #show.legend = T, 
                  segment.size = 0.5) +
  geom_point(data=valGenes2, aes(x=0,y=0, fill=key), shape=32)+
  scale_fill_discrete(breaks = valGenes2$key[order(as.numeric(valGenes2$ID))]) +
  scale_x_continuous(breaks=c(start,50,100,150,200)*1000, labels = c(start,50,100,150,200))+
  xlab("Alignment Length (kb)") +
  ylab("Percent Identity") +
  coord_cartesian(ylim = c(bot,top), xlim = c(start,150)*1000 )  +
  theme_classic() + theme(legend.position = "right",
                          legend.key.size = unit(1,"cm"), legend.box.just="left", legend.title=element_blank(), axis.title = element_text(face="bold")) 

mysave(paste0(plotsdir, "cloneVerifiedWithGenes.pdf"), plots[[4]])



















if(F){

dim(validated)
y =sum(validated$length)
x = 46103616 # yoruban 
#x = 16931966 # CHM1
x = 40466964 # CHM13 
y
y/x



file = paste0(asmdir, "/betterBlasrMap/all.genes.bed")
df = read.table(file, header=F)
colnames(df) = c("chr", "start", "end", "id", "perID", "gene")
notLOC = grep("LOC", df[[6]], invert=T)
df = df[notLOC,]

df$Length = df$end-df$start
summary(df$Length)

df$Status = "Diverged"
df$Status[df$perID>99.8] = "Assembled"
df = unique(df)
df = df[order(df$gene, df$perID),]
ggplot(df) + geom_bar(aes(Status, fill=Status))




totalbp=sum(df$Length)

bpid = c( 100, rep(df$perID, round(df$Length/1000) ) )
bpid = data.frame(perID=bpid)
bpid$Status  = "Diverged"
bpid$Status[bpid$perID >= 99.8 ] = "Assembled"
bpid$Mb_of_Assembly = ecdf(bpid$perID)(bpid$perID)*totalbp/1000000
dim(bpid)
bpid = bpid[bpid$Mb_of_Assembly > 1, ]

ggplot(bpid, aes(x=perID, y=Mb_of_Assembly)) + geom_line() + 
  geom_ribbon(aes(ymin=0,ymax=Mb_of_Assembly, fill=Status)) + 
  myTheme + scale_fill_manual(values=col4)



df

geneRegex = paste0(geneRegex, "|NOTCH.*|SRGAP2.*")
important = df[ grepl(geneRegex, df$gene), ]
important


}





