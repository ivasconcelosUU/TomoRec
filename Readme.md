#  Regularised FISTA-type iterative reconstruction algorithm for X-ray tomographic reconstruction with highly inaccurate measurements

** This software supports research published in the following journal papers [1,2] with applications in [3-5]. Software depends on several packages and requires a GPU (Nvidia) device to operate. ** 

<div align="center">
  <img src="docs/images/recsFISTA_stud.png" height="216"><br>  
</div>

## Package highlights:
 * Tomographic projection data are simulated without the "inverse crime" using [TomoPhantom](https://github.com/dkazanc/TomoPhantom). Noise and artifacts (zingers, rings) are also can be modelled.
 * Simulated data then iteratively reconstructed using FISTA-type algorithm with multiple "plug-and-play" regularisers from [CCPi-RegularisationToolkit](https://github.com/vais-ral/CCPi-Regularisation-Toolkit) 
 * FISTA algorithm offers novel modifications: convergence acceleration with ordered-subsets method, PWLS, Group-Huber and Students't data fidelities [1,2] to deal with noise and image artifacts
 * Various projection (2D/3D) geometries are supported and real data provided to demonstrate the effectivness of the method  

### General software prerequisites
 * [MATLAB](http://www.mathworks.com/products/matlab/) 
 * C compilers (GCC/MinGW) and nvcc [CUDA SDK](https://developer.nvidia.com/cuda-downloads) compilers
 
### Software dependencies: 
 * [ASTRA-toolbox](https://www.astra-toolbox.com/)  
 * [TomoPhantom](https://github.com/dkazanc/TomoPhantom)
 * [CCPi-RegularisationToolkit](https://github.com/vais-ral/CCPi-Regularisation-Toolkit) 

### Installation:
 * [TomoPhantom](https://github.com/dkazanc/TomoPhantom) and [CCPi-RegularisationToolkit](https://github.com/vais-ral/CCPi-Regularisation-Toolkit) 
 must be installed in order to use the software. See INSTALLATION for detailed information.  
 
### Package contents:
 * DemoRec_2D_Parallel.m - demo to run regularised FISTA reconstruction for noisy data 
 * DemoRec_2D_Parallel_OS.m - demo to run ordered-subsets regularised FISTA reconstruction for noisy data 
 * DemoRec_2D_Parallel_Artifacts.m - demo to run regularised FISTA reconstruction for erroneous data 
 * DemoRec_2D_Parallel_Artifacts_OS.m - demo to run ordered-subsets regularised FISTA reconstruction for erroneous data 

### References:
 1. [D. Kazantsev et al. 2017. A Novel Tomographic Reconstruction Method Based on the Robust Student's t Function For Suppressing Data Outliers. IEEE TCI, 3(4), pp.682-693.](https://doi.org/10.1109/TCI.2017.2694607)
 2. [D. Kazantsev et al. 2017. Model-based iterative reconstruction using higher-order regularization of dynamic synchrotron data. Measurement Science and Technology, 28(9), p.094004.](https://doi.org/10.1088/1361-6501/aa7fa8)

### Applications:
 3. [E. Guo et al. 2017. Dendritic evolution during coarsening of Mg-Zn alloys via 4D synchrotron tomography. Acta Materialia, 123, pp.373-382.](https://doi.org/10.1016/j.actamat.2016.10.022) 
 4. [E. Guo et al. 2018. The influence of nanoparticles on dendritic grain growth in Mg alloys. Acta Materialia.](https://doi.org/10.1016/j.actamat.2018.04.023)
 5. [E. Guo et al. 2017. Synchrotron X-ray tomographic quantification of microstructural evolution in ice cream–a multi-phase soft solid. Rsc Advances, 7(25), pp.15561-15573.](https://doi.org/10.1039/C7RA00642J)
 
### License:
GNU GENERAL PUBLIC LICENSE v.3

### Questions/Comments
can be addressed to Daniil Kazantsev at dkazanc@hotmail.com