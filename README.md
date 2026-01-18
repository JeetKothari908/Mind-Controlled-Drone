# Mind-Controlled-Drone
This project uses a Muse 2 along with Muselsl to live stream EEG data. We combined this with a ML model to get basic classifiers. The only drone we had was a DJI Air 2, so we built an Android app with DJI's Air 2 SDK and combined everything with websockets. 

For ML, we plan on using a three way classifier for each dimension of movement with imagining left hand movement, imagining right hand movement, and a third imagined movement/focused state. We also plan on using a two way classifier for + or - movement in the selected dimension with imagined left/right hand movement. 

Note: This program uses BlueMuse and muselsl, so you also need pylsl and liblsl to stream data. 

To Do:
Debug + Test EEG Pipeline
Develop ML model
Make Andriod App
Connect Everything w/ websockets

Progress:
Verified BCI works with Python and live streaming data works
