# example from https://filterpy.readthedocs.io/en/latest/kalman/KalmanFilter.html

from filterpy.kalman import FixedLagSmoother
import numpy as np

data=[]
fil=open("tracker.csv", "r")

for line in fil.readlines():
    data.append(line.split(",")[3:5])

fls = FixedLagSmoother(dim_x=2, dim_z=1)

fls.x = np.array([[0.],
                  [.5]])

fls.F = np.array([[1.,1.],
                  [0.,1.]])

fls.H = np.array([[1.,0.]])

fls.P *= 200
fls.R *= 5.
fls.Q *= 0.001

zs = data
xhatsmooth, xhat = fls.smooth_batch(zs, N=4)

print(xhatsmooth, xhat)