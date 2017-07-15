import serial
import time
import warnings


com_port = 'com4'


def get_sec(time_str):
    h, m, s = time_str.split(':')
    return float(int(h) * 3600 + int(m) * 60 + int(s))

def get_hms(time_float):
    time_float = int(time_float)
    h = time_float/3600
    m = (time_float-60*h)/60
    s = time_float-3600*h-60*m
    return str(h)+':'+str(m)+':'+str(s)

class ICC(serial.Serial):
    def __init__(self):
        super(ICC,self).__init__()
        self.port = 'com4'
        self.baudrate = 9600
        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE
        self.xonxoff = False
        self.rtscts = False
        self.dsrdtr = False
        self.timeout = 1.
        self.open()
        self.maxchar = 12


    def readline(self):
        Nchar = 0
        MyStr = str()
        while (Nchar < self.maxchar)&(MyStr[-2::]!='\r\n'):
            MyStr+= self.read()
            Nchar+=1
        return MyStr[:-2:]
    
    def __del__(self):
        self.close()
        super(ICC,self).__del__()

    basic_answers = {'*':'the command was executed successfully',
                     '#':'the command was not executed successfully'}

    def check_answer(self,ans,answer_dictionary = basic_answers):
        if ans== '*':
            return answer_dictionary[ans]
        else:
            warnings.warn(answer_dictionary[ans],UserWarning,stacklevel=3)
            return ""

    def DiscrTyp3(self,MyInput):
        number = str(int(MyInput))
        return '0'*(6-len(number))+number

    
    def VolType2(self,MyInput):
        oldstr = "{:4.3e}".format(float(MyInput))
        e_position = oldstr.index("e")
        if oldstr[e_position+2]=='0':
            newstr = oldstr[:(e_position+2)] + oldstr[(e_position+3):]
        newstr2 = newstr.replace("e", "")
        number = newstr2.replace(".","")
        return number
    

    start_answers = basic_answers
    start_answers.update({'-':'channel setting(s) are not correct or unachievable.'})
    def start_pumping(self,ch):
        self.write(str(ch)+'H\r\n')
        ans = self.read()
        diagnostic = ""
        if ans == '-':
            diagnostic = ICC.get_flow_rate_error(self,ch)
        return ICC.check_answer(self,ans,answer_dictionary = ICC.start_answers)+diagnostic
        

    def stop_pumping(self,ch):
        self.write(str(ch)+'I\r\n')
        ans = self.read()
        return ICC.check_answer(self,ans)
    
    dirget_dict = {'J':'clockwise','K':'counter-clockwise'}
    def get_direction(self,ch):
        self.write(str(ch)+'xD\r\n')
        ans = self.readline()
        return 'channel ' + str(ch) +' direction: '+ICC.dirget_dict[ans]

    def get_direction_simple(self,ch):
        self.write(str(ch)+'xD\r\n')
        ans = self.readline()
        return ICC.dirget_dict[ans]

    dirset_dict = {'clockwise':'J','counter-clockwise':'K'}
    def set_direction(self,ch,direction):
         self.write(str(ch)+ICC.dirset_dict[direction]+'\r\n')
         ans = self.read()
         return ICC.check_answer(self,ans)

    getpumpingmode_dict = {'L':'RPM',
                           'M':'Flow Rate',
                           'O':'Volume (at rate)',
                           'G':'Volume (over time)',
                           'Q':'Volume+pause',
                           'N':'Time',
                           'P':'Tme+pause'}
    def get_pumping_mode(self,ch):
        self.write(str(ch)+'xM'+'\r\n')
        ans = self.readline()
        return 'pumping mode channel ' + str(ch) +': ' +ICC.getpumpingmode_dict[ans]

    setpumpingmode_dict = {'RPM':'L',
                           'Flow Rate':'M',
                           'Volume (at rate)':'O',
                           'Volume (over time)':'G',
                           'Volume+pause':'Q',
                           'Time':'N',
                           'Tme+pause':'P'}
    def set_pumping_mode(self,ch,mode):
        self.write(str(ch)+ICC.setpumpingmode_dict[mode]+'\r\n')
        ans = self.read()
        return ICC.check_answer(self,ans)

    def get_pumping_rate_rpm(self,ch):
        self.write(str(ch)+'S'+'\r\n')
        ans = self.readline()
        return 'channel ' + str(ch) +' flow rate: ' + ans+' RPM'

    def set_pumping_rate_rpm(self,ch,rate):
        self.write(str(ch)+'S'+ICC.DiscrTyp3(self,100*rate)+'\r\n')
        ans = self.read()
        return ICC.check_answer(self,ans)

    def get_pumping_rate(self,ch):
        self.write(str(ch)+'f'+'\r\n')
        ans = self.readline()
        return 'channel ' + str(ch) +' flow rate: ' + str(float(ans)/1000)+' mL/min'

    def set_pumping_rate(self,ch,rate):
        self.write(str(ch)+'f'+ICC.VolType2(self,rate)+'\r\n')
        ans = self.readline()
        return str(float(ans)/1000)+' mL/min'

    start_error_dict = {'0': ['The pump has already started',""],
                        'C': ['Cycle count of 0',""],
                        'R': ['Max flow rate exceeded or flow is set to 0, (max flow is ',' mL/min)'],
                        'V': ['Max volume exceeded (max vol is ','mL)']}
    def get_flow_rate_error(self,ch):
        self.write(str(ch)+'xe'+'\r\n')
        ans = self.readline()
        #print(ans)
        t = len(ICC.start_error_dict[ans[0]][1])>0
        return ICC.start_error_dict[ans[0]][0]+t*str(float(ans[1:])/1000)+ICC.start_error_dict[ans[0]][1]

    def reverse_direction(self,ch):
        self.stop_pumping(ch)
        direction = self.get_direction_simple(ch)
        if direction == 'clockwise':
            self.set_direction(ch,'counter-clockwise')
        else:
            self.set_direction(ch,'clockwise')
        time.sleep(0.01)
        self.start_pumping(ch)
    
if __name__ == "__main__":
    with ICC() as icc:
        print(icc.stop_pumping(1))
        time.sleep(0.5)
        print(icc.start_pumping(1))
        time.sleep(0.5)
        print(icc.get_direction(1))
        print(icc.stop_pumping(1))
        print(icc.set_direction(1,'counter-clockwise'))
        print(icc.get_pumping_mode(1))
        print(icc.set_pumping_mode(1,'Flow Rate'))
        print(icc.set_pumping_rate_rpm(1,40))
        time.sleep(0.5)
        print(icc.start_pumping(1))
        time.sleep(0.1)
        print(icc.start_pumping(1))
        print(icc.get_flow_rate_error(1))
        time.sleep(0.5)
        print(icc.get_pumping_rate_rpm(1))
        print(icc.get_pumping_rate(1))
        print(icc.set_pumping_rate(1,0.05))
        print(icc.stop_pumping(1))
