import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime


# algorithm copied from https://machinelearningspace.com/object-tracking-python/
class KalmanFilter(object):
    def __init__(self, dt, u_x, u_y, std_acc, x_std_meas, y_std_meas):
        """
        :param dt: sampling time (time for 1 cycle)
        :param u_x: acceleration in x-direction
        :param u_y: acceleration in y-direction
        :param std_acc: process noise magnitude
        :param x_std_meas: standard deviation of the measurement in x-direction
        :param y_std_meas: standard deviation of the measurement in y-direction
        """
        # Define sampling time
        self.dt = dt
        # Define the  control input variables
        self.u = np.mat([[u_x], [u_y]])
        # Intial State
        self.x = np.mat([[0.], [0.], [0.], [0.]])
        # Define the State Transition Matrix A
        self.A = np.mat([[1., 0., self.dt, 0.],
                         [0., 1., 0., self.dt],
                         [0., 0., 1., 0.],
                         [0., 0., 0., 1.]])
        # Define the Control Input Matrix B
        self.B = np.mat([[(self.dt ** 2) / 2, 0.],
                         [0., (self.dt ** 2) / 2.],
                         [self.dt, 0.],
                         [0., self.dt]])
        # Define Measurement Mapping Matrix
        self.H = np.mat([[1., 0., 0., 0.],
                         [0., 1., 0., 0.]])
        # Initial Process Noise Covariance
        self.Q = np.mat([[(self.dt ** 4) / 4, 0., (self.dt ** 3) / 2, 0.],
                         [0, (self.dt ** 4) / 4, 0., (self.dt ** 3) / 2.],
                         [(self.dt ** 3) / 2, 0., self.dt ** 2, 0.],
                         [0, (self.dt ** 3) / 2, 0., self.dt ** 2]]) * std_acc ** 2
        # Initial Measurement Noise Covariance
        self.R = np.mat([[x_std_meas ** 2, 0],
                         [0, y_std_meas ** 2]])
        # Initial Covariance Matrix
        self.P = np.eye(self.A.shape[1])

    def predict(self):
        # Refer to :Eq.(9) and Eq.(10)  in https://machinelearningspace.com/object-tracking-simple-implementation-of-kalman-filter-in-python/?preview_id=1364&preview_nonce=52f6f1262e&preview=true&_thumbnail_id=1795
        # Update time state
        # x_k =Ax_(k-1) + Bu_(k-1)     Eq.(9)
        self.x = np.dot(self.A, self.x) + np.dot(self.B, self.u)
        # Calculate error covariance
        # P= A*P*A' + Q               Eq.(10)
        self.P = np.dot(np.dot(self.A, self.P), self.A.T) + self.Q
        return self.x[0:2]

    def update(self, z):
        # Refer to :Eq.(11), Eq.(12) and Eq.(13)  in https://machinelearningspace.com/object-tracking-simple-implementation-of-kalman-filter-in-python/?preview_id=1364&preview_nonce=52f6f1262e&preview=true&_thumbnail_id=1795
        # S = H*P*H'+R
        S = np.dot(self.H, np.dot(self.P, self.H.T)) + self.R
        # Calculate the Kalman Gain
        # K = P * H'* inv(H*P*H'+R)
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))  # Eq.(11)
        self.x = (self.x + np.dot(K, (z - np.dot(self.H, self.x))))  # Eq.(12)
        I = np.eye(self.H.shape[1])
        # Update error covariance matrix
        self.P = (I - (K * self.H)) * self.P  # Eq.(13)
        return self.x[0:2]


# converts .csv data into numpy arrays
def getPlotData(d, xpoint=0, ypoint=1):
    xs = []
    ys = []

    for ds in np.array(d):
        xs.append(ds[xpoint])
        ys.append(ds[ypoint])
        # print(ds)

    return xs, ys


dataX = []
dataY = []


def getPreData():
    fil = open("tracker.csv", "r")
    data = []
    for line in fil.readlines():
        split_ = line.split(",")[3:5]
        # split_.append(0)
        split_[0] = float(split_[0])
        split_[1] = float(split_[1])
        dataX.append(split_[0])
        dataY.append(split_[1])
        data.append(split_)
    fil.close()
    return data


diff = []


def getCSVData():
    global diff
    fil = open("roverdata.csv", "r")
    dform = "%m/%d/%Y %H:%M:%S"
    rawdata = []
    meddata = []
    baccdata = []
    accdata = []
    diff = []
    last = (0,0,0)
    for line in fil.readlines():
        split_ = line.split(",")
        dt = datetime.strptime(split_[1], dform).timestamp()
        type = split_[2]
        if type == "raw":
            accdata.append((dt, float(split_[6])))
            rawdata.append((dt, float(split_[3]), float(split_[4]), float(split_[5]), float(split_[6])))
        elif type == "med":
            meddata.append((dt, float(split_[3]), float(split_[4]), float(split_[5]), float(split_[6])))
            x,y,z = float(split_[3]), float(split_[4]), float(split_[5])
            if last != (0, 0, 0):
                lx, ly, lz = last
                d = ( (x-lx)**2 + (y-ly)**2 + (z-lz)**2) **.5
                diff.append((dt, d))
            print(last, (x, y, z))
            last = x, y, z

        elif type == "ba":
            baccdata.append((dt, float(split_[3]), float(split_[4]), float(split_[5]), float(split_[6])))
    fil.close()
    return rawdata, meddata, baccdata, accdata


slow = lambda l: list(filter(lambda t: t[0] < 1630762508.0, l))
fast = lambda l: list(filter(lambda t: t[0] >= 1630762508.0, l))
t = 0
xp = 1
yp = 2
zp = 3
a = 4
a1 = t
a2 = yp
f = fast

s = 20
N = s

# Time interval in seconds
dk = 1

# data = getPreData()
data = f(getCSVData()[1])

givenX = data[0][a1]  # * 0
givenY = data[0][a2]  # * 0
print(givenX, givenY)
accel = 0

deltat = 1
noiseX = 0
noiseY = 0
xmerror = 50 ** (-6)
ymerror = 50 ** (-6)

A = np.mat([[1., 0., deltat, 0.],
            [0., 1., 0., deltat],
            [0., 0., 1., 0],
            [0., 0., 0., 1.]])

B = np.mat([[.5 * deltat ** 2, 0.],
            [0, .5 * deltat ** 2],
            [deltat, 0.],
            [0., deltat]])
C = np.identity(2)

H = np.mat([[1., 0., 0., 0.],
            [0., 1., 0., 0.]])

Q = np.mat([[deltat ** 4 / 4, 0., deltat ** 3 / 2, 0.],
            [0., deltat ** 4 / 4, 0., deltat ** 3 / 2],
            [deltat ** 3 / 2, 0., deltat ** 2, 0.],
            [0, deltat ** 3 / 2, 0, deltat ** 2]])  # * smth?

R = np.mat([[xmerror ** 2, 0.],
            [0., ymerror ** 2]])

P = np.eye(A.shape[1])

Xkm1 = np.mat([[givenX],
               [givenY],
               [0.],
               [0.]])

uk = np.mat(accel)
wk = 0

Pk = np.mat([[noiseX ** 2, 0.],
             [0., noiseY ** 2]])

# take first N elements - useful for debugging small amounts of data
# data = data[:N]
newData = []
predictData = []

# KalmanFilter(dt, u_x, u_y, std_acc, x_std_meas, y_std_meas)
Kf = KalmanFilter(1, 0, 0, .0000001, .0001, .0001)

for i in range(1, len(data)):
    xm, ym = data[i][a1], data[i][a2]
    (x, y) = Kf.predict()
    predictData.append([x, y])

    # could easily add file write here
    (x1, y1) = Kf.update(np.array([[xm], [ym]]))
    newData.append([x1, y1])
    print([xm, ym], [x, y], [x1, y1])
    print([xm - x, ym - y], [xm - x1, ym - y1])
    print("---")

# date conversions
# "%m/%d/%Y %H:%M:%S.%f"
# d.timestamp()

# plot data on same graph
# xs, ys = getPlotData(data, 1, 1)
# plt.scatter(xs, ys)

# xs, ys = getPlotData(newData)
# plt.scatter(xs, ys)
#
# plt.show()
rd, md, bad, ad = getCSVData()


# print(min(map(lambda t:t[1], slow(ad))))
# print(min(map(lambda t:t[0], slow(ad))))
# print(max(map(lambda t:t[0], slow(ad))))
# print(sum(map(lambda t: t[1], ad)) / len(ad))
# xs,ys = getPlotData(rd,0,3)
# plt.scatter(xs,ys)
# xs,ys = getPlotData(md,0,2)
# plt.scatter(xs,ys)
# xs,ys = getPlotData(bad,0,2)
# plt.scatter(xs,ys)

def plotData(data):
    xs, ys = data
    plt.scatter(xs, ys)


# xs, ys = getPlotData(f(rd), a1, a2)
# plt.scatter(xs, ys)
# plt.xlabel("ECEF Y coordinate (cm)")
diff = f(list(filter(lambda i: i[1] < 250, diff)))
pm = (max(map(lambda i: abs(i[1]-s), diff)))
print(pm, pm + s, pm - s)
xs, ys = getPlotData(diff)
plt.scatter(xs, ys)
plt.xlabel("Time (epoch time)")
plt.ylabel("Displacement from last median reading (cm)")
plt.axhline(s, dashes=(1, 5))
plt.axhline(s + pm, dashes=(1, 1), color='tab:red')
# plt.axhline(20 - pm, dashes=(1, 1), color='tab:red')
# plt.ylabel("Estimated Accuracy (cm)")
# xs, ys = getPlotData(f(md), a1, a2)
# plt.scatter(xs, ys)
# xs, ys = getPlotData(f(bad), a1, a2)
# plt.scatter(xs, ys)
# xs, ys = getPlotData(newData)
# plt.scatter(xs, ys)
# xs, ys = getPlotData(fast(ad))
# plt.scatter(xs, ys)
plt.show()
