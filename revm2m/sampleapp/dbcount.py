import time
from django.db import connection

COUNT = 0
STARTCOUNT = None
TIMER = None
START = None
LEVEL = 0


def d(tag='', show=False, total=False):
    """Usage::

          d('finished initialization')
          <....>
          d('finished ...')

       indented call graph::

          d('>foo')
          ...
          d('<foo')

       the > and < characater cause the intervening output to be indented.

    """
    global COUNT, STARTCOUNT, TIMER, START, LEVEL

    queries = connection.queries
    qlen = len(queries)

    if START is None:
        START = time.time()
        TIMER = START
        STARTCOUNT = qlen
        print()
        print('   when:  DB    time  message')
        print('--------  ----- ----- ----------------------------------------')
        print('%7.3f:  %-5d %.3f %s' % (0, 0, 0, 'start'))

    now = time.time()
    querycount = qlen - COUNT

    if tag.startswith('>'):
        if querycount > 1000:
            # if something massive happened before a new block
            # starts, then print it out verbosely
            show = True

        if LEVEL == 0:
            print()  # empty line between all first level indentation-blocks)
        ftag = '    ' * LEVEL + tag
        LEVEL += 1
    elif tag.startswith(('<', '=')):
        LEVEL -= 1
        ftag = '    ' * LEVEL + tag
    else:
        ftag = '    ' * LEVEL + tag

    if querycount:
        qcountstr = '%-5d' % querycount
    else:
        qcountstr = '     '

    if total or tag.startswith('='):
        qcountstr = '=%-4d' % (qlen - STARTCOUNT)

    if show:
        for query in queries[COUNT:]:
            _format_sql(query['sql'])
            print()

    elapsed = now - TIMER
    elapsedstr = '%.3f' % elapsed if elapsed > 0 else '     '
    elapsedstr += '+' if elapsed > 0.1 else ' '

    print('%7.3f:  %s %s %s' % (now - START, qcountstr, elapsedstr, ftag))

    COUNT = qlen
    TIMER = now

    return querycount


def _format_sql(rawsql):
    "Pull out keywords and indent everything else."
    from pygments import highlight, lexers, formatters
    from pygments_pprint_sql import SqlFilter

    lexer = lexers.MySqlLexer()
    lexer.add_filter(SqlFilter())
    return highlight(rawsql, lexer, formatters.TerminalFormatter())
