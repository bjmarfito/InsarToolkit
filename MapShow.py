#!/usr/bin/env python3 
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Plot most types of Insar products, including complex 
#  images and multi-band images
# 
# by Rob Zinke 2019 
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import sys 
import numpy as np 
import matplotlib.pyplot as plt 
from scipy.stats import mode
from osgeo import gdal 


### --- Parser --- ###
def createParser():
	'''
		Plot most types of Insar products, including complex images and multiband images.
	'''

	import argparse
	parser = argparse.ArgumentParser(description='Plot most types of Insar products, including complex images and multiband images')
	# Necessary 
	parser.add_argument(dest='imgfile', type=str, help='File to plot')
	# Options
	parser.add_argument('-b','--band', dest='band', default=1, type=int, help='Band to display. Default = 1')
	parser.add_argument('-ds', '--downsample', dest='dsample', default='0', type=int, help='Downsample factor (power of 2). Default = 2^0 = 1')
	parser.add_argument('-vmin','--vmin', dest='vmin', default=None, type=float, help='Min display value')
	parser.add_argument('-vmax','--vmax', dest='vmax', default=None, type=float, help='Max display value')
	parser.add_argument('-pctmin','--pctmin', dest='pctmin', default=0, type=float, help='Min value percent')
	parser.add_argument('-pctmax','--pctmax', dest='pctmax', default=100, type=float, help='Max value percent')
	parser.add_argument('-bg','--background', dest='background', default=None, help='Background value. Default is None. Use \'auto\' for outside edge of image.')
	parser.add_argument('-v','--verbose', dest='verbose', action='store_true', help='Verbose')
	parser.add_argument('--plot_complex', dest='plot_complex', action='store_true', help='Plot amplitude image behind phase')
	parser.add_argument('-hist','--hist', dest='hist', action='store_true', help='Show histogram')
	parser.add_argument('--nbins', dest='nbins', default=50, type=int, help='Number of histogram bins. Default = 50')

	return parser

def cmdParser(iargs = None):
	parser = createParser()
	return parser.parse_args(args=iargs)



### --- Main function --- ###
if __name__=='__main__':
	# Gather arguments
	inpt=cmdParser()

	## Basic parameters
	# Open image using gdal
	DS=gdal.Open(inpt.imgfile,gdal.GA_ReadOnly)
	nBands=DS.RasterCount # number of image bands

	# Geo transform
	M=DS.RasterYSize; N=DS.RasterXSize
	T=DS.GetGeoTransform()
	left=T[0]; dx=T[1]; right=left+N*dx 
	top=T[3]; dy=T[5]; bottom=top+M*dy 
	extent=(left, right, bottom, top)

	# Report basic parameters
	if inpt.verbose is True:
		print('Image: {}'.format(inpt.imgfile))
		print('BASIC PARAMETERS')
		print('Number of bands: {}'.format(nBands))
		print('Spatial extent: {}'.format(extent))
		print('Pixel size (x) {}; (y) {}'.format(dx,dy))


	## Image properties
	# Load image
	img=DS.GetRasterBand(inpt.band).ReadAsArray()

	# Image type (real/complex)
	datatype=type(img[0,0])
	if isinstance(img[0,0],np.complex64):
		imgMag=np.abs(img) # amplitude
		img=np.angle(img) # phase

	# Background value
	if inpt.background=='auto':
		# Auto-determine background value
		edgeValues=np.concatenate([img[0,:],img[-1,:],img[:,0],img[:,-1]])
		background=mode(edgeValues).mode[0] # most common value
	else:
		# Use prescribed value
		background=inpt.background 

	if inpt.background:
		mask=(img==background) # mask values
		img=np.ma.array(img,mask=mask) # mask main image array

	# Report
	if inpt.verbose is True:
		print('IMAGE PROPERTIES')
		print('data type: {}'.format(datatype))
		if inpt.background:
			print('background value: {:16f}'.format(background))


	## Image statistics
	imgArray=img.reshape(-1,1) # reshape 2D image as 1D array

	# Ignore background values
	if inpt.background:
		maskArray=mask.reshape(-1,1) # reshape mask from 2D to 1D
		imgArray=imgArray[maskArray==False] # mask background values

	# Ignore "outliers"
	if inpt.vmin:
		imgArray=imgArray[imgArray>=inpt.vmin]
	if inpt.vmax:
		imgArray=imgArray[imgArray<=inpt.vmax]

	# Percentages
	vmin,vmax=np.percentile(imgArray,(inpt.pctmin,inpt.pctmax))
	imgArray=imgArray[imgArray>=vmin]
	imgArray=imgArray[imgArray<=vmax]

	# Histogram analysis
	Hvals,Hedges=np.histogram(imgArray,bins=inpt.nbins)
	Hcntrs=(Hedges[:-1]+Hedges[1:])/2 # centers of bin edges

	# Report
	if inpt.verbose is True:
		print('IMAGE STATISTICS')
		if inpt.background:
			print('Ignoring background value')
		if inpt.vmin:
			print('vmin: {}'.format(inpt.vmin))
		if inpt.vmax:
			print('vmax: {}'.format(inpt.vmax))
		print('Upper left value: {:.16f}'.format(img[0,0]))


	## Main plot
	# Downsample factor
	dsample=int(2**inpt.dsample)

	F=plt.figure() 
	ax=F.add_subplot(111) 
	if inpt.plot_complex is True:
		print('Plot complex does not work yet')
	cax=ax.imshow(img[::dsample,::dsample],vmin=vmin,vmax=vmax)
	F.colorbar(cax,orientation='horizontal') 


	## Plot histogram
	if inpt.hist is True:
		Fhist=plt.figure()
		axHist=Fhist.add_subplot(111)
		markerline, stemlines, baseline = plt.stem(Hcntrs, Hvals, 
			linefmt='r',markerfmt='',use_line_collection=True)
		stemlines.set_linewidths(None); baseline.set_linewidth(0)
		axHist.plot(Hcntrs,Hvals,'k',linewidth=2)
		axHist.set_ylim([0.95*Hvals.min(),1.05*Hvals.max()])


	plt.show() 