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

def SendCommand(command):
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
    SendCommand(buildStartCompressorCommand())

def Stop_Clicked():
    gTxtFeedback.insert(INSERT, 'Stop button clicked\r\n')
    SendCommand(buildStopCompressorCommand())

def Query_Clicked():
    data = SendAndGet(buildRegistersQuery())
    breakdownReplyData(data)

def buildStartCompressorCommand():
    command = bytes([0x10,        # Slave Address
                     0x06,        # Function Code  6= Write a single Holding register
                     0x00,0x01,   # The register number
                     0x00,0x01,   # The value
                     0x1A,0x8B])  # Checksum
    return command

def buildStopCompressorCommand():
    command = bytes([0x10,        # Slave Address
                     0x06,        # Function Code  6= Write a single Holding register
                     0x00,0x01,   # The register number
                     0xFF,0xFF,   # The value
                     0xDA,0xFB])  # Checksum
    return command

def buildRegistersQuery():
    query = bytes([0x10,        # Slave Address
                   0x04,        # Function Code  3= Read HOLDING registers, 4 read INPUT registers
                   0x00,0x01,   # The starting Register Number
                   0x00,0x37,   # How many to read
                   0xE3,0x5D])  # Checksum
    return query

def FloatToString(theNumber):
    fNumber = round(theNumber, 1)
    return str(fNumber)

def breakdownReplyData(rawData):
    gTxtFeedback.delete('1.0',END)
    gTxtFeedback.insert(INSERT, "Bytes Received: " + str(len(rawData)) + "\r\n")

    wkrBytes = bytes([rawData[3], rawData[4]])
    iOperatingState = int.from_bytes(wkrBytes, byteorder='big')
    gTxtFeedback.insert(INSERT, "Operating State: " + buildOperatingState(iOperatingState) + "\r\n")
    
    wkrBytes = bytes([rawData[5], rawData[6]])
    iPumpState = int.from_bytes(wkrBytes, byteorder='big')
    gTxtFeedback.insert(INSERT, "Compressor State: " + buildCompressorState(iPumpState) + "\r\n")

    wkrBytes = bytes([rawData[107], rawData[108], rawData[105], rawData[106]])
    iWarn = int.from_bytes(wkrBytes, byteorder='big')
    gTxtFeedback.insert(INSERT, "Warning Number: " + str(iWarn) + "\r\n")
    gTxtFeedback.insert(INSERT, "   Warnings: " + buildMessage(iWarn) + "\r\n")

    wkrBytes = bytes([rawData[111], rawData[112], rawData[109], rawData[110]])
    iAlarm = int.from_bytes(wkrBytes, byteorder='big')
    gTxtFeedback.insert(INSERT, "Alarm Number: " + str(iAlarm) + "\r\n")
    gTxtFeedback.insert(INSERT, "   Alarms: " + buildMessage(iAlarm) + "\r\n")

    wkrBytes = bytes([rawData[81], rawData[82]])
    iCoolantIn = int.from_bytes(wkrBytes, byteorder='big')
    fCoolantIn = float(iCoolantIn) / 10.0
    gTxtFeedback.insert(INSERT, "Coolant In: " + FloatToString(fCoolantIn) + "\r\n")

    wkrBytes = bytes([rawData[83], rawData[84]])
    iCoolantOut = int.from_bytes(wkrBytes, byteorder='big')
    fCoolantOut = float(iCoolantOut) / 10.0
    gTxtFeedback.insert(INSERT, "Coolant Out: " + FloatToString(fCoolantOut) + "\r\n")

    wkrBytes = bytes([rawData[85], rawData[86]])
    iOil = int.from_bytes(wkrBytes, byteorder='big')
    fOil = float(iOil) / 10.0
    gTxtFeedback.insert(INSERT, "Oil: " + FloatToString(fOil) + "\r\n")

    wkrBytes = bytes([rawData[87], rawData[88]])
    iHelium = int.from_bytes(wkrBytes, byteorder='big')
    fHelium = float(iHelium) / 10.0
    gTxtFeedback.insert(INSERT, "Helium: " + FloatToString(fHelium) + "\r\n")

    wkrBytes = bytes([rawData[89], rawData[90]])
    iLowPressure = int.from_bytes(wkrBytes, byteorder='big')
    fLowPressure = float(iLowPressure) / 10.0
    gTxtFeedback.insert(INSERT, "Low Pressure: " + FloatToString(fLowPressure) + "\r\n")

    wkrBytes = bytes([rawData[91], rawData[92]])
    iLowPressureAvg = int.from_bytes(wkrBytes, byteorder='big')
    fLowPressureAvg = float(iLowPressureAvg) / 10.0
    gTxtFeedback.insert(INSERT, "Low Pressure Avg: " + FloatToString(fLowPressureAvg) + "\r\n")

    wkrBytes = bytes([rawData[93], rawData[94]])
    iHighPressure = int.from_bytes(wkrBytes, byteorder='big')
    fHighPressure = float(iHighPressure) / 10.0
    gTxtFeedback.insert(INSERT, "High Pressure: " + FloatToString(fHighPressure) + "\r\n")


    wkrBytes = bytes([rawData[95], rawData[96]])
    iHighPressureAvg = int.from_bytes(wkrBytes, byteorder='big')
    fHighPressureAvg = float(iHighPressureAvg) / 10.0
    gTxtFeedback.insert(INSERT, "High Pressure Avg: " + FloatToString(fHighPressureAvg) + "\r\n")

    wkrBytes = bytes([rawData[97], rawData[98]])
    iDeltaPressureAvg = int.from_bytes(wkrBytes, byteorder='big')
    fDeltaPressureAvg = float(iDeltaPressureAvg) / 10.0
    gTxtFeedback.insert(INSERT, "Delta of Avg Pressures: " + FloatToString(fDeltaPressureAvg) + "\r\n")

    wkrBytes = bytes([rawData[99], rawData[100]])
    iMotorCurrent = int.from_bytes(wkrBytes, byteorder='big')
    fMotorCurrent = float(iMotorCurrent) / 10.0
    gTxtFeedback.insert(INSERT, "Motor Current: " + FloatToString(fMotorCurrent) + "\r\n")

    wkrBytes = bytes([rawData[103], rawData[104], rawData[101], rawData[102]])
    iHoursOfOperation = int.from_bytes(wkrBytes, byteorder='big')
    fHoursOfOperation = float(iHoursOfOperation) / 10.0
    gTxtFeedback.insert(INSERT, "Hours Of Operation: " + FloatToString(fHoursOfOperation) + "\r\n")

    gTxtFeedback.insert(INSERT, "Pressure Scale: " + getPressureScale(rawData[60]) + "\r\n")

    gTxtFeedback.insert(INSERT, "Temperature Scale: " + getTempScale(rawData[62]) + "\r\n")

    wkrBytes = bytes([rawData[63], rawData[64]])
    iPanelSN = int.from_bytes(wkrBytes, byteorder='big')
    gTxtFeedback.insert(INSERT, "Panel Serial Number: " + str(iPanelSN) + "\r\n")

    gTxtFeedback.insert(INSERT, "Model Numbers: " + buildModel(rawData[65], rawData[66])  + "\r\n")

    gTxtFeedback.insert(INSERT, "Software Rev: " + str(rawData[67]) + "." + str(rawData[68]) + "\r\n")



def getTempScale(lowByte):
    strReturn = 'F'
    if 1 == lowByte:
        strReturn = 'C'
    elif 2 == lowByte:
        strReturn = 'K'
    return strReturn
    

def getPressureScale(lowByte):
    strReturn = 'psi'
    if 1 == lowByte:
        strReturn = 'Bar'
    elif 2 == lowByte:
        strReturn = 'KPA'
    return strReturn
    

def buildModel(highByte, lowByte):
    strReturn = 'CPA'
    if 1 == highByte:
        strReturn = strReturn + '08'
    elif 2 == highByte:
        strReturn = strReturn + '09'
    elif 3 == highByte:
        strReturn = strReturn + '10'
    elif 4 == highByte:
        strReturn = strReturn + '11'
    elif 5 == highByte:
        strReturn = strReturn + '28'

    if 1 == lowByte:
        strReturn = strReturn + 'A1'
    elif 2 == lowByte:
        strReturn = strReturn + '01'
    elif 3 == lowByte:
        strReturn = strReturn + '02'
    elif 4 == lowByte:
        strReturn = strReturn + '03'
    elif 5 == lowByte:
        strReturn = strReturn + 'H3'
    elif 6 == lowByte:
        strReturn = strReturn + 'I3'
    elif 7 == lowByte:
        strReturn = strReturn + '04'
    elif 8 == lowByte:
        strReturn = strReturn + 'H4'
    elif 9 == lowByte:
        strReturn = strReturn + '05'
    elif 10 == lowByte:
        strReturn = strReturn + 'H5'
    elif 11 == lowByte:
        strReturn = strReturn + 'I6'
    elif 12 == lowByte:
        strReturn = strReturn + '06'
    elif 13 == lowByte:
        strReturn = strReturn + '07'
    elif 14 == lowByte:
        strReturn = strReturn + 'H7'
    elif 15 == lowByte:
        strReturn = strReturn + 'I7'
    elif 16 == lowByte:
        strReturn = strReturn + '08'
    elif 17 == lowByte:
        strReturn = strReturn + '09'
    elif 18 == lowByte:
        strReturn = strReturn + '9C'
    elif 19 == lowByte:
        strReturn = strReturn + '10'
    elif 20 == lowByte:
        strReturn = strReturn + '1I'
    elif 21 == lowByte:
        strReturn = strReturn + '11'
    elif 22 == lowByte:
        strReturn = strReturn + '12'
    elif 23 == lowByte:
        strReturn = strReturn + '13'
    elif 24 == lowByte:
        strReturn = strReturn + '14'
    return strReturn



def buildMessage(code):
    strReturn = "  "
    worker = code
    if (1073741824 <= worker):
        strReturn += "Inverter Comm Loss, "
        worker -= 1073741824
    if (536870912 <= worker):
        strReturn += "Driver Comm Loss, "
        worker -= 536870912
    if (268435456 <= worker):
        strReturn += "Inverter Error, "
        worker -= 268435456
    if (134217728 <= worker):
        strReturn += "Motor Current High, "
        worker -= 134217728
    if (67108864 <= worker):
        strReturn += "Motor Current Sensor, "
        worker -= 67108864
    if (33554432 <= worker):
        strReturn += "Low Pressure Sensor, "
        worker -= 33554432
    if (16777216 <= worker):
        strReturn += "High Pressure Sensor, "
        worker -= 16777216
    if (8388608 <= worker):
        strReturn += "Oil Sensor, "
        worker -= 8388608
    if (4194304 <= worker):
        strReturn += "Helium Sensor, "
        worker -= 4194304
    if (2097152 <= worker):
        strReturn += "Coolant Out Sensor, "
        worker -= 2097152
    if (1048576 <= worker):
        strReturn += "Coolant In Sensor, "
        worker -= 1048576
    if (524288 <= worker):
        strReturn += "Motor Stall, "
        worker -= 524288
    if (262144 <= worker):
        strReturn += "Static Pressure Low, "
        worker -= 262144
    if (131072 <= worker):
        strReturn += "Static Pressure High, "
        worker -= 131072
    if (65536 <= worker):
        strReturn += "Power Supply Error, "
        worker -= 65536
    if (32768 <= worker):
        strReturn += "Three Phase Error, "
        worker -= 32768 
    if (16384 <= worker):
        strReturn += "Motor Current Low, "
        worker -= 16384
    if (8192 <= worker):
        strReturn += "Delta Pressure Low, "
        worker -= 8192
    if (4096 <= worker):
        strReturn += "Delta Pressure High, "
        worker -= 4096
    if (2048 <= worker):
        strReturn += "High Pressure Low, "
        worker -= 2048
    if (1024 <= worker):
        strReturn += "High Pressure High, "
        worker -= 1024
    if (512 <= worker):
        strReturn += "Low Pressure Low, "
        worker -= 512
    if (256 <= worker):
        strReturn += "Low Pressure High, "
        worker -= 256
    if (128 <= worker):
        strReturn += "Helium Low, "
        worker -= 128
    if (64 <= worker):
        strReturn += "Helium High, "
        worker -= 64
    if (32 <= worker):
        strReturn += "Oil Low, "
        worker -= 32
    if (16 <= worker):
        strReturn += "Oil High, "
        worker -= 16
    if (8 <= worker):
        strReturn += "Coolant Out Low, "
        worker -= 8
    if (4 <= worker):
        strReturn += "Coolant Out High, "
        worker -= 4
    if (2 <= worker):
        strReturn += "Coolant In Low, "
        worker -= 2
    if (1 <= worker):
        strReturn += "Coolant In High, "
        worker -= 1
    #remove the final space & Comma if we have a message
    if (0 < len(strReturn.strip())):
        strReturn = strReturn.strip()
        strReturn = strReturn[0:len(strReturn)-1]
    else:
        strReturn = 'None'
    return strReturn


def buildCompressorState(stateNumber):
    return 'Running' if 0 < stateNumber else 'Idle' 

def buildOperatingState(stateNumber):
    strReturn = 'Unknown State'
    if 0 == stateNumber:
        strReturn = 'Ready to start'
    elif 2 == stateNumber:
        strReturn = 'Starting'
    elif 3 == stateNumber:
        strReturn = 'Running'
    elif 5 == stateNumber:
        strReturn = 'Stopping'
    elif 6 == stateNumber:
        strReturn = 'Error Lockout'
    elif 7 == stateNumber:
        strReturn = 'Error'
    elif 8 == stateNumber:
        strReturn = 'Helium Overtemp Cooldown'
    elif 9 == stateNumber:
        strReturn = 'Power Related Error'
    elif 15 == stateNumber:
        strReturn = 'Recovered From Error'
    return strReturn 

def main():
    gWindow.title("CPA3.0 Format Modbus")
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
