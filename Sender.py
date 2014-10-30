import sys
import getopt

import Checksum
import BasicSender

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False, sackMode=False):
        super(Sender, self).__init__(dest, port, filename, debug)
        if sackMode:
            raise NotImplementedError #remove this line when you implement SACK

    # Main sending loop.
    def start(self):
        window = []
        ack_counts = {}
        seqno = 0
        msg = self.infile.read(1400)
        msg_type = None
        while not msg_type == 'end':
            next_msg = self.infile.read(1400)
            msg_type = 'data'
            if seqno == 0:
                msg_type = 'start'
            elif next_msg == "":
                msg_type = 'end'
            
            #don't create more packets to send if last packet is already in the window
            if len(window) < 5 and not self.last_packet_in_window(window):
                packet = self.make_packet(msg_type, seqno, msg)
                print("Sending packet: " + packet[0:10])
                self.send(packet)
                window.append(packet)
                msg = next_msg
                seqno += 1
                if msg_type != 'end':
                    continue
            #handle ack
            while(True):
                response = self.receive(.5)
                if response:
                    break
                for packet in window:
                    if not sackMode or (sack_array and not self.split_packet(packet)[1] in sack_array):
                        print("Timeout: sending " + packet[0:10])
                        self.send(packet)
            print("sender getting response: " + response + "\n\n\n")
            if not Checksum.validate_checksum(response):
                continue
            response = self.split_packet(response)
            
            if sackMode:
                sack_string = response[1].split(";") # "1;3,4".split(";") gives you ["1", "3,4"]
                ack_num = int(sack_string[0]) # "1;3,4".split(";") gives you ["1", "3,4"]
                sack_array = sack_string[1].split(",") # gives [3, 4]
            else:
                ack_num = int(response[1])

            # fast retransmit
            base = int(self.split_packet(window[0])[1]) # 1st seq no in window
            if not ack_counts.has_key(ack_num):
                ack_counts[ack_num] = 0
            else:
                ack_counts[ack_num] += 1
                if ack_counts[ack_num] == 3:
                    self.send(window[0])
                    ack_counts.remove(ack_num)


            diff = ack_num - int(self.split_packet(window[0])[1])
            if diff > 0: # decide if shift window
                for x in range(0, diff):
                    # window.pop(0)
                    print("Removing: " + window.pop(0)[0:10] + "from window\n\n\n")
            #if we have read everyting from the input file and there is still stuff 
            #in the window, update msg_type from 'end' to 'data' so loop doesn't end
            if msg_type == 'end' and window:
                msg_type = 'data' 
        self.infile.close()

    def last_packet_in_window(self, window):
        if window:
            return self.split_packet(window[-1])[0] == 'end'
        return False
    
    def handle_timeout(self, window):
        pass

    def handle_new_ack(self, ack):
        pass

    def handle_dup_ack(self, ack):
        pass

    def log(self, msg):
        if self.debug:
            print msg


'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
    def usage():
        print "BEARS-TP Sender"
        print "-f FILE | --file=FILE The file to transfer; if empty reads from STDIN"
        print "-p PORT | --port=PORT The destination port, defaults to 33122"
        print "-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost"
        print "-d | --debug Print debug messages"
        print "-h | --help Print this usage message"
        print "-k | --sack Enable selective acknowledgement mode"

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                               "f:p:a:dk", ["file=", "port=", "address=", "debug=", "sack="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = None
    debug = False
    sackMode = False

    for o,a in opts:
        if o in ("-f", "--file="):
            filename = a
        elif o in ("-p", "--port="):
            port = int(a)
        elif o in ("-a", "--address="):
            dest = a
        elif o in ("-d", "--debug="):
            debug = True
        elif o in ("-k", "--sack="):
            sackMode = True

    s = Sender(dest, port, filename, debug, sackMode)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
