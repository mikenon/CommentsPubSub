from autobahn.wamp import exportSub, exportPub, WampServerFactory, \
    WampServerProtocol
from autobahn.websocket import listenWS
from twisted.internet import reactor
from twisted.python import log
import TwistedCommentStream
import json
import sys

SERVER_URL = "ws://localhost:9000"
TOPIC_URL = "http://example.com/pubsub/"
TOPIC_URI = TOPIC_URL + "subreddit#"
META_URI = TOPIC_URL + "meta#"
PubSubConnection = None
ConnectionCount = 0

class CommentStreamClient(TwistedCommentStream.CommentReceiver):
    def connectionMade(self):
        print "connected to stream..."
        PublishMeta(message={'type':'status','connected':True})

    def connectionLost(self, why):
        print 'stream connection lost:', why
        PublishMeta(message={'type':'status','connected':True, 'why':why, 'reconnecting':True})

    def connectionFailed(self, why):
        print "stream connection failed:", why
        PublishMeta(message={'type':'status','connected':True, 'why':why, 'reconnecting':False})
        reactor.stop()

    def commentReceived(self, comment):
        PublishComment(comment=comment)

def PublishComment(comment={}):
    global PubSubConnection
    if PubSubConnection != None:
        PubSubConnection.dispatch(TOPIC_URI + comment['subreddit'].lower(), comment)

def PublishMeta(message={}):
    global PubSubConnection
    if PubSubConnection != None:
        PubSubConnection.dispatch(META_URI + message['type'].lower(), message)

class RedditTopicServiceimage:

    @exportSub("subreddit#", True)
    def subscribe(self, topicUriPrefix, topicUriSuffix):
        print "subscribe to /r/%s" % topicUriSuffix
        return True

    '''
    Not defining a publish handler makes it pretty difficult for clients to publish
    '''
#    @exportPub("subreddit#", True)
#    def publish(self, topicUriPrefix, topicUriSuffix, event):
#        print "client wants to publish to %s\t%s" % (topicUriPrefix, topicUriSuffix)
#        return None
    
class MetaTopicService:
    
    @exportSub("meta#", True)
    def subscribe(self, topicUriPrefix, topicUriSuffix):
        print "subscribe to Meta %s" % topicUriSuffix
        return True
    
    '''
    Not defining a publish handler makes it pretty difficult for clients to publish
    '''
#    @exportPub("meta#", True)
#    def publish(self, topicUriPrefix, topicUriSuffix, event):
#        print "client wants to publish to %s\t%s" % (topicUriPrefix, topicUriSuffix)
#        return None    

class PubSubServerProto(WampServerProtocol):
    
    def onSessionOpen(self):
        global ConnectionCount
        ConnectionCount += 1
        self.topicservice = RedditTopicServiceimage()
        self.registerHandlerForPubSub(self.topicservice, TOPIC_URL)
        self.metaservice = MetaTopicService()
        self.registerHandlerForPubSub(self.metaservice, TOPIC_URL)
        self.publishJoin()
        
    def onClose(self, wasClean, code, reason):
        global ConnectionCount
        ConnectionCount -= 1
        self.publishLeave(reason)
    
    def publishJoin(self):
        ip = self.peerstr.split(':')[0]
        info = {'type':'join', 'count':ConnectionCount}
        print '%s joined. %s total.' % (ip, info['count'])
        PublishMeta(message=info)
        
    def publishLeave(self, reason=''):
        ip = self.peerstr.split(':')[0]
        info = {'type':'leave', 'count':ConnectionCount, 'reason':reason}
        print '%s left. %s total. [%s]' % (ip, info['count'], info['reason'])
        PublishMeta(message=info)
        
class CommentServerFactory(WampServerFactory):

    protocol = PubSubServerProto
    
    def startFactory(self):
        WampServerFactory.startFactory(self)
        global PubSubConnection
        PubSubConnection = self
        reactor.callLater(5, self.connectComment)
    
    def connectComment(self):
        TwistedCommentStream.comments(CommentStreamClient())

if __name__ == '__main__':

    log.startLogging(sys.stdout)
    debug = len(sys.argv) > 1 and sys.argv[1] == 'debug'
    
    if debug:
        factory = CommentServerFactory(SERVER_URL, debug = True, debugCodePaths = True, debugWamp = True)
    else:
        factory = CommentServerFactory(SERVER_URL)

    factory.setProtocolOptions(allowHixie76 = True)

    listenWS(factory)
    
    reactor.run()
