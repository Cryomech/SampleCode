import socket
import struct
from tkinter import Tk, Button, INSERT, END, Label, Text
from tkinter import scrolledtext

# ----  Global Variables ----
gWindow = Tk()
gTxtIP = Text(gWindow, height=1, width=40)
gTxtFeedback = scrolledtext.ScrolledText(gWindow)

def Start_Clicked():
    gTxtFeedback.insert(INSERT, 'Start button clicked\r\n')
    HOST = gTxtIP.get('1.0', END) #'192.168.1.27'    # The compressor's IP address
    HOST = HOST.strip()
    PORT = 502              # The port used by ModBus

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(buildStartCompressorCommand())
        data = s.recv(1024)
        s.close()

def Stop_Clicked():
    gTxtFeedback.insert(INSERT, 'Stop button clicked\r\n')
    HOST = gTxtIP.get('1.0', END) #'192.168.1.27'    # The compressor's IP address
    HOST = HOST.strip()
    PORT = 502              # The port used by ModBus

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(buildStopCompressorCommand())
        data = s.recv(1024)
        s.close()

def Query_Clicked():
    gTxtFeedback.insert(INSERT, 'Query button clicked\r\n')
    HOST = gTxtIP.get('1.0', END) #'192.168.1.27'    # The compressor's IP address
    HOST = HOST.strip()
    PORT = 502              # The port used by ModBus

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(buildRegistersQuery())
        data = s.recv(1024)
        breakdownReplyData(data)
        s.close()

def buildStartCompressorCommand():
    command = bytes([0x09, 0x99,  # Message ID
                    0x00, 0x00,  # Unused
                    0x00, 0x06,  # Message size in bytes
                    0x01,        # Slave Address
                    0x06,        # Function Code  6= Write a single Holding register
                    0x00,0x01,   # The register number
                    0x00,0x01])  # The value
    return command

def buildStopCompressorCommand():
    command = bytes([0x09, 0x99,  # Message ID
                    0x00, 0x00,  # Unused
                    0x00, 0x06,  # Message size in bytes
                    0x01,        # Slave Address
                    0x06,        # Function Code  6= Write a single Holding register
                    0x00,0x01,   # The register number
                    0xFF,0xFF])  # The value
    return command

def buildRegistersQuery():
    query = bytes([0x09, 0x99,  # Message ID
                   0x00, 0x00,  # Unused
                   0x00, 0x06,  # Message size in bytes
                   0x01,        # Slave Address
                   0x04,        # Function Code  3= Read HOLDING registers, 4 read INPUT registers
                   0x00,0x01,   # The starting Register Number
                   0x00,0x35])  # How many to read
    return query

def FloatToString(theNumber):
    fNumber = round(theNumber, 1)
    return str(fNumber)

def breakdownReplyData(rawData):
    gTxtFeedback.delete('1.0',END)
    gTxtFeedback.insert(INSERT, "Bytes Received: " + str(len(rawData)) + "\r\n")

    wkrBytes = bytes([rawData[9], rawData[10]])
    iOperatingState = int.from_bytes(wkrBytes, byteorder='big')
    gTxtFeedback.insert(INSERT, "Operating State: " + buildOperatingState(iOperatingState) + "\r\n")
    
    wkrBytes = bytes([rawData[11], rawData[12]])
    iPumpState = int.from_bytes(wkrBytes, byteorder='big')
    gTxtFeedback.insert(INSERT, "Compressor State: " + buildCompressorState(iPumpState) + "\r\n")
      
    wkrBytes = bytes([rawData[14], rawData[13], rawData[16], rawData[15]])
    tplWarn = struct.unpack('f', wkrBytes)
    iWarn = round(tplWarn[0])
    gTxtFeedback.insert(INSERT, "Warning Number: " + str(iWarn) + "\r\n")
    gTxtFeedback.insert(INSERT, "   Warnings: " + buildMessage(iWarn) + "\r\n")

    wkrBytes = bytes([rawData[18], rawData[17], rawData[20], rawData[19]])
    tplAlarm = struct.unpack('f', wkrBytes)
    iAlarm = round(tplAlarm[0])
    gTxtFeedback.insert(INSERT, "Alarm Number: " + str(iAlarm) + "\r\n")
    gTxtFeedback.insert(INSERT, "   Alarms: " + buildMessage(iAlarm) + "\r\n")

    wkrBytes = bytes([rawData[22], rawData[21], rawData[24], rawData[23]])
    fCoolantIn = struct.unpack('f', wkrBytes)
    gTxtFeedback.insert(INSERT, "Coolant In: " + FloatToString(fCoolantIn[0]) + "\r\n")

    wkrBytes = bytes([rawData[26], rawData[25], rawData[28], rawData[27]])
    fCoolantOut = struct.unpack('f', wkrBytes)
    gTxtFeedback.insert(INSERT, "Coolant Out: " + FloatToString(fCoolantOut[0]) + "\r\n")

    wkrBytes = bytes([rawData[30], rawData[29], rawData[32], rawData[31]])
    fOil = struct.unpack('f', wkrBytes)
    gTxtFeedback.insert(INSERT, "Oil: " + FloatToString(fOil[0]) + "\r\n")

    wkrBytes = bytes([rawData[34], rawData[33], rawData[36], rawData[35]])
    fHelium = struct.unpack('f', wkrBytes)
    gTxtFeedback.insert(INSERT, "Helium: " + FloatToString(fHelium[0]) + "\r\n")

    wkrBytes = bytes([rawData[38], rawData[37], rawData[40], rawData[39]])
    fLowP = struct.unpack('f', wkrBytes)
    gTxtFeedback.insert(INSERT, "Low Pressure: " + FloatToString(fLowP[0]) + "\r\n")

    wkrBytes = bytes([rawData[42], rawData[41], rawData[44], rawData[43]])
    fLowPAvg = struct.unpack('f', wkrBytes)
    gTxtFeedback.insert(INSERT, "Low Pressure Avg: " + FloatToString(fLowPAvg[0]) + "\r\n")

    wkrBytes = bytes([rawData[46], rawData[45], rawData[48], rawData[47]])
    fHighP = struct.unpack('f', wkrBytes)
    gTxtFeedback.insert(INSERT, "High Pressure: " + FloatToString(fHighP[0]) + "\r\n")

    wkrBytes = bytes([rawData[50], rawData[49], rawData[52], rawData[51]])
    fHighPAvg = struct.unpack('f', wkrBytes)
    gTxtFeedback.insert(INSERT, "High Pressure Avg: " + FloatToString(fHighPAvg[0]) + "\r\n")

    wkrBytes = bytes([rawData[54], rawData[53], rawData[56], rawData[55]])
    fDeltaP = struct.unpack('f', wkrBytes)
    gTxtFeedback.insert(INSERT, "Delta of Pressure Avgs: " + FloatToString(fDeltaP[0]) + "\r\n")

    wkrBytes = bytes([rawData[58], rawData[57], rawData[60], rawData[59]])
    fMotorCur = struct.unpack('f', wkrBytes)
    gTxtFeedback.insert(INSERT, "Motor Current: " + FloatToString(fMotorCur[0]) + "\r\n")

    wkrBytes = bytes([rawData[62], rawData[61], rawData[64], rawData[63]])
    fHoursOfOperation = struct.unpack('f', wkrBytes)
    gTxtFeedback.insert(INSERT, "Hours Of Operation: " + FloatToString(fHoursOfOperation[0]) + "\r\n")

    gTxtFeedback.insert(INSERT, "Pressure Scale: " + getPressureScale(rawData[66]) + "\r\n")

    gTxtFeedback.insert(INSERT, "Temperature Scale: " + getTempScale(rawData[68]) + "\r\n")

    wkrBytes = bytes([rawData[69], rawData[70]])
    iPanelSN = int.from_bytes(wkrBytes, byteorder='big')
    gTxtFeedback.insert(INSERT, "Panel Serial Number: " + str(iPanelSN) + "\r\n")

    gTxtFeedback.insert(INSERT, "Model Numbers: " + buildModel(rawData[71], rawData[72])  + "\r\n")

    gTxtFeedback.insert(INSERT, "Software Rev: " + str(rawData[73]) + "." + str(rawData[74])  + "\r\n")


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
    strReturn = '   '
    worker = code
    if (-1073741824 >= worker):
        strReturn += "Inverter Comm Loss, "
        worker -= -1073741824
    if (-536870912 >= worker):
        strReturn += "Driver Comm Loss, "
        worker -= -536870912
    if (-268435456 >= worker):
        strReturn += "Inverter Error, "
        worker -= -268435456
    if (-134217728 >= worker):
        strReturn += "Motor Current High, "
        worker -= -134217728
    if (-67108864 >= worker):
        strReturn += "Motor Current Sensor, "
        worker -= -67108864
    if (-33554432 >= worker):
        strReturn += "Low Pressure Sensor, "
        worker -= -33554432
    if (-16777216 >= worker):
        strReturn += "High Pressure Sensor, "
        worker -= -16777216
    if (-8388608 >= worker):
        strReturn += "Oil Sensor, "
        worker -= -8388608
    if (-4194304 >= worker):
        strReturn += "Helium Sensor, "
        worker -= -4194304
    if (-2097152 >= worker):
        strReturn += "Coolant Out Sensor, "
        worker -= -2097152
    if (-1048576 >= worker):
        strReturn += "Coolant In Sensor, "
        worker -= -1048576
    if (-524288 >= worker):
        strReturn += "Motor Stall, "
        worker -= -524288
    if (-262144 >= worker):
        strReturn += "Static Pressure Low, "
        worker -= -262144
    if (-131072 >= worker):
        strReturn += "Static Pressure High, "
        worker -= -131072 
    if (-65536 >= worker):
        strReturn += "Power Supply Error, "
        worker -= -65536 
    if (-32768 >= worker):
        strReturn += "Three Phase Error, "
        worker -= -32768 
    if (-16384 >= worker):
        strReturn += "Motor Current Low, "
        worker -= -16384
    if (-8192 >= worker):
        strReturn += "Delta Pressure Low, "
        worker -= -8192
    if (-4096 >= worker):
        strReturn += "Delta Pressure High, "
        worker -= -4096
    if (-2048 >= worker):
        strReturn += "High Pressure Low, "
        worker -= -2048
    if (-1024 >= worker):
        strReturn += "High Pressure High, "
        worker -= -1024
    if (-512 >= worker):
        strReturn += "Low Pressure Low, "
        worker -= -512
    if (-256 >= worker):
        strReturn += "Low Pressure High, "
        worker -= -256
    if (-128 >= worker):
        strReturn += "Helium Low, "
        worker -= -128 
    if (-64 >= worker):
        strReturn += "Helium High, "
        worker -= -64
    if (-32 >= worker):
        strReturn += "Oil Low, "
        worker -= -32
    if (-16 >= worker):
        strReturn += "Oil High, "
        worker -= -16
    if (-8 >= worker):
        strReturn += "Coolant Out Low, "
        worker -= -8
    if (-4 >= worker):
        strReturn += "Coolant Out High, "
        worker -= -4
    if (-2 >= worker):
        strReturn += "Coolant In Low, "
        worker -= -2
    if (-1 >= worker):
        strReturn += "Coolant In High, "
        worker -= -1
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
    gWindow.title("CPA2.0 Format ModbusTCP")
    gWindow.geometry('700x500')

    lblIP = Label(gWindow, text="IP Address:")
    lblIP.grid(column=0, row=0)

    gTxtIP.text = 'xxx.xxx.xxx.xxx'
    gTxtIP.grid(column=1, row=0)

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
