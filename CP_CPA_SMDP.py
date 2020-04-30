# The demo application requires the installation of pySerial to work.
# https://pypi.org/project/pyserial/

import serial
import serial.tools.list_ports
import struct
import time
from tkinter import Tk, Button, INSERT, END, Label, Text
from tkinter import scrolledtext

# ----  Global Variables ----
gWindow = Tk()
gTxtPort = Text(gWindow, height=1, width=40)
gTxtFeedback = scrolledtext.ScrolledText(gWindow)
gCompressorID = 16

def SendCommand(command):
    # Extract the Comm Port from the textbox
    # Open the port then send the command.  
    # Close the port when done
    thePort = gTxtPort.get('1.0', END)
    thePort = thePort.strip()
    activePort = serial.Serial(port = thePort, baudrate=115200, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE)
    activePort.write(command)
    activePort.close()

def SendAndGet(query):
    # Extract the Comm Port from the textbox
    # Open the port then send the command.
    # Wait for a reply the pull it in until we have 100mSec of no new data coming in
    # Close the port when done
    thePort = gTxtPort.get('1.0', END)
    thePort = thePort.strip()
    activePort = serial.Serial(port = thePort, baudrate=115200, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE)
    activePort.timeout = .2
    activePort.write(query)
    bailCounter = 0
    while ((1 > activePort.in_waiting) and (10 > bailCounter)) :
        time.sleep(.01)
        bailCounter+=1

    if (0 < activePort.in_waiting): 
        bytesAvail = activePort.in_waiting
        time.sleep(.1)
        while(bytesAvail != activePort.in_waiting):
            bytesAvail = activePort.in_waiting
            time.sleep(.01)
    reply = bytearray(bytesAvail)
    len = activePort.readinto(reply)
    activePort.close()
    return reply

def Start_Clicked():
    gTxtFeedback.insert(INSERT, 'Start button clicked\r\n')
    command      = SMDPCompressorStart(gCompressorID)
    cmdWrapped   = SMDPWrapper(command)
    SendCommand(cmdWrapped)

def Stop_Clicked():
    gTxtFeedback.insert(INSERT, 'Stop button clicked\r\n')
    command      = SMDPCompressorStop(gCompressorID)
    cmdWrapped   = SMDPWrapper(command)
    SendCommand(cmdWrapped)

def Query_Clicked():
    gTxtFeedback.delete('1.0', END)
    gTxtFeedback.insert(INSERT, "Compressor Status: " + GetCompressorStatus() + "\r\n")
    gTxtFeedback.insert(INSERT, "Coolant In: " + GetCoolantIn() + "\r\n")
    gTxtFeedback.insert(INSERT, "Coolant Out: " + GetCoolantOut() + "\r\n")
    gTxtFeedback.insert(INSERT, "Oil: " + GetOil() + "\r\n")
    gTxtFeedback.insert(INSERT, "Helium: " + GetHelium() + "\r\n")
    gTxtFeedback.insert(INSERT, "High Pressure: " + GetHighPressure() + "\r\n")
    gTxtFeedback.insert(INSERT, "Low Pressure: " + GetLowPressure() + "\r\n")

def GetCompressorStatus():
    query = SMDPWrapper(SMDPCompressorStatus(gCompressorID))
    reply = SendAndGet(query)
    tmpUnwrapped = SMDPUnwrapper(reply)
    isRunning = SMDPExtractBool(tmpUnwrapped)
    state = 'Running' if (isRunning) else 'Ideling'
    return state

def GetCoolantIn():
    query = SMDPWrapper(SMDPCoolantIn(gCompressorID))
    reply = SendAndGet(query)
    tmpUnwrapped = SMDPUnwrapper(reply)
    tempC = SMDPExtractTempOrPressure(tmpUnwrapped)  # the reply is in 1/10th Celcius
    tempC /= 10.0
    return FloatToString(CtoF(tempC))

def GetCoolantOut():
    query = SMDPWrapper(SMDPCoolantOut(gCompressorID))
    reply = SendAndGet(query)
    tmpUnwrapped = SMDPUnwrapper(reply)
    tempC = SMDPExtractTempOrPressure(tmpUnwrapped)  # the reply is in 1/10th Celcius
    tempC /= 10.0
    return FloatToString(CtoF(tempC))

def GetOil():
    query = SMDPWrapper(SMDPOil(gCompressorID))
    reply = SendAndGet(query)
    tmpUnwrapped = SMDPUnwrapper(reply)
    tempC = SMDPExtractTempOrPressure(tmpUnwrapped)  # the reply is in 1/10th Celcius
    tempC /= 10.0
    return FloatToString(CtoF(tempC))

def GetHelium():
    query = SMDPWrapper(SMDPHelium(gCompressorID))
    reply = SendAndGet(query)
    tmpUnwrapped = SMDPUnwrapper(reply)
    tempC = SMDPExtractTempOrPressure(tmpUnwrapped)  # the reply is in 1/10th Celcius
    tempC /= 10.0
    return FloatToString(CtoF(tempC))

def GetLowPressure():
    query = SMDPWrapper(SMDPLowPressure(gCompressorID))
    reply = SendAndGet(query)
    tmpUnwrapped = SMDPUnwrapper(reply)
    tempC = SMDPExtractTempOrPressure(tmpUnwrapped)  # the reply is in 1/10th Celcius
    tempC /= 10.0
    return FloatToString(CtoF(tempC))

def GetHighPressure():
    query = SMDPWrapper(SMDPHighPressure(gCompressorID))
    reply = SendAndGet(query)
    tmpUnwrapped = SMDPUnwrapper(reply)
    tempC = SMDPExtractTempOrPressure(tmpUnwrapped)  # the reply is in 1/10th Celcius
    tempC /= 10.0
    return FloatToString(CtoF(tempC))

def SMDPWrapper(data):
    # THe data to be returned will need to start with a [x02] and terminate with a [x0D]
    # To handle these bytes being in data they use the Escape char [x07]
    # This two character sequence to be used if one of the three bytes are in the stream are:
    # [x02] = [x07][x30]
    # [x0D] = [x07][x31]
    # [x07] = [x07][x32]
    # NOTE: THE CHECKSUM MUST BE CALCULATED BEFORE DOING THE ESCAPE CHARS
    
    # Place STX header on
    iChecksumBuilder = 0
    lstBuilder = [0x02]

    # Calculate the checksum while adding the bytes to the list
    for i in range(0, len(data), 1):
    
        iChecksumBuilder += data[i]
        if(0x02 == data[i]):
            lstBuilder.append(0x07)
            lstBuilder.append(0x30)
        elif (0x0D == data[i]):
            lstBuilder.append(0x07)
            lstBuilder.append(0x31)
        elif (0x07 == data[i]):
            lstBuilder.append(0x07)
            lstBuilder.append(0x32)
        else:
            lstBuilder.append(data[i])

    iChecksumBuilder = iChecksumBuilder % 256

    lstBuilder.append((0x30 + ((iChecksumBuilder & 0xF0) >> 4)))
    lstBuilder.append((0x30 + (iChecksumBuilder & 0x0F)))


    # Place terminationg CR
    lstBuilder.append(0x0D)

    # Convert list to byte array
    rtnWrapped = bytearray(lstBuilder)
    return rtnWrapped

def SMDPUnwrapper(data):

    # The data to be returned will remove the leading [x02] and terminating [x0D]
    # To handle these bytes being in data they use the Escape char [x07]
    # This two character sequence to be used if one of the three bytes are in the stream are:
    # [x02] = [x07][x30]
    # [x0D] = [x07][x31]
    # [x07] = [x07][x32]
    # NOTE: THE CHECKSUM MUST BE CALCULATED BEFORE DOING THE ESCAPE CHARS
    lstBuilder = []

    # The first byte must be STX header and last byte must be [CR ]
    if (0x02 != data[0]): raise Exception('Missing SMDP leading 0x02 char')
    if (0x0D != data[len(data) - 1]): raise Exception('Missing SMDP trailing 0x0D char')
    iChecksumBuilder = 0

    # Calculate the checksum while adding the bytes to the list
    bSkipByte = False
    for i in range(1, len(data) - 3, 1):
        if (False == bSkipByte):
            wkrByte = data[i]
            if (0x07 == wkrByte):
            
                wkrByte = data[i + 1]

                if (0x30 == wkrByte):
                    wkrByte = 0x02 
                    bSkipByte = True
                elif (0x31 == wkrByte):
                    wkrByte = 0x0D
                    bSkipByte = True
                elif (0x32 == wkrByte):
                    wkrByte = 0x07
                    bSkipByte = True
                else: raise Exception('Missing SMDP bad byte stuffing')
                
            
            lstBuilder.append(wkrByte)
            iChecksumBuilder += wkrByte
        else:
            bSkipByte = False
    

    iChecksumBuilder = iChecksumBuilder % 256

    byChecksumHigh = (0x30 + ((iChecksumBuilder & 0xF0) >> 4))
    byChecksumLow  = (0x30 + (iChecksumBuilder & 0x0F))

    if ((byChecksumHigh != data[len(data) - 3]) or (byChecksumLow != data[len(data) - 2])): raise Exception("Missing SMDP bad checksum")

    # Convert list to byte array
    rtnUnwrapped = bytearray(lstBuilder)
    return rtnUnwrapped
        
def SMDPCompressorStatus(ID):
    arrReturn = [ID, 0x80, 0x63, 0x5F, 0x95, 0x00]
    return arrReturn

def SMDPMotorCurrent(ID):
    arrReturn = [ID, 0x80, 0x63, 0x63, 0x8B, 0x00]
    return arrReturn

def SMDPCompressorStart(ID):
    arrReturn = [ID, 0x80, 0x61, 0xD5, 0x01, 0x00, 0x00, 0x00, 0x00, 0x01]
    return arrReturn

def SMDPCompressorStop(ID):
    arrReturn = [ID, 0x80, 0x61, 0xC5, 0x98, 0x00, 0x00, 0x00, 0x00, 0x01]
    return arrReturn

def SMDPCoolantIn(ID):
    arrReturn = [ID, 0x80, 0x63, 0x0D, 0x8F, 0x00]
    return arrReturn

def SMDPCoolantOut(ID):
    arrReturn = [ID, 0x80, 0x63, 0x0D, 0x8F, 0x01]
    return arrReturn

def SMDPHelium(ID):
    arrReturn = [ID, 0x80, 0x63, 0x0D, 0x8F, 0x02]
    return arrReturn

def SMDPOil(ID):
    arrReturn = [ID, 0x80, 0x63, 0x0D, 0x8F, 0x03]
    return arrReturn

def SMDPHighPressure(ID):
    arrReturn = [ID, 0x80, 0x63, 0xAA, 0x50, 0x00]
    return arrReturn

def SMDPLowPressure(ID):
    arrReturn = [ID, 0x80, 0x63, 0xAA, 0x50, 0x01]
    return arrReturn

def SMDPExtractTempOrPressure(theData):
    fReturn = 0.0
    fReturn = 0x10000 * theData[0x06]
    fReturn += 0x1000 * theData[0x07]
    fReturn += 0x100 * theData[0x08]
    fReturn += theData[0x09]
    return fReturn

def SMDPExtractBool(theData):
    bReturn = (0 < theData[0x09])
    return bReturn

def CtoF(tempInC):
    return tempInC * 9 / 5 + 32

def FloatToString(theNumber):
    fNumber = round(theNumber, 1)
    return str(fNumber)

def main():
    gWindow.title("CP & CPA SMDP")
    gWindow.geometry('700x500')

    lblIP = Label(gWindow, text="Serial Port:")
    lblIP.grid(column=0, row=0)

    # this attempts to pre fill the comm port text box with the highest comm port available
    gTxtPort.grid(column=1, row=0)
    ports = serial.tools.list_ports.comports()
    if (0 < len(ports)):
        gTxtPort.delete('1.0', END)
        gTxtPort.insert('1.0',ports[len(ports)-1].device)

    btnStart = Button(gWindow, text="Press Start", bg="LawnGreen", command=Start_Clicked)
    btnStart.grid(column=0, row=1)

    btnStop = Button(gWindow, text="Press Stop", bg="Salmon", command=Stop_Clicked)
    btnStop.grid(column=1, row=1)

    btnQuery = Button(gWindow, text="Get Status", bg="LightGray", command=Query_Clicked)
    btnQuery.grid(column=2, row=1)

    gTxtFeedback.grid(column=0, row=2, columnspan=3)

    gWindow.mainloop()


if __name__ == '__main__':
    main()
