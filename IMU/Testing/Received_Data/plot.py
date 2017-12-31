# ---------------------------------------------------------------------
# Last Modified:
#   30-12-2017
# Description:
#   This program reads data from a csv file and graphs it in 1 second
#   intervals.
# ---------------------------------------------------------------------

# ---------------------- Import required libraries --------------------
import matplotlib.pyplot as plt
import numpy

# ---------------------- Start Program --------------------------------

plt.close('all')
win = 200  # window length

#name = raw_input("Enter the filename you wish to graph (with file extension): ")
#filename = "/home/pi/Documents/Received_Data/"+name
filename = "/home/pi/Documents/Received_Data/pz2_11-47-20.csv"
graph_data = open(filename, 'r').read()
lines = graph_data.split("\n")

# Setup Plots
fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True, sharey=True)
mng = plt.get_current_fig_manager()
mng.resize(*mng.window.maxsize())
# mng.full_screen_toggle()
#fig.subplots_adjust(hspace=0.15)
#plt.setp([a.get_xticklabels() for a in fig.axes[:-1]], visible=False)

# Init data vectors
Sensitivity= 0.244/1000
ts = []
xs = []
ys = []
zs = []

# Extract Data
for line in lines:
    if len(line) > 0:
        parts = line.split(",")
        if len(parts) == 4:
            # Rescale Data into g's
            parts[1]=int(parts[1])*Sensitivity
            parts[2]=int(parts[2])*Sensitivity
            parts[3]=int(parts[3])*Sensitivity
            
            ts.append(parts[0])
            xs.append(parts[1])
            ys.append(parts[2])
            zs.append(parts[3])

ax1.plot(ts, xs, color='r', label = 'x')
ax1.legend()
ax2.plot(ts, ys, color='b', label = 'y')
ax2.legend()
ax3.plot(ts, zs, color='k', label = 'z')
ax3.legend()

ax1.set_title('Bump Test Plot')
ax3.set_xlabel('Time (secs)')
ax2.set_ylabel('Acceleration (Gs)')
plt.show()
