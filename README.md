CommentsPubSub
==============

A 2-for-1
---------

At the center is TwistedCommentStream, which enables the fetching and reading of the [comment stream](http://dev.redditanalytics.com/search/stream/) provided by [RedditAnalytis](redditanalytics.com/).

TwistedCommentStream is capable of reading the full stream, or a single subreddit. It can be used on its own, outside of pubsub_server, like so:

```python
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
    # all comments
    #TwistedCommentStream.comments(consumer())
    # single subreddit
    TwistedCommentStream.subreddit(consumer(), subreddit='funny')
    reactor.run()
```

pubsub_server.py isn't much more complicated, thanks to the Autobahn library. I'm setting up an example website now.
