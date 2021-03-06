#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
A reconstruction class for regularised iterative methods:
-- Regularised FISTA algorithm (A. Beck and M. Teboulle,  A fast iterative 
                               shrinkage-thresholding algorithm for linear inverse problems,
                               SIAM Journal on Imaging Sciences, vol. 2, no. 1, pp. 183–202, 2009.)
-- SIRT, CGLS algorithms from ASTRA

Dependencies: 
    * astra-toolkit, install conda install -c astra-toolbox astra-toolbox
    * CCPi-RGL toolkit (for regularisation), install with 
    conda install ccpi-regulariser -c ccpi -c conda-forge
    or https://github.com/vais-ral/CCPi-Regularisation-Toolkit

GPLv3 license (ASTRA toolbox)
@author: Daniil Kazantsev: https://github.com/dkazanc
"""

import numpy as np
from numpy import linalg as LA

class RecToolsIR:
    """ 
    A class for iterative reconstruction algorithms using ASTRA and CCPi RGL toolkit
    """
    def __init__(self, 
              DetectorsDimH,  # DetectorsDimH # detector dimension (horizontal)
              DetectorsDimV,  # DetectorsDimV # detector dimension (vertical) for 3D case only
              AnglesVec, # array of angles in radians
              ObjSize, # a scalar to define reconstructed object dimensions
              datafidelity,# data fidelity, choose LS, PWLS, GH (wip), Student (wip)
              OS_number, # the number of subsets, NONE/(or > 1) ~ classical / ordered subsets
              tolerance, # tolerance to stop outer iterations earlier
              device):
        if ObjSize is tuple: 
            raise (" Reconstruction is currently available for square or cubic objects only, provide a scalar ")
        else:
            self.ObjSize = ObjSize # size of the object
        
        self.tolerance = tolerance
        self.datafidelity = datafidelity
        self.OS_number = OS_number
        
        if device is None:
            self.device = 'gpu'
        else:
            self.device = device
        if ((datafidelity != 'LS') and (datafidelity != 'PWLS')):
                raise('Unknown data fidelity type, select: LS or PWLS')
        
        if DetectorsDimV is None:
            # Creating Astra class specific to 2D parallel geometry
            if ((OS_number is None) or (OS_number <= 1)):
                # classical approach
                from tomorec.supp.astraOP import AstraTools
                self.Atools = AstraTools(DetectorsDimH, AnglesVec, ObjSize, device) # initiate 2D ASTRA class object
                self.OS_number = 1
            else:
                # Ordered-subset approach
                from tomorec.supp.astraOP import AstraToolsOS
                self.Atools = AstraToolsOS(DetectorsDimH, AnglesVec, ObjSize, self.OS_number, device) # initiate 2D ASTRA class OS object
            self.geom = '2D'
        else:
            # Creating Astra class specific to 3D parallel geometry
            self.geom = '3D'
            if ((OS_number is None) or (OS_number <= 1)):
                from tomorec.supp.astraOP import AstraTools3D
                self.Atools = AstraTools3D(DetectorsDimH, DetectorsDimV, AnglesVec, ObjSize) # initiate 3D ASTRA class object
                self.OS_number = 1
            else:
                # Ordered-subset 
                from tomorec.supp.astraOP import AstraToolsOS3D
                self.Atools = AstraToolsOS3D(DetectorsDimH, DetectorsDimV, AnglesVec, ObjSize, self.OS_number) # initiate 3D ASTRA class OS object
    
    def SIRT(self, sinogram, iterations):
        if (self.OS_number > 1):
            raise('There is no OS mode for SIRT yet, please choose OS = None')
        #SIRT reconstruction algorithm from ASTRA
        if (self.geom == '2D'):
            SIRT_rec = self.Atools.sirt2D(sinogram, iterations)
        if (self.geom == '3D'):
            SIRT_rec = self.Atools.sirt3D(sinogram, iterations)
        return SIRT_rec

    def CGLS(self, sinogram, iterations):
        if (self.OS_number > 1):
            raise('There is no OS mode for CGLS yet, please choose OS = None')
        #CGLS reconstruction algorithm from ASTRA
        if (self.geom == '2D'):
            CGLS_rec = self.Atools.cgls2D(sinogram, iterations)
        if (self.geom == '3D'):
            CGLS_rec = self.Atools.cgls3D(sinogram, iterations)
        return CGLS_rec

    def powermethod(self, weights = None):
        # power iteration algorithm to  calculate the eigenvalue of the operator (projection matrix)
        # weights (raw projection data) are required for PWLS fidelity (self.datafidelity = PWLS), otherwise ignored
        niter = 15 # number of power method iterations
        s = 1.0
        if (self.geom == '2D'):
            x1 = np.float32(np.random.randn(self.Atools.ObjSize,self.Atools.ObjSize))
        else:
            x1 = np.float32(np.random.randn(self.Atools.ObjSize,self.Atools.ObjSize,self.Atools.ObjSize))
        if (self.datafidelity == 'PWLS'):
            if weights is None: 
                raise ValueError('The selected data fidelity is PWLS, hence the raw projection data must be provided to the function')
            else:
                sqweight = np.sqrt(weights)
        if (self.OS_number == 1):
            # non-OS approach
            y = self.Atools.forwproj(x1)
            if (self.datafidelity == 'PWLS'):
                y = np.multiply(sqweight, y)
            for iter in range(0,niter):
                x1 = self.Atools.backproj(y)
                s = LA.norm(x1)
                x1 = x1/s
                y = self.Atools.forwproj(x1)
                if (self.datafidelity == 'PWLS'):
                    y = np.multiply(sqweight, y)
        else:
            # OS approach
            y = self.Atools.forwprojOS(x1,0)
            if (self.datafidelity == 'PWLS'):
                y = np.multiply(sqweight[self.Atools.newInd_Vec[0,:],:], y)
            for iter in range(0,niter):
                x1 = self.Atools.backprojOS(y,0)
                s = LA.norm(x1)
                x1 = x1/s
                y = self.Atools.forwprojOS(x1,0)
                if (self.datafidelity == 'PWLS'):
                    y = np.multiply(sqweight[self.Atools.newInd_Vec[0,:],:], y)
        return s
    
    def FISTA(self, 
              projdata, # tomographic projection data in 2D (sinogram) or 3D array
              weights = None, # raw projection data for PWLS model
              InitialObject = 0, # initialise reconstruction with an array
              lipschitz_const = 5e+06, # can be a given value or calculated using Power method
              iterationsFISTA = 100, # the number of OUTER FISTA iterations
              regularisation = None, # enable regularisation  with CCPi - RGL toolkit
              regularisation_parameter = 0.01, # regularisation parameter if regularisation is not None
              regularisation_parameter2 = 0.01, # 2nd regularisation parameter (LLT_ROF method)
              regularisation_iterations = 100, # the number of INNER iterations for regularisation
              time_marching_parameter = 0.0025, # gradient step parameter (ROF_TV, LLT_ROF, NDF, DIFF4th) penalties
              tolerance_regul = 1e-06,  # tolerance to stop regularisation
              TGV_alpha1 = 1.0, # TGV specific parameter for the 1st order term
              TGV_alpha2 = 0.8, # TGV specific parameter for the 2st order term
              TGV_LipschitzConstant = 12.0, # TGV specific parameter for convergence
              edge_param = 0.01, # edge (noise) threshold parameter for NDF and DIFF4th
              NDF_penalty = 1, # NDF specific penalty type: 1 - Huber, 2 - Perona-Malik, 3 - Tukey Biweight
              NLTV_H_i = 0, # NLTV-specific penalty type, the array of i-related indices
              NLTV_H_j = 0, # NLTV-specific penalty type, the array of j-related indices
              NLTV_Weights = 0, # NLTV-specific penalty type, the array of Weights
              methodTV = 0, # 0/1 - isotropic/anisotropic TV
              nonneg = 0 # 0/1 disabled/enabled nonnegativity (for FGP_TV currently)
              ):
        
        L_const_inv = 1.0/lipschitz_const # inverted Lipschitz constant
        if (self.geom == '2D'):
            # 2D reconstruction
            # initialise the solution
            if (np.size(InitialObject) == self.ObjSize**2):
                # the object has been initialised with an array
                X = InitialObject
                del InitialObject
            else:
                X = np.zeros((self.ObjSize,self.ObjSize), 'float32')
        if (self.geom == '3D'):
            # initialise the solution
            if (np.size(InitialObject) == self.ObjSize**3):
                # the object has been initialised with an array
                X = InitialObject
                del InitialObject
            else:
                X = np.zeros((self.ObjSize,self.ObjSize,self.ObjSize), 'float32')
        if (self.OS_number > 1):
            regularisation_iterations = (int)(regularisation_iterations/self.OS_number)

        # The dependency on the CCPi-RGL toolkit for regularisation
        if regularisation is not None:
            if ((regularisation != 'ROF_TV') and (regularisation != 'FGP_TV') and (regularisation != 'SB_TV') and (regularisation != 'LLT_ROF') and (regularisation != 'TGV') and (regularisation != 'NDF') and (regularisation != 'DIFF4th') and (regularisation != 'NLTV')):
                raise('Unknown regularisation method, select: ROF_TV, FGP_TV, SB_TV, LLT_ROF, TGV, NDF, DIFF4th, NLTV')
            else:
                from ccpi.filters.regularisers import ROF_TV, FGP_TV, SB_TV, LLT_ROF, TGV, NDF, DIFF4th, NLTV

#****************************************************************************#
        # FISTA algorithm begins here:
        t = 1.0
        denomN = 1.0/np.size(X)
        X_t = np.copy(X)
        # Outer FISTA iterations
        for iter in range(0,iterationsFISTA):
            for sub_ind in range(self.OS_number):
                # loop over subsets
                X_old = X
                t_old = t
                if (self.OS_number > 1):
                    #select a specific set of indeces for the subset (OS)
                    indVec = self.Atools.newInd_Vec[sub_ind,:]
                    if (indVec[self.Atools.NumbProjBins-1] == 0):
                        indVec = indVec[:-1] #shrink vector size
                
                if (self.datafidelity == 'LS'):
                    # Least-squares data fidelity (linear)
                    if (self.OS_number > 1):
                        # OS-reduced gradient for LS fidelity
                        if (self.geom == '2D'):
                            grad_fidelity = self.Atools.backprojOS(self.Atools.forwprojOS(X_t,sub_ind) - projdata[indVec,:], sub_ind)
                        else:
                            grad_fidelity = self.Atools.backprojOS(self.Atools.forwprojOS(X_t,sub_ind) - projdata[:,indVec,:], sub_ind)
                    else:
                        # full gradient for LS fidelity
                        grad_fidelity = self.Atools.backproj(self.Atools.forwproj(X_t) - projdata)
                elif (self.datafidelity == 'PWLS'):
                    # Penalised Weighted Least-squares data fidelity (approximately linear)
                    if (self.OS_number > 1):
                        # OS-reduced gradient for PWLS fidelity
                        if (self.geom == '2D'):
                            grad_fidelity = self.Atools.backprojOS(np.multiply(weights[indVec,:], (self.Atools.forwprojOS(X_t,sub_ind) - projdata[indVec,:])), sub_ind)
                        else:
                            grad_fidelity = self.Atools.backprojOS(np.multiply(weights[:,indVec,:], (self.Atools.forwprojOS(X_t,sub_ind) - projdata[:,indVec,:])), sub_ind)
                    else:
                        # full gradient for PWLS fidelity
                        grad_fidelity = self.Atools.backproj(np.multiply(weights, (self.Atools.forwproj(X_t) - projdata)))
                else:
                    raise ("Choose the data fidelity term: LS, PWLS")
                X = X_t - L_const_inv*grad_fidelity
                # stopping criteria
                nrm = LA.norm(X - X_old)*denomN
                if nrm > self.tolerance:
                    # The proximal operator of the chosen regulariser
                    if (regularisation == 'ROF_TV'):
                        # Rudin - Osher - Fatemi Total variation method
                        X = ROF_TV(X, regularisation_parameter, regularisation_iterations, time_marching_parameter, self.device)
                    if (regularisation == 'FGP_TV'):
                        # Fast-Gradient-Projection Total variation method
                        X = FGP_TV(X, regularisation_parameter, regularisation_iterations, tolerance_regul, methodTV, nonneg, 0, self.device)
                    if (regularisation == 'SB_TV'):
                        # Split Bregman Total variation method
                        X = SB_TV(X, regularisation_parameter, regularisation_iterations, tolerance_regul, methodTV, 0, self.device)
                    if (regularisation == 'LLT_ROF'):
                        # Lysaker-Lundervold-Tai + ROF Total variation method 
                        X = LLT_ROF(X, regularisation_parameter, regularisation_parameter2, regularisation_iterations, time_marching_parameter, self.device)
                    if (regularisation == 'TGV'):
                        # Total Generalised Variation method (2D only currently)
                        X = TGV(X, regularisation_parameter, TGV_alpha1, TGV_alpha2, regularisation_iterations, TGV_LipschitzConstant, 'cpu') # till gpu version is fixed
                    if (regularisation == 'NDF'):
                        # Nonlinear isotropic diffusion method
                        X = NDF(X, regularisation_parameter, edge_param, regularisation_iterations, time_marching_parameter, NDF_penalty, self.device)
                    if (regularisation == 'DIFF4th'):
                        # Anisotropic diffusion of higher order
                        X = DIFF4th(X, regularisation_parameter, edge_param, regularisation_iterations, time_marching_parameter, self.device)
                    if (regularisation == 'NLTV'):
                        # Non-local Total Variation
                        X = NLTV(X, NLTV_H_i, NLTV_H_j, NLTV_H_i, NLTV_Weights, regularisation_parameter, regularisation_iterations)
                    t = (1.0 + np.sqrt(1.0 + 4.0*t**2))*0.5; # updating t variable
                    X_t = X + ((t_old - 1.0)/t)*(X - X_old) # updating X
                else:
                    #print('FISTA stopped at iteration', iter)
                    break
#****************************************************************************#
        return X
