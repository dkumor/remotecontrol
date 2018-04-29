#print "cdbcontrol: Importing..."
import connectordb
from RemoteControl import RemoteControl
import time,argparse

parser = argparse.ArgumentParser()
parser.add_argument("--wait",help="wait this number of seconds before starting",type=int,default=0)
parser.add_argument("--notify",help="toggle one of the switches on startup to notify of start",action="store_true")
args = parser.parse_args()

if args.wait>0:
    print "cdbcontrol: waiting",args.wait,"seconds"
    time.sleep(args.wait)

print "cdbcontrol: Starting"

r = RemoteControl(sdevice="/dev/ttyS0")

def toggle(stream,datapoint):
	d = datapoint[-1]["d"]
	print stream,datapoint
	if stream.endswith("/rc3/downlink"):
		r.toggle(3,d)
	elif stream.endswith("/rc2/downlink"):
		r.toggle(2,d)
	return [{"t": time.time(),"d": d}]

cdb = connectordb.ConnectorDB("apikey",url="https://connectordb.com")

def create(l,downlink=True,description="Remote controlled electric socket",schema={"type":"boolean"}):
	if not l.exists():
		l.create(schema,downlink=downlink,description=description)
		#l.downlink=True
create(cdb["rc3"])
create(cdb["rc2"])
create(cdb["temperature"],downlink=False,description="Temperature in my apartment",schema={"type": "number"})
create(cdb["light"],downlink=False,description="Raw ambient light sensor reading",schema={"type": "number"})

if args.notify:
    print "cdbcontrol: Notifying"
    # Now we notify that we're good
    oldvalue = True
    if len(cdb["rc2"]) > 0:
    	oldvalue = cdb["rc2"][-1]["d"]

    r.toggle(2,not oldvalue)
    time.sleep(1)
    r.toggle(2,oldvalue)

cdb["rc3"].subscribe(toggle,downlink=True,transform="if last")
cdb["rc2"].subscribe(toggle,downlink=True,transform="if last")
#cdb["light3"].subscribe(toggle,downlink=True)



print "cdbcontrol: Running"

while True:
        reading = r.readSensors()
        print "Sensor Readings:",reading
        cdb["temperature"].insert(reading["temp"])
        cdb["light"].insert(reading["light"])
        time.sleep(60)
