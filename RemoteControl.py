import serial
import sys
import copy

class RemoteControl():
    
    def __init__(self,conversions=None,strings=None,defaultDevices=None, sdevice='/dev/ttyACM0'):
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
        header = self.ser.readline()
        isok=""
        while (isok!="ok\r\n"):
            isok= self.ser.readline()
            if (isok=="ferr\r\n"):
                self.close()
                raise "Serial device error"
                
    #Closes all necessary resources
    def close(self):
        self.ser.close()
        
    #Writes command string s and waits for ok
    def sendCommandToDevice(self,s):
        success=True
        isok=""
        self.ser.write(s)
        while (isok!="ok\r\n"):
            isok= self.ser.readline()
            if (isok=="ferr\r\n"):
                self.close()
                raise "Serial device error"
            elif (isok=="err\r\n"):
                success=False
        return success
        
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
    def sendList(self,l,device=1,commandtype="b"):
        #Communication starts from 0, so if the connection does not start from a 0, insert a short 0 pulse
        if (l[0][0]!=0):
            l=[[0,10]]+l
        
        #Send shit
        return self.sendCommandToDevice(self.listToBuffer(self.simplifyList(l),device,commandtype))
    
    def sendString(self,s,device=1,comtype="t"):
        return self.sendList(self.stringToList(s),device,comtype)
    
    #SendBuiltin allows to send a built in "signal" over the given device,
    def sendBuiltin(self,device=1,commandID=0):
        return self.sendCommandToDevice("x\n"+str(device)+"\n"+str(commandID)+"\n")
    
    def sendRedo(self,device=1):
        return self.sendCommandToDevice("w\n"+str(device)+"\n")
    
    #The following functions are for simple activation's sake
    
    def toggle(self,objectID,onoff):
        #print self.strings[str(outletnum)+str(int(turnon))]
       return self.send(str(objectID)+"_"+str(int(onoff)))
    
    def send(self,stringid):
        if isinstance(self.strings[stringid],int):  #If the stringid refers to an integer, then that is the ID of a builtin command
            return self.sendBuiltin(self.defaultDevices[stringid],self.strings[stringid])
        else:
            return self.sendString(self.strings[stringid],device=self.defaultDevices[stringid])
            
    def setConversion(self,convchar,conv):
        self.conversions[convchar]=conv
    def setString(self,stringID,string,defdevice=None):
        self.strings[stringID]=string
        if (defdevice):
            self.defaultDevices[stringID]=defdevice
    def setObjectToggle(self,objectID,onoff,defdevice,string):
        self.setString(str(objectID)+"_"+str(int(onoff)),string,defdevice)

if (__name__=="__main__"):
    o = RemoteControl()
    o.toggle(1,True)
    raw_input()
    o.toggle(4,False)
    
