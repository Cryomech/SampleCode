import socket
import struct
from tkinter import Tk, Button, INSERT, END, Label, Text, Grid
from tkinter import scrolledtext
from tkinter import messagebox

# Create global objects
g_root = Tk()
g_txtIP = Text(g_root, height=1, width=40)
g_txtFeedback = scrolledtext.ScrolledText(g_root)


def TextBoxInput(e):
    # We arrived here via an enter key press
    # We want to strip off that <CR> at the end then treat it like the button click
    tmp = g_txtIP.get('1.0', END)
    tmpLen = len(tmp)
    tmp = tmp[0:tmpLen-1]
    g_txtIP.delete(1.0,"end")
    g_txtIP.insert(1.0, tmp)
    Query_Clicked();
    
def Query_Clicked():
    g_txtFeedback.insert(INSERT, 'Query button clicked\r\n')
    HOST = g_txtIP.get('1.0', END) #'192.168.1.27'    # The compressor's IP address
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
                   0x00,0x3C])  # How many to read
    return query

def FloatToString(theNumber, digitsRightOfDecimal):
    sDecimalPlaces = str(digitsRightOfDecimal)
    fNumber = round(theNumber, digitsRightOfDecimal)
    sFormat = '{:.' + sDecimalPlaces + 'f}'
    return sFormat.format(fNumber)


def buildOperatingMode(stateNumber):
    strReturn = 'Unknown State: ' + str(stateNumber)
    if 0 == stateNumber:
        strReturn = 'Off'
    elif 3 == stateNumber:
        strReturn = 'Single Head Compressor Regulated'
    elif 4 == stateNumber:
        strReturn = 'Single Head Heater Regulated'
    elif 5 == stateNumber:
        strReturn = 'Single Head Manual Mode'
    elif 6 == stateNumber:
        strReturn = 'Multi Head Mode'
    elif 21 == stateNumber:
        strReturn = 'Fault: Compressor Comms Loss'
    elif 22 == stateNumber:
        strReturn = 'Fault: Compressor Comms Partial Loss'
    elif 23 == stateNumber:
        strReturn = 'Fault: Default Compressor ON'
    elif 24 == stateNumber:
        strReturn = 'Fault: Single Head Compressor Regulated, Assumed Full'
    elif 25 == stateNumber:
        strReturn = 'Fault: Single Head Heater Regulated, Assumed Full'
    elif 26 == stateNumber:
        strReturn = 'Fault: Single Head Manual, Assumed Full'
    elif 27 == stateNumber:
        strReturn = 'Fault: Single Head Forced Compressor Regulation'
    elif 28 == stateNumber:
        strReturn = 'Fault: Cryo-Temp Based Regulation'
    return strReturn 

def bytesToFeedback(theBytes):
    g_txtFeedback.insert(INSERT, bytes.hex(theBytes))
    g_txtFeedback.insert(INSERT, '\r\n')
    #messagebox.showinfo(title="Greetings", message=bytes.hex(theBytes))
                    
def breakdownReplyData(rawData):
    g_txtFeedback.delete('1.0',END)
    g_txtFeedback.insert(INSERT, "Bytes Received: " + str(len(rawData)) + "\r\n")

    # Volume  30,001
    #   Replies are 2 bytes in size, but int vars in python are 4 bytes
    #   If it appears to be a negative value prefix a couple 0xFF bytes
    wkrBytes = bytes([rawData[9], rawData[10]])
    if(0xef < rawData[9]):
       wkrBytes = bytes([0xff, 0xff, rawData[9], rawData[10]])
    iInletPsi = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fInletPsi = float(iInletPsi) / 10.0
    g_txtFeedback.insert(INSERT, "Volume: " + FloatToString(fInletPsi, 1) + "\r\n")


    # Operating Mode  30,002
    wkrBytes = bytes([rawData[11], rawData[12]])
    iState = int.from_bytes(wkrBytes, byteorder='big')
    g_txtFeedback.insert(INSERT, "Operating Mode: " + buildOperatingMode(iState) + "\r\n")


    # Percent Full  30,003
    wkrBytes = bytes([rawData[13], rawData[14]])
    if(0xef < rawData[13]):
       wkrBytes = bytes([0xff, 0xff, rawData[13], rawData[14]])
    iTrapTemp = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fTrapTemp = float(iTrapTemp) / 10.0
    g_txtFeedback.insert(INSERT, "Percent Full: " + FloatToString(fTrapTemp, 1) + "%\r\n")


    # Depth  30,004
    wkrBytes = bytes([rawData[15], rawData[16]])
    if(0xef < rawData[15]):
       wkrBytes = bytes([0xff, 0xff, rawData[15], rawData[16]])
    iCounterflowTemp = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fCounterflowTemp = float(iCounterflowTemp) / 10.0
    g_txtFeedback.insert(INSERT, "Depth: " + FloatToString(fCounterflowTemp, 1) + " cm\r\n")


    # Heater Power in Watts  30,005
    wkrBytes = bytes([rawData[17], rawData[18]])
    if(0xef < rawData[17]):
       wkrBytes = bytes([0xff, 0xff, rawData[17], rawData[18]])
    iWatts = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    #messagebox.showinfo("iWatts", str(iWatts))
    fWatts = float(iWatts) / 1000.0
    g_txtFeedback.insert(INSERT, "Watts: " + FloatToString(fWatts, 3) + "\r\n")


    # Pressure  30,006
    wkrBytes = bytes([rawData[19], rawData[20]])
    if(0xef < rawData[19]):
       wkrBytes = bytes([0xff, 0xff, rawData[19], rawData[20]])
    iPressure = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fPressure = float(iPressure) / 100.0
    g_txtFeedback.insert(INSERT, "Pressure: " + FloatToString(fPressure, 2) + "\r\n\r\n")


    # Head A  30,010
    wkrBytes = bytes([rawData[27], rawData[28]])
    iTempA = int.from_bytes(wkrBytes, byteorder='big')
    fTempA = float(iTempA) / 100.0
    g_txtFeedback.insert(INSERT, "Temp A: " + FloatToString(fTempA, 2) + "\r\n")


    # Compressor A is running check  30,011
    wkrBytes = bytes([rawData[29], rawData[30]])
    iIsRunning = int.from_bytes(wkrBytes, byteorder='big')
    if (0 < iIsRunning):
        g_txtFeedback.insert(INSERT, "Comp A is running\r\n")
    else:
        g_txtFeedback.insert(INSERT, "Comp A is idle\r\n")

    # Compressor A High Pressure  30,012
    wkrBytes = bytes([rawData[31], rawData[32]])
    if(0xef < rawData[31]):
       wkrBytes = bytes([0xff, 0xff, rawData[31], rawData[32]])
    iHighP_A = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fHighP_A = float(iHighP_A) / 10.0
    g_txtFeedback.insert(INSERT, "Comp A High P: " + FloatToString(fHighP_A, 1) + "\r\n")


    # Compressor A Low Pressure  30,013
    wkrBytes = bytes([rawData[33], rawData[34]])
    if(0xef < rawData[33]):
       wkrBytes = bytes([0xff, 0xff, rawData[33], rawData[34]])
    iLowP_A = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fLowP_A = float(iLowP_A) / 10.0
    g_txtFeedback.insert(INSERT, "Comp A Low P: " + FloatToString(fLowP_A, 1) + "\r\n")

    # Compressor A Coolant In  30,014
    wkrBytes = bytes([rawData[35], rawData[36]])
    if(0xef < rawData[35]):
       wkrBytes = bytes([0xff, 0xff, rawData[35], rawData[36]])
    iCoolantIn_A = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fCoolantIn_A = float(iCoolantIn_A) / 10.0
    g_txtFeedback.insert(INSERT, "Comp A Coolant In: " + FloatToString(fCoolantIn_A, 1) + "\r\n")

    # Compressor A Coolant Out  30,015
    wkrBytes = bytes([rawData[37], rawData[38]])
    if(0xef < rawData[37]):
       wkrBytes = bytes([0xff, 0xff, rawData[37], rawData[38]])
    iCoolantOut_A = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fCoolantOut_A = float(iCoolantOut_A) / 10.0
    g_txtFeedback.insert(INSERT, "Comp A Coolant Out: " + FloatToString(fCoolantOut_A, 1) + "\r\n")

    # Compressor A Oil  30,016
    wkrBytes = bytes([rawData[39], rawData[40]])
    if(0xef < rawData[39]):
       wkrBytes = bytes([0xff, 0xff, rawData[39], rawData[40]])
    iOil_A = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fOil_A = float(iOil_A) / 10.0
    g_txtFeedback.insert(INSERT, "Comp A Oil: " + FloatToString(fOil_A, 1) + "\r\n")

    # Compressor A Helium  30,017
    wkrBytes = bytes([rawData[41], rawData[42]])
    if(0xef < rawData[41]):
       wkrBytes = bytes([0xff, 0xff, rawData[41], rawData[42]])
    iHelium_A = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fHelium_A = float(iHelium_A) / 10.0
    g_txtFeedback.insert(INSERT, "Comp A Helium: " + FloatToString(fHelium_A, 1) + "\r\n")

    # Compressor A Motor Current  30,018
    wkrBytes = bytes([rawData[43], rawData[44]])
    if(0xef < rawData[43]):
       wkrBytes = bytes([0xff, 0xff, rawData[43], rawData[44]])
    iCurrent_A = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fCurrent_A = float(iCurrent_A) / 10.0
    g_txtFeedback.insert(INSERT, "Comp A Motor Current: " + FloatToString(fCurrent_A, 1) + "\r\n")

    # Compressor A Hours  30,019 & 20
    wkrBytes = bytes([rawData[45], rawData[46],rawData[47], rawData[48]])
    iHrs_A = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fHrs_A = float(iHrs_A) / 10.0
    g_txtFeedback.insert(INSERT, "Comp A Hours: " + FloatToString(fHrs_A, 1) + "\r\n\r\n")



    #===============================================
    # Head B  30,030
    wkrBytes = bytes([rawData[67], rawData[68]])
    iTempB = int.from_bytes(wkrBytes, byteorder='big')
    fTempB = float(iTempB) / 100.0
    g_txtFeedback.insert(INSERT, "Temp B: " + FloatToString(fTempB, 2) + "\r\n")


    # Compressor B is running check  30,031
    wkrBytes = bytes([rawData[69], rawData[70]])
    iIsRunning = int.from_bytes(wkrBytes, byteorder='big')
    if (0 < iIsRunning):
        g_txtFeedback.insert(INSERT, "Comp B is running\r\n")
    else:
        g_txtFeedback.insert(INSERT, "Comp B is idle\r\n")

    # Compressor B High Pressure  30,032
    wkrBytes = bytes([rawData[71], rawData[72]])
    if(0xef < rawData[71]):
       wkrBytes = bytes([0xff, 0xff, rawData[71], rawData[72]])
    iHighP_B = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fHighP_B = float(iHighP_B) / 10.0
    g_txtFeedback.insert(INSERT, "Comp B High P: " + FloatToString(fHighP_B, 1) + "\r\n")


    # Compressor B Low Pressure  30,033
    wkrBytes = bytes([rawData[73], rawData[74]])
    if(0xef < rawData[73]):
       wkrBytes = bytes([0xff, 0xff, rawData[73], rawData[74]])
    iLowP_B = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fLowP_B = float(iLowP_B) / 10.0
    g_txtFeedback.insert(INSERT, "Comp B Low P: " + FloatToString(fLowP_B, 1) + "\r\n")

    # Compressor B Coolant In  30,034
    wkrBytes = bytes([rawData[75], rawData[76]])
    if(0xef < rawData[75]):
       wkrBytes = bytes([0xff, 0xff, rawData[75], rawData[76]])
    iCoolantIn_B = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fCoolantIn_B = float(iCoolantIn_B) / 10.0
    g_txtFeedback.insert(INSERT, "Comp B Coolant In: " + FloatToString(fCoolantIn_B, 1) + "\r\n")

    # Compressor B Coolant Out  30,035
    wkrBytes = bytes([rawData[77], rawData[78]])
    if(0xef < rawData[77]):
       wkrBytes = bytes([0xff, 0xff, rawData[77], rawData[78]])
    iCoolantOut_B = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fCoolantOut_B = float(iCoolantOut_B) / 10.0
    g_txtFeedback.insert(INSERT, "Comp B Coolant Out: " + FloatToString(fCoolantOut_B, 1) + "\r\n")

    # Compressor B Oil  30,036
    wkrBytes = bytes([rawData[79], rawData[80]])
    if(0xef < rawData[79]):
       wkrBytes = bytes([0xff, 0xff, rawData[79], rawData[80]])
    iOil_B = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fOil_B = float(iOil_B) / 10.0
    g_txtFeedback.insert(INSERT, "Comp B Oil: " + FloatToString(fOil_B, 1) + "\r\n")

    # Compressor B Helium  30,037
    wkrBytes = bytes([rawData[81], rawData[82]])
    if(0xef < rawData[81]):
       wkrBytes = bytes([0xff, 0xff, rawData[81], rawData[82]])
    iHelium_B = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fHelium_B = float(iHelium_B) / 10.0
    g_txtFeedback.insert(INSERT, "Comp  Helium: " + FloatToString(fHelium_B, 1) + "\r\n")

    # Compressor B Motor Current  30,038
    wkrBytes = bytes([rawData[83], rawData[84]])
    if(0xef < rawData[83]):
       wkrBytes = bytes([0xff, 0xff, rawData[83], rawData[84]])
    iCurrent_B = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fCurrent_B = float(iCurrent_B) / 10.0
    g_txtFeedback.insert(INSERT, "Comp B Motor Current: " + FloatToString(fCurrent_B, 1) + "\r\n")

    # Compressor B Hours  30,039 & 40
    wkrBytes = bytes([rawData[85], rawData[86],rawData[87], rawData[88]])
    iHrs_B = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fHrs_B = float(iHrs_B) / 10.0
    g_txtFeedback.insert(INSERT, "Comp B Hours: " + FloatToString(fHrs_B, 1) + "\r\n\r\n")



    #===============================================
    # Head C  30,050
    wkrBytes = bytes([rawData[107], rawData[108]])
    iTempC = int.from_bytes(wkrBytes, byteorder='big')
    fTempC = float(iTempC) / 100.0
    g_txtFeedback.insert(INSERT, "Temp C: " + FloatToString(fTempC, 2) + "\r\n")

    # Compressor C is running check  30,051
    wkrBytes = bytes([rawData[109], rawData[110]])
    iIsRunning = int.from_bytes(wkrBytes, byteorder='big')
    if (0 < iIsRunning):
        g_txtFeedback.insert(INSERT, "Comp C is running\r\n")
    else:
        g_txtFeedback.insert(INSERT, "Comp C is idle\r\n")

    # Compressor C High Pressure  30,052
    wkrBytes = bytes([rawData[111], rawData[112]])
    if(0xef < rawData[111]):
       wkrBytes = bytes([0xff, 0xff, rawData[111], rawData[112]])
    iHighP_C = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fHighP_C = float(iHighP_C) / 10.0
    g_txtFeedback.insert(INSERT, "Comp C High P: " + FloatToString(fHighP_C, 1) + "\r\n")

    # Compressor C Low Pressure  30,053
    wkrBytes = bytes([rawData[113], rawData[114]])
    if(0xef < rawData[113]):
       wkrBytes = bytes([0xff, 0xff, rawData[113], rawData[114]])
    iLowP_C = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fLowP_C = float(iLowP_C) / 10.0
    g_txtFeedback.insert(INSERT, "Comp C Low P: " + FloatToString(fLowP_C, 1) + "\r\n")

    # Compressor C Coolant In  30,054
    wkrBytes = bytes([rawData[115], rawData[116]])
    if(0xef < rawData[115]):
       wkrBytes = bytes([0xff, 0xff, rawData[115], rawData[116]])
    iCoolantIn_C = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fCoolantIn_C = float(iCoolantIn_C) / 10.0
    g_txtFeedback.insert(INSERT, "Comp C Coolant In: " + FloatToString(fCoolantIn_C, 1) + "\r\n")

    # Compressor C Coolant Out  30,055
    wkrBytes = bytes([rawData[117], rawData[118]])
    if(0xef < rawData[117]):
       wkrBytes = bytes([0xff, 0xff, rawData[117], rawData[118]])
    iCoolantOut_C = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fCoolantOut_C = float(iCoolantOut_C) / 10.0
    g_txtFeedback.insert(INSERT, "Comp C Coolant Out: " + FloatToString(fCoolantOut_C, 1) + "\r\n")

    # Compressor C Oil  30,056
    wkrBytes = bytes([rawData[119], rawData[120]])
    if(0xef < rawData[119]):
       wkrBytes = bytes([0xff, 0xff, rawData[119], rawData[120]])
    iOil_C = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fOil_C = float(iOil_C) / 10.0
    g_txtFeedback.insert(INSERT, "Comp C Oil: " + FloatToString(fOil_C, 1) + "\r\n")

    # Compressor C Helium  30,057
    wkrBytes = bytes([rawData[121], rawData[122]])
    if(0xef < rawData[121]):
       wkrBytes = bytes([0xff, 0xff, rawData[121], rawData[122]])
    iHelium_C = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fHelium_C = float(iHelium_C) / 10.0
    g_txtFeedback.insert(INSERT, "Comp C Helium: " + FloatToString(fHelium_C, 1) + "\r\n")

    # Compressor C Motor Current  30,058
    wkrBytes = bytes([rawData[123], rawData[124]])
    if(0xef < rawData[123]):
       wkrBytes = bytes([0xff, 0xff, rawData[123], rawData[124]])
    iCurrent_C = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fCurrent_C = float(iCurrent_C) / 10.0
    g_txtFeedback.insert(INSERT, "Comp C Motor Current: " + FloatToString(fCurrent_C, 1) + "\r\n")

    # Compressor C Hours  30,059 & 20
    wkrBytes = bytes([rawData[125], rawData[126],rawData[127], rawData[128]])
    iHrs_C = int.from_bytes(wkrBytes, byteorder='big', signed=True)
    fHrs_C = float(iHrs_C) / 10.0
    g_txtFeedback.insert(INSERT, "Comp C Hours: " + FloatToString(fHrs_C, 1) + "\r\n\r\n")



def main():

    # Define window
    g_root.title("LHeP ModbusTCP")
    g_root.geometry('700x500')
    g_root.bind('<Return>',TextBoxInput);

    # Specify Grid
    #Grid.rowconfigure(g_root,0,weight=1)
    #Grid.rowconfigure(g_root,1,weight=1)
    Grid.rowconfigure(g_root,2,weight=1)
    Grid.columnconfigure(g_root,0,weight=1)
    Grid.columnconfigure(g_root,1,weight=1)
    Grid.columnconfigure(g_root,2,weight=3)
     

    g_lblIP = Label(g_root, text="IP Address:")
    g_lblIP.grid(column=0, row=0)

    g_txtIP.grid(column=1, row=0)
    g_txtIP.insert(1.0,'xxx.xxx.xxx.xxx')

    btnQuery = Button(g_root, text="Get Status", bg="LightGray", command=Query_Clicked)
    btnQuery.grid(column=0, row=1)

    g_txtFeedback.grid(column=0, row=2, columnspan=3, sticky='NSEW')

    g_root.mainloop()


if __name__ == '__main__':
    main()
