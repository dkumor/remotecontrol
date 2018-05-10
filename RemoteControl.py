#The following code is released to the public domain in 2013 by Daniel Kumor
import serial
import sys
import copy

class RemoteControl():
    
    def __init__(self,conversions=None,strings=None,defaultDevices=None, sdevice='/dev/ttyS0'):
        #Conversions are the actual binary sequences of the "most basic" s and 0s.
        #   Note that converisons can only be single characters
        if not conversions:
            self.conversions = {
                "1":    [[1,1270],[0,410]],
                "0":    [[1,410],[0,1270]],
                "l":    [[1,410],[0,12000]]
            }
        else:
            self.conversions = conversions
        
        #Strings are the sequence of 1s 0s and other defined
        #   conversions that make up the signals. The naming convention
        #   is <objectID>_<on/off>
        #Note that a built-in command is an integer, so you can define a
        #   "string" that just basically has the microcontroller do a built-in command
        if not strings:
            self.strings = {
                "1_0": 0,
                "1_1": 1,
                "2_0": 2,
                "2_1": 3,
                "3_0": 4,
                "3_1": 5,
                #These strings are the same as the built in commands, they are here just
                #   to serve as reference
                "4_1": "l"+"10010000010010000000000000l"*5,
                "4_0": "l"+"01010000010010000000000000l"*5,
                "5_1": "l"+"10010000010001000000000000l"*5,
                "5_0": "l"+"01010000010001000000000000l"*5,
                "6_1": "l"+"10010000010000100000000000l"*5,
                "6_0": "l"+"01010000010000100000000000l"*5,
            }
        else:
            self.strings = strings
        
        #The strings which have devices associated with them
        if not defaultDevices:
            self.defaultDevices = {
                "1_1": 1,
                "1_0": 1,
                "2_1": 1,
                "2_0": 1,
                "3_1": 1,
                "3_0": 1,
                "4_1": 1,
                "4_0": 1,
                "5_1": 1,
                "5_0": 1,
                "6_1": 1,
                "6_0": 1,
            }
        else:
            self.defaultDevices=defaultDevices
        
        self.ser = serial.Serial(sdevice,57600,timeout=10)
        
        #Sometimes, we get some sort of weird failure on serial start, so clear buffer of micro
        #   Serial probably sometimes sends initialization characters. This is especially annoying
        #   on RasPi.
        self.sendCommandToDevice("0\n")
                
    #Closes all necessary resources
    def close(self):
        self.ser.close()
        
    #Writes command string s and waits for ok
    def sendCommandToDevice(self,s,verbose=False):
        success=True
        isok=""
        self.ser.write(s)
        while (isok!="ok\r\n"):
            isok= self.ser.readline()
            if (verbose):
                print isok,
            if (isok=="ferr\r\n"):
                self.close()
                raise "Serial device error"
            elif (isok=="err\r\n"):
                success=False
        return success
    
    def readSensors(self):
        self.ser.write("r\n")
        isok=self.ser.readline()
        output = {}
        while (isok!="ok\r\n"):
            if (isok=="ferr\r\n"):
                self.close()
                raise "Serial device error"
            # This line is a sensor reading
            sname,svalue = isok.split(":")
            sname=sname.strip()
            svalue = svalue.strip()
            try:
                svalue = int(svalue)
            except:
                try:
                    svalue = float(svalue)
                except:
                    pass
            output[sname] = svalue
            isok = self.ser.readline()
        return output
    #Given a string, applies the conversions to create the list of binary activations
    def stringToList(self,s):
        l=[]
        for i in xrange(len(s)):
            l+= copy.deepcopy(self.conversions[s[i]])
        return l

    #Given a converted list (meaning a list of 1s,0s and timings), it simplifies by combining consecutive 0s and 1s
    def simplifyList(self,l):
        if (len(l)<=1): return l
        res = [l[0]]
        for i in xrange(1,len(l)):
            if (res[-1][0]==l[i][0]):
                res[-1][1]+=l[i][1]
            else:
                res.append(l[i])
        return res
        
    #given a list, prepares the command string for the given data sending mode
    def listToBuffer(self,l,device,c):
        s=""
        if (c=='t'):    #Text mode
            s+="t\n"+str(device)+'\n'
            for i in xrange(len(l)):
                s+=str(l[i][1])+'\n'
            s+="0\n"
            return s
        elif (c=='b'):  #Binary mode
            s+="b\n"+str(device)+'\n'
            for i in xrange(len(l)):
                s+=chr((l[i][1] >> 8) & 0xff) + chr(l[i][1] & 0xff)
            s+=chr(0)+chr(0)
            return s
        return ""
    
    #Sends the sequence defined by the list to device number given
    def sendList(self,l,device=1,commandtype="b",verbose=False):
        #Communication starts from 0, so if the connection does not start from a 0, insert a short 0 pulse
        if (l[0][0]!=0):
            l=[[0,10]]+l
        
        #Send shit
        return self.sendCommandToDevice(self.listToBuffer(self.simplifyList(l),device,commandtype),verbose)
    
    def sendString(self,s,device=1,comtype="b",verbose=False):
        return self.sendList(self.stringToList(s),device,comtype,verbose)
    
    #SendBuiltin allows to send a built in "signal" over the given device,
    def sendBuiltin(self,device=1,commandID=0,verbose=False):
        return self.sendCommandToDevice("x\n"+str(device)+"\n"+str(commandID)+"\n",verbose)
    
    def sendRedo(self,device=1,verbose=False):
        return self.sendCommandToDevice("w\n"+str(device)+"\n",verbose)
    
    #The following functions are for simple activation's sake
    
    def toggle(self,objectID,onoff,verbose=False):
        #print self.strings[str(outletnum)+str(int(turnon))]
       return self.send(str(objectID)+"_"+str(int(onoff)),verbose)
    
    def send(self,stringid,verbose=False):
        if isinstance(self.strings[stringid],int):  #If the stringid refers to an integer, then that is the ID of a builtin command
            return self.sendBuiltin(self.defaultDevices[stringid],self.strings[stringid],verbose)
        else:
            return self.sendString(self.strings[stringid],device=self.defaultDevices[stringid],verbose=verbose)
            
    def setConversion(self,convchar,conv):
        self.conversions[convchar]=conv
    def setString(self,stringID,string,defdevice=None):
        self.strings[stringID]=string
        if (defdevice):
            self.defaultDevices[stringID]=defdevice
    def setObjectToggle(self,objectID,onoff,defdevice,string):
        self.setString(str(objectID)+"_"+str(int(onoff)),string,defdevice)

    def readIR(self):
        self.ser.write("i\n")
        device = int(self.ser.readline().strip())
        command = int(self.ser.readline().strip())
        bits = int(self.ser.readline().strip())
        isok = self.ser.readline()
        if isok != "ok\r\n":
            raise "IR read did not succeed"
        return (device,command,bits)
    def writeIR(self,device,command,bits):
        return self.sendCommandToDevice("l\n%d\n%d\n%d\n"%(device,command,bits))
        

if (__name__=="__main__"):
    print "Creating"
    o = RemoteControl()
    print o.writeIR(3, 2774153415L, 32)
    """
    print "Reading Sensors"
    print o.readSensors()
    print "Toggling"
    o.toggle(2,True)
    print "User Input"
    raw_input()
    print "Toggle"
    o.toggle(5,False)
    """
    print "Done"
    
