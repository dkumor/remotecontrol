#print "cdbcontrol: Importing..."
from connectordb.logger import Logger
from RemoteControl import RemoteControl
import time,argparse

def initlogger(l):
    # This function is called when first creating the Logger, to initialize the values

    # api key is needed to get access to ConnectorDB
    l.apikey = input("apikey:")
    l.serverurl = "https://connectordb.com"

    # If given a schema (as we have done here), addStream will create the stream if it doesn't exist
    l.addStream("temperature",{"type":"number"})
    l.addStream("light",{"type":"number"})
    l.addStream("humidity",{"type":"number"})
    l.addStream("pressure",{"type":"number"})
    l.addStream("gas",{"type":"number"})
    l.addStream("lux",{"type":"number"})
    l.addStream("temp",{"type":"number"})

    # Sync with ConnectorDB every 5 minutes
    l.syncperiod = 60*5

parser = argparse.ArgumentParser()
parser.add_argument("--wait",help="wait this number of seconds before starting",type=int,default=0)
parser.add_argument("--notify",help="toggle one of the switches on startup to notify of start",action="store_true")
args = parser.parse_args()

if args.wait>0:
    print("cdbcontrol: waiting",args.wait,"seconds")
    time.sleep(args.wait)

print("cdbcontrol: Starting")

r = RemoteControl(sdevice="/dev/ttyS0")

def toggle(stream,datapoint):
	d = datapoint[-1]["d"]
	print(stream,datapoint)
	if stream.endswith("/rc3/downlink"):
		r.toggle(3,d)
	elif stream.endswith("/rc2/downlink"):
		r.toggle(2,d)
	return [{"t": time.time(),"d": d}]

l = Logger("/home/pi/Desktop/arduino/remotecontrol/database.db",on_create=initlogger)
cdb = l.connectordb

def create(l,description="Remote controlled electric socket",downlink=True,schema={"type":"boolean"}):
	if not l.exists():
		l.create(schema,downlink=downlink,description=description)
		#l.downlink=True
create(cdb["rc3"])
create(cdb["rc2"])

# Start the logger in the background
l.start()

if args.notify:
    print("cdbcontrol: Notifying")
    # Now we notify that we're good
    oldvalue = True
    if len(cdb["rc2"]) > 0:
    	oldvalue = cdb["rc2"][-1]["d"]

    r.toggle(2,not oldvalue)
    time.sleep(1)
    r.toggle(2,oldvalue)

# Subscribe to the downlinks
cdb["rc3"].subscribe(toggle,downlink=True,transform="if last")
cdb["rc2"].subscribe(toggle,downlink=True,transform="if last")
#cdb["light3"].subscribe(toggle,downlink=True)



print("cdbcontrol: Running")

def w(reading,x,y=None):
    if y is None:
        y = x
    if y in reading:
        l.insert(x,reading[y])


while True:
        reading = r.readSensors()
        print("Sensor Readings:",reading)
        w(reading,"temperature","temp2")
        w(reading,"light")
        w(reading,"lux")
        w(reading,"temp")
        w(reading,"pressure")
        w(reading,"gas")
        w(reading,"humidity")
        #cdb["temperature"].insert(reading["temp"])
        #cdb["light"].insert(reading["light"])
        time.sleep(60)
