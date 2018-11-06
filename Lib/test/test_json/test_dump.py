from datetime import date, datetime, time, timedelta, timezone
from io import StringIO
from uuid import UUID

from test.test_json import PyTest, CTest
from test.support import bigmemtest, _1G

class TestDump:
    def test_dump(self):
        sio = StringIO()
        self.json.dump({}, sio)
        self.assertEqual(sio.getvalue(), '{}')

    def test_dumps(self):
        self.assertEqual(self.dumps({}), '{}')

    def test_encode_truefalse(self):
        self.assertEqual(self.dumps(
                 {True: False, False: True}, sort_keys=True),
                 '{"false": true, "true": false}')
        self.assertEqual(self.dumps(
                {2: 3.0, 4.0: 5, False: 1, 6: True}, sort_keys=True),
                '{"false": 1, "2": 3.0, "4.0": 5, "6": true}')

    # Issue 16228: Crash on encoding resized list
    def test_encode_mutated(self):
        a = [object()] * 10
        def crasher(obj):
            del a[-1]
        self.assertEqual(self.dumps(a, default=crasher),
                 '[null, null, null, null, null]')

    # Issue 24094
    def test_encode_evil_dict(self):
        class D(dict):
            def keys(self):
                return L

        class X:
            def __hash__(self):
                del L[0]
                return 1337

            def __lt__(self, o):
                return 0

        L = [X() for i in range(1122)]
        d = D()
        d[1337] = "true.dat"
        self.assertEqual(self.dumps(d, sort_keys=True), '{"1337": "true.dat"}')

    def test_encode_jsonformatable_object(self):
        class C:
            def jsonformat(self):
                return 'hi there'

        self.assertEqual(self.dumps({'v': C()}),
                         '{"v": "hi there"}')

    def test_encode_datetime(self):
        then = datetime(2018, 11, 5, 7, 54, 55, 123456)
        self.assertEqual(self.dumps({'then': then}),
                         '{"then": "2018-11-05T07:54:55.123"}')

        then = then.replace(tzinfo=timezone.utc)
        self.assertEqual(self.dumps({'then': then}),
                         '{"then": "2018-11-05T07:54:55.123+00:00"}')

    def test_encode_date(self):
        then = date(2018, 11, 5)
        self.assertEqual(self.dumps({'then': then}), '{"then": "2018-11-05"}')

    def test_encode_time(self):
        then = time(7, 54, 55, 123456)
        self.assertEqual(self.dumps({'then': then}),
                         '{"then": "07:54:55.123456"}')

        then = then.replace(tzinfo=timezone.utc)
        self.assertEqual(self.dumps({'then': then}),
                         '{"then": "07:54:55.123456+00:00"}')

    def test_encode_duration(self):
        self.assertEqual(
            self.dumps({
                'span': timedelta(days=1, hours=23, minutes=59, seconds=59,
                                  microseconds=999999),
            }),
            '{"span": "PT47H59M59.999999S"}')
        self.assertEqual(
            self.dumps({
                'span': timedelta(days=-15, hours=10, microseconds=1234),
            }),
            '{"span": "PT-350H0M0.1234S"}')

    def test_encode_uuid(self):
        uuid = UUID('886313E1-3B8A-5372-9B90-0C9AEE199E5D')
        self.assertEqual(self.dumps({'id': uuid}),
                         '{"id": "886313e1-3b8a-5372-9b90-0c9aee199e5d"}')


class TestPyDump(TestDump, PyTest): pass

class TestCDump(TestDump, CTest):

    # The size requirement here is hopefully over-estimated (actual
    # memory consumption depending on implementation details, and also
    # system memory management, since this may allocate a lot of
    # small objects).

    @bigmemtest(size=_1G, memuse=1)
    def test_large_list(self, size):
        N = int(30 * 1024 * 1024 * (size / _1G))
        l = [1] * N
        encoded = self.dumps(l)
        self.assertEqual(len(encoded), N * 3)
        self.assertEqual(encoded[:1], "[")
        self.assertEqual(encoded[-2:], "1]")
        self.assertEqual(encoded[1:-2], "1, " * (N - 1))
