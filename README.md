redis-faina
===========

A query analyzer that parses Redis' MONITOR command for counter/timing stats about query patterns

At its core, redis-faina uses the Redis MONITOR command, which echoes every single command (with arguments) sent to a Redis instance. It parses these
entries, and aggregates stats on the most commonly-hit keys, and the most common key prefixes
as well.

Usage is simple:

    # reading from stdin
    redis-cli -p 6490 MONITOR | head -n <NUMBER OF LINES TO ANALYZE> | ./redis-faina.py [options]

    # reading a file
    redis-cli -p 6490 MONITOR | head -n <...> > /tmp/outfile.txt
    ./redis-faina.py [options] /tmp/outfile.txt
    
 		options:
  	--redis-version=...       			  Version of the redis server being monitored, if not provided `2.6` is the default. e.g. --redis-version=2.4


The output (anonymized below with 'zzz's) looks as follows:

<pre>
Overall Stats
========================================
Lines Processed     117773

Top Keys
========================================
friendlist:zzz:1:2     534
followingcount:zzz     227
friendlist:zxz:1:2     167
friendlist:xzz:1:2     165
friendlist:yzz:1:2     160
friendlist:gzz:1:2     160
friendlist:zdz:1:2     160
friendlist:zpz:1:2     156

Top Commands
========================================
SISMEMBER   59545
HGET        27681
HINCRBY     9413
SMEMBERS    9254
MULTI       3520
EXEC        3520
LPUSH       1620
EXPIRE      1598
</pre>
