//#############################################################################
//
//   coverageEstimators.h
//
//   Methods for estimating coverage values from pileups
//
//   Copyright (C) Michael Imelfort, Ben Woodcroft
//
//   This library is free software; you can redistribute it and/or
//   modify it under the terms of the GNU Lesser General Public
//   License as published by the Free Software Foundation; either
//   version 3.0 of the License, or (at your option) any later version.
//
//   This library is distributed in the hope that it will be useful,
//   but WITHOUT ANY WARRANTY; without even the implied warranty of
//   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
//   Lesser General Public License for more details.
//
//   You should have received a copy of the GNU Lesser General Public
//   License along with this library.
//
//#############################################################################

#ifndef BM_COV_ESTIMATOR
  #define BM_COV_ESTIMATOR

// system includes
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// there are several different definitions of coverage types
typedef enum {CT_NONE,           // do not calculate coverage
              CT_COUNT,          // read counts, unaffected by contig length
              CT_C_MEAN,         // read counts, divided by contig length
              CT_P_MEAN,         // mean pileup depth
              CT_P_MEDIAN,       // median pileup depth
              CT_P_MEAN_TRIMMED, // pileup mean trancated based on upper lower %
              CT_P_MEAN_OUTLIER, // pileup mean trancated based on distributions
              } CT;

/*! @typedef
 * @abstract Structure for storing information about a coverage type
 *
 * @field type                Identifies the method used to calculate coverage
 * @field upperCut            Upper bound cutoff for coverage calculation
 * @field lowerCut            Lower bound cutoff for coverage calculation
 */
 typedef struct BM_coverageType {
    CT type;
    float upperCut;
    float lowerCut;
 } BM_coverageType;

/*!
 * @abstract Estimate the coverage along a single contig given pileup
 *           information and a coverage type to calculate
 *
 * @param  coverageValues   array of floats to set (len == numBams)
 * @param  data             matrix of int pileup depths or read start depths
 *                          size == (numBams x contigLength)
 * @param  BM_coverageType  BM_coverageType struct with initialised values
 * @param  contigLength     Length of the contig being assesed
 * @param  numBams          the number of bams responsible for the pileup
 * @return void
 *
 * @discussion This function is essentially a wrapper that calls specific
 * coverage calculators based on the type of coverage supplied. It updates the
 * values in coverageValues before exiting.
 */
void estimateCoverages(float * coverageValues,
                       uint32_t ** data,
                       BM_coverageType * covType,
                       uint32_t contigLength,
                       uint32_t numBams
                       );

/*!
 * @abstract Estimate the raw read count coverage along a single contig
 *
 * @param  readStarts       array of int read starts (len == contigLength)
 * @param  BM_coverageType  BM_coverageType struct with initialised values
 * @param  contigLength     Length of the contig being assesed
 * @return float that is the calculated coverage
 *
*/
float estimate_COUNT_Coverage(uint32_t * readStarts,
                              BM_coverageType * covType,
                              uint32_t contigLength);

/*!
 * @abstract Estimate the mean read count coverage along a single contig
 *
 * @param  readStarts       array of int read starts (len == contigLength)
 * @param  BM_coverageType  BM_coverageType struct with initialised values
 * @param  contigLength     Length of the contig being assesed
 * @return float that is the calculated coverage
 *
*/
float estimate_C_MEAN_Coverage(uint32_t * readStarts,
                               BM_coverageType * covType,
                               uint32_t contigLength);

/*!
 * @abstract Estimate the mean pileup coverage along a single contig given
 *           pileup information
 *
 * @param  pileupValues     array of int read starts (len == contigLength)
 * @param  BM_coverageType  BM_coverageType struct with initialised values
 * @param  contigLength     Length of the contig being assesed
 * @return float that is the calculated coverage
 *
*/
float estimate_P_MEAN_Coverage(uint32_t * pileupValues,
                               BM_coverageType * covType,
                               uint32_t contigLength);


/*!
 * @abstract Estimate the median pileup coverage along a single contig given
 *           pileup information
 *
 * @param  pileupValues     array of int read starts (len == contigLength)
 * @param  BM_coverageType  BM_coverageType struct with initialised values
 * @param  contigLength     Length of the contig being assesed
 * @return float that is the calculated coverage
 *
 * @discussion This function alters the order of pileupValues
*/
float estimate_P_MEDIAN_Coverage(uint32_t * pileupValues,
                                 BM_coverageType * covType,
                                 uint32_t contigLength);

/*!
 * @abstract Estimate trimmed mean pileup coverage (not truncated,
 *           outlier coverage) along a single contig given pileup information
 *           and percentage of the data to exclude at the upper and lower limits
 *
 * @param  pileupValues     array of int read starts (len == contigLength)
 * @param  BM_coverageType  BM_coverageType struct with initialised values
 * @param  contigLength     Length of the contig being assesed
 * @return float that is the calculated coverage
 *
 */
float estimate_P_MEAN_TRIMMED_Coverage(uint32_t * pileupValues,
                                       BM_coverageType * covType,
                                       uint32_t contigLength);

/*
 * @abstract Estimate truncated mean (outlier) pileup coverage along a single
 *           contig given pileup information and a symetric stdev cutoff
 *
 * @param  pileupValues     array of int read starts (len == contigLength)
 * @param  BM_coverageType  BM_coverageType struct with initialised values
 * @param  contigLength     Length of the contig being assesed
 * @return float that is the calculated coverage
*/
float estimate_P_MEAN_OUTLIER_Coverage(uint32_t * pileupValues,
                                       BM_coverageType * covType,
                                       uint32_t contigLength);
        /***********************
        ***   MATHY EXTRAS   ***
        ***********************/
/*!
 * @abstract Calculate the median of an array values
 *
 * @param  values       array of (integer) values
 * @param  size         size of values array
 * @return float        the caluclated median
 *
 * MODIFIES THE ORDER OF VALUES IN values ARRAY!
 */
float BM_median(uint32_t * values, uint32_t size);

/*!
 * @abstract Calculate the mean of an array values
 *
 * @param  values       array of (integer) values
 * @param  size         size of values array
 * @return float        the caluclated mean
 */
float BM_mean(uint32_t * values, uint32_t size);

/*!
 * @abstract Calculate the standard deviations of an array values
 *
 * @param  values       array of (integer) values
 * @param  size         size of values array
 * @param  m            mean of the values array
 * @return float        the caluclated standard deviation
 */
float BM_stdDev(uint32_t * values, uint32_t size, float m);

/*!
 * @abstract Calculate the standard deviations of an array values
 *
 * @param  values       array of (integer) values
 * @param  size         size of values array
 * @return float        the caluclated standard deviation
 *
 * @discussion Everything is 3 stdevs from the mean right?
*/
float BM_fakeStdDev(uint32_t * values, uint32_t size);


#ifdef __cplusplus
}
#endif

#endif // BM_COV_ESTIMATOR

