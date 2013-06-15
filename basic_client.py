import TwistedCommentStream
from twisted.internet import reactor

class consumer(TwistedCommentStream.CommentReceiver):
    def connectionMade(self):
        print "connected to stream..."

    def connectionLost(self, why):
        print 'connection lost:', why
    
    def connectionFailed(self, why):
        print "connection failed:", why
        reactor.stop()

    def commentReceived(self, comment):
        if comment.has_key('subreddit'):
            print "[%s] %s: %s" % (comment['subreddit'], comment['author'], comment['body'])

if __name__ == "__main__":
    TwistedCommentStream.comments(consumer())
    reactor.run()