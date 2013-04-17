import serial
import sys

conv = {
    "1": "1270\n410\n",
    "0": "410\n1270\n",
    "l": "410\n12000\n",
    "s": "410\n"
}

lights = {
    "11": "10010000010010000000000000l",
    "10": "01010000010010000000000000l",
    "21": "10010000010001000000000000l",
    "20": "01010000010001000000000000l",
    "31": "10010000010000100000000000l",
    "30": "01010000010000100000000000l",
    "test": "00000000000000000000000000000000000000000000000000000000000000000000000000l",
}

def msgstr(light):
    s=""
    for i in xrange(len(lights[light])):
        s+= conv[lights[light][i]]
    return s
def getMessageString(light):
    try:
        print "Binary String:",lights[light]
    except:
        print "NOT FOUND"
        return ""
    s="t\n"
    s+=conv["s"]
    s+=conv["l"]
    s+= msgstr(light)*5
    s+="0\n"
    return s
ser = serial.Serial('/dev/ttyACM0',9600,timeout=10)
header = ser.readline()
sys.stdout.write("Header: "+header)

if (header!="Serial RF v0.10\r\n"):
    print "Unknown header!"

isok = ""
itxt = ""
while (True):
    while(isok!="ok\r\n"):
        isok=ser.readline()
        sys.stdout.write(isok)
    isok=""
    itxt = raw_input(">")
    
    if (itxt=="exit"):
        break
    else:
        txt=getMessageString(itxt)
        if (txt!=""):
            ser.write(txt)
        

ser.close()
