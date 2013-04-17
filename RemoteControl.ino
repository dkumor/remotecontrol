/*
This code implements a fairly general purpose communication method. The idea here is that IR LEDs and
cheap 433 MHz RF transmitters can be used to control things like TVs or wireless outlets. This code
attempts to make an arduino connected through serial to a computer (ideally a raspberry pi) be able
to output an arbitrary binary sequence through connected modules.

The code will boot, display a "SerialRemote v0.20" at 57600 baud and on the next line, display an "ok".
After each command you send is executed, you must wait for an "ok\r\n" to be able to execute further commands.
If an error is encountered at any point, an "err\r\n" will be sent. If the error is fatal, and the arduino is
about to be put into an infinite loop for safety, and "ferr\r\n" will be sent.

The program contains a buffer of fixed size (about 700) which holds the sequence that will be "sent".
The sequence is starting from zero, the delays in microseconds before flipping to a 1, and so forth.
The 0th device is a null device, meaning is in a command you choose it,
then the buffer will be filled and so on, but nothing will be sent.
That being said, each command must be followed by a newline before any further arguments are interpreted.

The following are the commands available:

t:
  Allows to fill the buffer (ie, write a sequence of 1s and 0s and send them) from the computer
  using serial in text format. A sample command is as follows:
  "t\n1\n500\n1000\n40\n100\n0\n"
  The t\n is the command to write the text sequence to buffer, the 1\n is the device number to send command to,
  and the seqence is 0 for 500 microseconds,
  1 for 1000 microseconds, 0 for 40 microseconds, 1 for 100 microseconds. Then the 0\n notifies that the sequence
  is finished.
b:
  Allows to fill the buffer just like in command "t", but using straight binary 16-bit unsigned integers instead of text.
  Thus, the command would start "b\n1\n", where 1 is the device number, and then start sending 
  <highbyte1><lowbyte1><highbyte2><lowbyte2> and so on,
  until the last is a 16 bit 0, meaning <0><0>, notifying end of sequence. There is no \n following, the next command follows
  immediately after <0><0>. (After an ok is recieved, of course)
w:
  Sends the command in buffer to the given device. This writes the contents of the buffer to the given device.
  A sample command would be: "w\n3" This writes the command in buffer to device number 3. Devices start with 1. The 0th device
  is "do not send"
x:
  Sends a built-in command. The built in commands have to be manually coded for each command you want to support. The built in commands
  are basically on-board sequences to fill the buffer with.
  A sample command is "x\n3\n8\n". This sends command 8 to device 3.
  The reason that builtin commands are preferable to sending buffers manually is that they are *much* faster: there is usually about a second
  of delay in sending a buffer, while the delay is negligible when using builtin.


Please note that there is a reference implementation of interfacing with this program in python called RemoteControl.py, which should be in the
same directory

The following code is released to the public domain in 2013 by Daniel Kumor
*/

//memcpy
#include <string.h>

#define RFVERSION 0.2f
#define RF433_POWERPIN 2
#define RF433_DATAPIN 4
#define LEDPIN 13
#define BUFFERSIZE 700

unsigned int *dataBuffer;

void setup() {
    
    //Write notification LED
    pinMode(LEDPIN,OUTPUT);
      digitalWrite(LEDPIN,0);
    //RF433
    pinMode(RF433_POWERPIN,OUTPUT);
    pinMode(RF433_DATAPIN,OUTPUT);
      digitalWrite(RF433_POWERPIN,0);
      digitalWrite(RF433_DATAPIN,0);
    
    
    //Get to communicatin'
    Serial.begin(57600);
    Serial.print("SerialRemote v");
    Serial.println(RFVERSION);
    
    //The databuffer allows the user to send a custom binary sequence
    //  during runtime.
    dataBuffer = (unsigned int*)malloc(BUFFERSIZE*sizeof(unsigned int));
    if (!dataBuffer) {
        //If allocation fails, require restart (ferr=fatal error)
        Serial.println("ferr");
        while (true);
    }
}

//This function does the bit-flipping necessary to send the signal we want
void writeBuffer(int pin) {
    bool pinval = false;  //Writes start with 0
    
    //Turn on "sending" notification LED
    digitalWrite(LEDPIN,1);
    
    //Transmit
    for (int i=0; i<BUFFERSIZE && dataBuffer[i]!=0;i++) {
        digitalWrite(pin,pinval);
        pinval = !pinval;
        delayMicroseconds(dataBuffer[i]);
    }
    
    //Do final bit-flip
    digitalWrite(pin,pinval);
    
    //Finished sending
    digitalWrite(LEDPIN,0);
}

//This sends the actual signal using the device given
bool writeBufferToDevice(unsigned int device) {
    switch (device) {
          case 0:  //The 0 device does not send anything
              break;    
          case 1:  //The 1 device is a 433MHz transmitter   
              //Turn on the transmitter, and wait a bit to make sure it is working
              digitalWrite(RF433_POWERPIN,1);
              delayMicroseconds(100);
              //Write the buffer
              writeBuffer(RF433_DATAPIN);
              //Turn off the transmitter
              digitalWrite(RF433_DATAPIN,0);
              digitalWrite(RF433_POWERPIN,0);
              break;
          default:
              return false;  //The device doesn't exist!
              break;
    }
    return true;
}

//This is a helper function: It reads an integer (unsigned int) which is in the form "3432\n"
unsigned int readIntLine() {
    unsigned int value = 0;
    char b = 0;
    while (b!='\n') {
        while (!Serial.available());
        b = Serial.read();
        if (b>=48 && b<=57) {
            value*=10;
            value += (unsigned int)b - 48;
        }
    }
    return value;
}

//Reads the given text into buffer
bool text_bufferRead() {
    unsigned int rd = 1;
    for (int i=0; i < BUFFERSIZE && rd != 0;i++) {
        rd = readIntLine();
        dataBuffer[i] = rd;
    }
    if (rd!=0) return false;
    return true;
}

//Reads a binary array into buffer
bool binary_bufferRead() {
    unsigned int rd = 1;
    for (int i=0; i < BUFFERSIZE && rd != 0;i++) {
        while (!Serial.available());
        rd = (unsigned int)Serial.read() << 8;
        while (!Serial.available());
        rd += (unsigned int)Serial.read();
        dataBuffer[i] = rd;
    }
    if (rd!=0) return false;
    return true;
}

//Given a command number, writes the given sequence straight to buffer
bool command(unsigned int num) {
    switch (num) {
        //The first 6 commands are the on/off commands to my personal RF wall outlets
        case 0:
        case 1:
        case 2:
        case 3:
        case 4:
        case 5:
            //The sequence is repeated 5 times
            dataBuffer[0]=12000;  //0
            //First 2 bytes: On/off
            if (num%2) { //Turn ON
                dataBuffer[1]=1270;
                dataBuffer[2]=410;
                dataBuffer[3]=410;
                dataBuffer[4]=1270;
            } else { //Turn OFF
                dataBuffer[1]=410;
                dataBuffer[2]=1270;
                dataBuffer[3]=1270;
                dataBuffer[4]=410;
            }
            
            dataBuffer[5]=410;
            dataBuffer[6]=1270;
            dataBuffer[7]=1270;
            dataBuffer[8]=410;
            
            for (int i=0;i<5;i++) {  //Next are 5 0s
                dataBuffer[9+2*i]=410;
                dataBuffer[10+2*i]=1270;
            }
            dataBuffer[19]=1270;  //A 1
            dataBuffer[20]=410;
            for (int i=0;i<num/2+2;i++) {
                dataBuffer[21+2*i]=410;
                dataBuffer[22+2*i]=1270;
            }
            dataBuffer[25+2*(num/2)]=1270;  //A 1 in the wall outlet ID spot
            dataBuffer[26+2*(num/2)]=410;
            for (int i=num/2;i<13;i++) {
                dataBuffer[27+2*i]=410;
                dataBuffer[28+2*i]=1270;
            }
            dataBuffer[53]=410;  //1
            
            //Now memcpy this sequence 4 times, since we repeat it
            for (int i=1;i<5;i++) {
                memcpy((void*)&(dataBuffer[54*i]),(void*)dataBuffer,108);
            }
            
            //Lastly, the end cap
            dataBuffer[270]=0;
            break;
        default:
            return false;
            
    }
    return true;
}

void loop() {
    Serial.println("ok");  //The "ok" signals that commands are accepted now
    //Don't do anything while no serial available
    while (!Serial.available());
    char cmd = Serial.read();       //Read command character
    while (Serial.read()!='\n');    //Ignore rest until next line
    unsigned int device,com;
    switch (cmd) {
        //Command 't' is for 'text'
        case 't':
            device = readIntLine();
            if (!(text_bufferRead() && writeBufferToDevice(device))) Serial.println("err");
            break;
        //'b' stands for binary
        case 'b':
            device = readIntLine();
            if (!(binary_bufferRead() && writeBufferToDevice(device))) Serial.println("err");
            break;
        //'w' is for write contents of buffer to device
        case 'w':
            device = readIntLine();
            if (!(writeBufferToDevice(device))) Serial.println("err");
            break;
        //'x' is for "eXecute built in buffer"
        case 'x':
            device = readIntLine();  //Device number
            com = readIntLine();     //Command number
            if (!(command(com) && writeBufferToDevice(device))) Serial.println("err");
            break;
        default:
            Serial.println("err");
            break;
    }
}
