#                                                            #
# This file is distributed as part of the WannierBerri code  #
# under the terms of the GNU General Public License. See the #
# file `LICENSE' in the root directory of the WannierBerri   #
# distribution, or http://www.gnu.org/copyleft/gpl.txt       #
#                                                            #
# The WannierBerri code is hosted on GitHub:                 #
# https://github.com/stepan-tsirkin/wannier-berri            #
#                     written by                             #
#           Stepan Tsirkin, University of Zurich             #
#                                                            #
#------------------------------------------------------------

#import billiard as multiprocessing 
import  multiprocessing 
import functools
import numpy as np
from collections.abc import Iterable
import lazy_property
from copy import copy
from time import time
import pickle
import glob

from .__Data_K import Data_K
from . import symmetry as SYM
from  .__Kpoint import exclude_equiv_points
from . import __utility as utility

def print_progress(count, total, t0):
    t = time() - t0
    t_remain = t / count * (total - count)
    print("{:20d}{:17.1f}{:22.1f}".format(count, t, t_remain), flush=True)

def process(paralfunc,K_list,nproc,symgroup=None,chunksize=0):
    t0=time()
    selK=[ik for ik,k in enumerate(K_list) if k.res is None]
    numK = len(selK)
    nstep_print = max(1, nproc, numK // 100)
    dK_list=[K_list[ik] for ik in selK]
    if len(dK_list)==0:
        print ("nothing to process now")
        return 0

    # Set chunksize for multiprocessing
    if nproc > 0:
        if chunksize <= 0:
            chunksize = max(1, min(int(numK / nproc / 200), 10))
        print("chunksize = {} used for parallelization.".format(chunksize), end=" ")
        if chunksize > 1:
            print("Smaller values recommended for large systems.", end=" ")
        else:
            print("Larger values may be used for small systems.", end=" ")
        print("Read the docs for more info.")

    print ("processing {0} K points :".format(len(dK_list)), end=" ")
    if nproc > 0:
        print("using a pool of {} processes.".format(nproc))
    else:
        print("in serial.")
    print("# K-points calculated  Wall time (sec)  Est. remaining (sec)", flush=True)
    res = []
    if nproc <= 0:
        for count, Kp in enumerate(dK_list):
            res.append(paralfunc(Kp))
            if (count + 1) % nstep_print == 0:
                print_progress(count + 1, numK, t0)
    else:
        p = multiprocessing.Pool(nproc)
        # Method 1: map. Cannot print progress.
        # res = p.map(paralfunc,dK_list)
        # Method 2: imap
        for count, res_K in enumerate(p.imap(paralfunc, dK_list, chunksize=chunksize)):
            res.append(res_K)
            if (count + 1) % nstep_print == 0:
                print_progress(count + 1, numK, t0)
        p.close()

    if not (symgroup is None):
        res=[symgroup.symmetrize(r) for r in res]
    for i,ik in enumerate(selK):
        K_list[ik].set_res(res[i])

    t=time()-t0
    if nproc <= 0:
        print("time for processing {0:6d} K-points in serial: ".format(numK), end="")
        nproc_ = 1
    else:
        print("time for processing {0:6d} K-points on {1:3d} processes: ".format(numK, nproc), end="")
        nproc_ = nproc
    print("{0:10.4f} ; per K-point {1:15.4f} ; proc-sec per K-point {2:15.4f}".format(t, t/numK, t*nproc_/numK), flush=True)
    return len(dK_list)



def evaluate_K(func,system,grid,nparK,nparFFT=0,fftlib='fftw',
            adpt_mesh=2,adpt_num_iter=0,adpt_nk=1,fout_name="result",
             suffix="",
             file_Klist="K_list.pickle",restart=False,start_iter=0,nosym=False,
             chunksize=0):
    """This function evaluates in parallel or serial an integral over the Brillouin zone 
of a function func, which whould receive only one argument of type Data_K, and return 
a numpy.array of whatever dimensions

the user has to provide 2 grids:  of K-points - NKdiv and FFT grid (k-points) NKFFT

The parallelisation is done by K-points

As a result, the integration will be performed over NKFFT x NKdiv
"""
    
    if file_Klist is not None:
        if not file_Klist.endswith(".pickle"):
            file_Klist+=".pickle"
    cnt_exclude=0

    try:
        print ("using NKdiv={}, NKFFT={}, NKtot={}".format( grid.div,grid.FFT,grid.dense))
    except: 
        pass

    
    paralfunc=functools.partial(
        _eval_func_k, func=func,system=system,grid=grid,nparFFT=nparFFT,fftlib=fftlib )



    if restart:
        try:
            K_list=pickle.load(open(file_Klist,"rb"))
            print ("{0} K-points were read from {1}".format(len(K_list),file_Klist))
            if len(K_list)==0:
                print ("WARNING : {0} contains zero points starting from scrath".format(file_Klist))
                restart=False
        except Exception as err:
            restart=False
            print ("WARNING: {}".format( err) )
            print ("WARNING : reading from {0} failed, starting from scrath".format(file_Klist))
    else:
        K_list=grid.get_K_list()
        print ("Done, sum of weights:{}".format(sum(Kp.factor for Kp in K_list)))
        start_iter=0

    suffix="-"+suffix if len(suffix)>0 else ""

    if restart:
        print ("searching for start_iter")
        try:
            start_iter=int(sorted(glob.glob(fout_name+"*"+suffix+"_iter-*.dat"))[-1].split("-")[-1].split(".")[0])
        except Exception as err:
            print ("WARNING : {0} : failed to read start_iter. Setting to zero".format(err))
            start_iter=0

    if adpt_num_iter<0:
        adpt_num_iter=-adpt_num_iter*np.prod(NKdiv)/np.prod(adpt_mesh)/adpt_nk/3
    adpt_num_iter=int(round(adpt_num_iter))


    if (adpt_mesh is None) or np.max(adpt_mesh)<=1:
        adpt_num_iter=0
    else:
        if not isinstance(adpt_mesh, Iterable):
            adpt_mesh=[adpt_mesh]*3
        adpt_mesh=np.array(adpt_mesh)
    
    counter=0


    for i_iter in range(adpt_num_iter+1):
        print ("iteration {0} - {1} points. New points are:".format(i_iter,len([K for K in  K_list if K.res is None])) ) 
        for i,K in enumerate(K_list):
          if not K.evaluated:
            print (" K-point {0} : {1} ".format(i,K))
        counter+=process(paralfunc,K_list,nparK,symgroup=None if nosym else system.symgroup, chunksize=chunksize)
        
        try:
            if file_Klist is not None:
                pickle.dump(K_list,open(file_Klist,"wb"))
        except Exception as err:
            print ("Warning: {0} \n the K_list was not pickled".format(err))
            
        result_all=sum(kp.get_res for kp in K_list)
        
        if not (restart and i_iter==0):
            result_all.write(fout_name+"-{}"+suffix+"_iter-{0:04d}.dat".format(i_iter+start_iter))
        
        if i_iter >= adpt_num_iter:
            break
             
        # Now add some more points
        Kmax=np.array([K.max for K in K_list]).T
        select_points=set().union( *( np.argsort( Km )[-adpt_nk:] for Km in Kmax )  )
        
        l1=len(K_list)
        for iK in select_points:
            K_list+=K_list[iK].divide(adpt_mesh,system.periodic)
        print ("checking for equivalent points in all points (of new  {} points)".format(len(K_list)-l1))
        nexcl=exclude_equiv_points(K_list,new_points=len(K_list)-l1)
        print (" excluded {0} points".format(nexcl))
        print ("sum of weights now :{}".format(sum(Kp.factor for Kp in K_list)))
        
    
    print ("Totally processed {0} K-points ".format(counter))
    return result_all
       


def _eval_func_k(Kpoint,func,system,grid,nparFFT,fftlib):
    data=Data_K(system,Kpoint.Kp_fullBZ,grid=grid,Kpoint=Kpoint,npar=nparFFT,fftlib=fftlib)
    return func(data)

