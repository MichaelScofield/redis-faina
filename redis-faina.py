#! /usr/bin/env python
# coding=utf-8
import argparse
import sys
from collections import defaultdict
import re
import socket

line_re_26 = re.compile(r"""
    ^(?P<timestamp>[\d\.]+)\s\[(?P<db>\d+)\s(?P<ip>\d+\.\d+\.\d+\.\d+):(?P<port>\d+)]\s"(?P<command>\w+)"(\s"(?P<key>[^(?<!\\)"]+)(?<!\\)")?(\s(?P<args>.+))?$
    """, re.VERBOSE)

# For Redisproxy.
line_re_99 = re.compile(r"""
    ^(?P<timestamp>[\d\.]+)\s\[/(?P<ip>\d+\.\d+\.\d+\.\d+):\d+]\s"(?P<command>\w+)"(\s"(?P<key>[^(?<!\\)"]+)(?<!\\)")?(\s(?P<args>.+))?$
    """, re.VERBOSE)


class StatCounter(object):
    def __init__(self, redis_version=2.6, with_port=False, ignored_commands=""):
        self.line_count = 0
        self.skipped_lines = 0
        self.commands = defaultdict(int)
        self.keys = defaultdict(int)
        self._cached_sorts = {}
        self.redis_version = redis_version
        self.line_re = line_re_26 if self.redis_version == 2.6 else line_re_99
        self.with_port = with_port
        self.ignored_commands = frozenset([x.strip().upper() for x in ignored_commands.split(',')])

    def _record_command(self, entry):
        self.commands[entry['command']] += 1

    def _record_key(self, key, ip, port):
        formatted_key = re.sub('\d{4,}', '#', key)
        try:
            (host, _, _) = socket.gethostbyaddr(ip)
            formatted_key = formatted_key + "@" + host
        except socket.herror:
            formatted_key = formatted_key + "@" + ip
        if self.with_port:
            formatted_key = formatted_key + ":" + port
        self.keys[formatted_key] += 1

    @staticmethod
    def _reformat_entry(entry):
        max_args_to_show = 5
        output = '"%(command)s"' % entry
        if entry['key']:
            output += ' "%(key)s"' % entry
        if entry['args']:
            arg_parts = entry['args'].split(' ')
            ellipses = ' ...' if len(arg_parts) > max_args_to_show else ''
            output += ' %s%s' % (' '.join(arg_parts[0:max_args_to_show]), ellipses)
        return output

    def _get_or_sort_list(self, ls):
        key = id(ls)
        if not key in self._cached_sorts:
            sorted_items = sorted(ls)
            self._cached_sorts[key] = sorted_items
        return self._cached_sorts[key]

    def _general_stats(self):
        return [("Lines Processed", self.line_count)]

    def process_entry(self, entry):
        if entry['command'] not in self.ignored_commands:
            self._record_command(entry)
            if entry['key']:
                self._record_key(entry['key'], entry['ip'], entry['port'])

    def _top_n(self, stat):
        sorted_items = sorted(stat.iteritems(), key=lambda x: x[1], reverse=True)
        return sorted_items[:]

    def _pretty_print(self, result, title, percentages=False):
        print title
        print '=' * 40
        if not result:
            print 'n/a\n'
            return

        max_key_len = max((len(x[0]) for x in result))
        max_val_len = max((len(str(x[1])) for x in result))
        for key, val in result:
            key_padding = max(max_key_len - len(key), 0) * ' '
            if percentages:
                val_padding = max(max_val_len - len(str(val)), 0) * ' '
                val = '%s%s\t(%.2f%%)' % (val, val_padding, (float(val) / self.line_count) * 100)
            print key, key_padding, '\t', val
        print

    def print_stats(self):
        self._pretty_print(self._general_stats(), 'Overall Stats')
        self._pretty_print(self._top_n(self.keys), 'Top Keys', percentages=True)
        self._pretty_print(self._top_n(self.commands), 'Top Commands', percentages=True)

    def process_input(self, input):
        for line in input:
            self.line_count += 1
            line = line.strip()
            match = self.line_re.match(line)
            if not match:
                if line != "OK":
                    self.skipped_lines += 1
                continue
            self.process_entry(match.groupdict())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input',
        type=argparse.FileType('r'),
        default=sys.stdin,
        nargs='?',
        help="File to parse; will read from stdin otherwise")
    parser.add_argument(
        '--redis-version',
        type=float,
        default=2.6,
        help="Version of the redis server being monitored",
        required=False)
    parser.add_argument(
        '--with-port',
        type=bool,
        default=False,
        help="Aggregate keys by host and port, or solely by host.",
        required=False)
    parser.add_argument(
        '--ignored-commands',
        default="",
        help="不统计的命令,例如PING,INFO或者SLOWLOG",
        required=False)
    args = parser.parse_args()
    counter = StatCounter(redis_version=args.redis_version,
                          with_port=args.with_port,
                          ignored_commands=args.ignored_commands)
    counter.process_input(args.input)
    counter.print_stats()
