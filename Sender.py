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
            
            if len(window) < 5:
                packet = self.make_packet(msg_type, seqno, msg)
                self.send(packet)
                window.append(packet)
                msg = next_msg
                seqno += 1
                if msg_type != 'end': #
                    continue
            #handle ack
            response = self.receive(.5)
            #timeout
            if not response: 
                for packet in window:
                    self.send(packet)
                continue 
            response = self.split_packet(response)
            if not Checksum.validate_checksum(response):
                continue
            diff = response[1] - self.split_packet(window[0])[1]
            if diff > 0: # decide if shift window
                for x in range(0, diff):
                    window.pop(0)
                    
        self.infile.close()

    def handle_timeout(self):
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
