import socket
import struct
from tkinter import Tk, Button, INSERT, END, Label, Text
from tkinter import scrolledtext

# ----  Global Variables ----
gWindow = Tk()
gTxtIP = Text(gWindow, height=1, width=40)
gTxtFeedback = scrolledtext.ScrolledText(gWindow)

def TextBoxInput(e):
    # We arrived here via an enter key press
    # We want to strip off that <CR> at the end then treat it like the button click
    tmp = gTxtIP.get('1.0', END)
    tmpLen = len(tmp)
    tmp = tmp[0:tmpLen-1]
    gTxtIP.delete(1.0,"end")
    gTxtIP.insert(1.0, tmp)
    Query_Clicked();
    
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

def buildRegistersQuery():
    query = bytes([0x09, 0x99,  # Message ID
                   0x00, 0x00,  # Unused
                   0x00, 0x06,  # Message size in bytes
                   0x01,        # Slave Address
                   0x04,        # Function Code  3= Read HOLDING registers, 4 read INPUT registers
                   0x00,0x01,   # The starting Register Number
                   0x00,0x09])  # How many to read
    return query

def FloatToString(theNumber):
    fNumber = round(theNumber, 1)
    return str(fNumber)


def buildOperatingState(stateNumber):
    strReturn = 'Unknown State: ' + str(stateNumber)
    if 0 == stateNumber:
        strReturn = 'Off'
    elif 1 == stateNumber:
        strReturn = 'Trap Flush'
    elif 2 == stateNumber:
        strReturn = 'Initial Cooldown'
    elif 3 == stateNumber:
        strReturn = 'Final Cooldown'
    elif 4 == stateNumber:
        strReturn = 'Initilizing Sensor'
    elif 5 == stateNumber:
        strReturn = 'Purifying'
    elif 6 == stateNumber:
        strReturn = 'Vacuum Jacket Pump Prep'
    elif 7 == stateNumber:
        strReturn = 'Vacuum Jacket Pumping'
    elif 8 == stateNumber:
        strReturn = 'Regeneration Prep'
    elif 9 == stateNumber:
        strReturn = 'Regenerating'
    elif 10 == stateNumber:
        strReturn = 'In Transition'
    elif 11 == stateNumber:
        strReturn = 'Error'
    elif 12 == stateNumber:
        strReturn = 'Technician'
    elif 13 == stateNumber:
        strReturn = 'Cycling - Cooling Down'
    elif 14 == stateNumber:
        strReturn = 'Cycling - Leak Check'
    elif 15 == stateNumber:
        strReturn = 'Cycling - Warming Up'
    elif 16 == stateNumber:
        strReturn = 'Transition to off'
    elif 17 == stateNumber:
        strReturn = 'Deplugging in progress'
    elif 30 == stateNumber:
        strReturn = 'Interruption - Low Input Pressure'
    elif 31 == stateNumber:
        strReturn = 'Interruption - Plug Detected'
    elif 32 == stateNumber:
        strReturn = 'Interruption - Purity Sensor Malfunction'
    elif 33 == stateNumber:
        strReturn = 'Interruption - Pressure Sensor Malfunction'
    elif 34 == stateNumber:
        strReturn = 'Interruption - Temperature Sensor Malfunction'
    return strReturn 


def breakdownReplyData(rawData):
    gTxtFeedback.delete('1.0',END)
    gTxtFeedback.insert(INSERT, "Bytes Received: " + str(len(rawData)) + "\r\n")

    # Inlet
    #   Replies are 2 bytes in size, but int vars in python are 4 bytes
    #   If it appears to be a negative value prefix a couple 0xFF bytes
    wkrBytes = bytes([rawData[9], rawData[10]])
    if(0xef < rawData[9]):
       wkrBytes = bytes([0xff, 0xff, rawData[9], rawData[10]])
    iInletPsi = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fInletPsi = float(iInletPsi) / 10.0
    gTxtFeedback.insert(INSERT, "Inlet PSI: " + FloatToString(fInletPsi) + "\r\n")


    # Outlet
    wkrBytes = bytes([rawData[11], rawData[12]])
    if(0xef < rawData[11]):
       wkrBytes = bytes([0xff, 0xff, rawData[11], rawData[12]])
    iOutletPsi = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fOutletPsi = float(iOutletPsi) / 10.0
    gTxtFeedback.insert(INSERT, "Outlet PSI: " + FloatToString(fOutletPsi) + "\r\n")


    # Trap Temp
    wkrBytes = bytes([rawData[13], rawData[14]])
    if(0xef < rawData[13]):
       wkrBytes = bytes([0xff, 0xff, rawData[13], rawData[14]])
    iTrapTemp = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fTrapTemp = float(iTrapTemp) / 10.0
    gTxtFeedback.insert(INSERT, "Trap Temp: " + FloatToString(fTrapTemp) + "\r\n")


    # Counterflow Temp
    wkrBytes = bytes([rawData[15], rawData[16]])
    if(0xef < rawData[15]):
       wkrBytes = bytes([0xff, 0xff, rawData[15], rawData[16]])
    iCounterflowTemp = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fCounterflowTemp = float(iCounterflowTemp) / 10.0
    gTxtFeedback.insert(INSERT, "Counterflow Temp: " + FloatToString(fCounterflowTemp) + "\r\n")


    # Purity Reader
    wkrBytes = bytes([rawData[17], rawData[18]])
    if(0xef < rawData[17]):
       wkrBytes = bytes([0xff, 0xff, rawData[17], rawData[18]])
    iPurity = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fPurity = float(iPurity) / 10.0
    gTxtFeedback.insert(INSERT, "Purity: " + FloatToString(fPurity) + "\r\n")


    # Purity LED
    wkrBytes = bytes([rawData[19], rawData[20]])
    iPurity = int.from_bytes(wkrBytes, byteorder='big')
    gTxtFeedback.insert(INSERT, "Purity LED: " + FloatToString(iPurity) + "\r\n")


    # Purifying Hrs
    wkrBytes = bytes([rawData[21], rawData[22]])
    iPurityTime = int.from_bytes(wkrBytes, byteorder='big')
    fPurityTime = float(iPurityTime) / 10.0
    gTxtFeedback.insert(INSERT, "Purifying Hrs: " + FloatToString(fPurityTime) + "\r\n")


    # Vacuum Hrs
    wkrBytes = bytes([rawData[23], rawData[24]])
    iVacuumTime = int.from_bytes(wkrBytes, byteorder='big')
    fVacuumTime = float(iVacuumTime) / 10.0
    gTxtFeedback.insert(INSERT, "Vacuum Hrs: " + FloatToString(fVacuumTime) + "\r\n")

    # Operating State
    wkrBytes = bytes([rawData[25], rawData[26]])
    iState = int.from_bytes(wkrBytes, byteorder='big')
    gTxtFeedback.insert(INSERT, "Operating State: " + buildOperatingState(iState) + "\r\n")

  



gWindow.bind('<Return>',TextBoxInput);

def main():
    gWindow.title("Automatic Purifier ModbusTCP")
    gWindow.geometry('700x500')

    lblIP = Label(gWindow, text="IP Address:")
    lblIP.grid(column=0, row=0)

    gTxtIP.grid(column=1, row=0)
    gTxtIP.insert(1.0,'xxx.xxx.xxx.xxx')

    btnQuery = Button(gWindow, text="Get Status", bg="LightGray", command=Query_Clicked)
    btnQuery.grid(column=0, row=1)

    gTxtFeedback.grid(column=0, row=2, columnspan=3)

    gWindow.mainloop()


if __name__ == '__main__':
    main()
