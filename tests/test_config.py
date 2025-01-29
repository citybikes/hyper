from pybikes import BikeShareSystem

from citybikes.hyper.config import Config


class TestConfig:


    defaults = {
        'some': 'defaults',
        'more': 'defaults',
    }

    config = Config(defaults, {
        'tests.test_config::MockInst::foo': {
            'foo': 'values',
        },
        'tests.test_config::MockInst::bar': {
            'bar': 'values',
        },
        'tests.test_config::MockInst::b.*z': {
            'any': 'values',
        },
        'tests.test_config::MockInst::zap': {
            'zap': 'values',
        },
        'tests.test_config::MockInst::z.*': {
            'even_more': 'values',
        },
        'tests.test_config::MockInst::Do.*': {
            'nested': {'foo': 10},
        },
        'tests.test_config::MockInst::.*It': {
            'nested': {'bar': 10},
        },
        'tests.test_config::MockInst::DoIt': {
            'hello': 'world',
            'nested': {'foo': 42},
        },
    })

    class MockInst(BikeShareSystem):
        pass

    def test_not_set_gets_defaults(self):
        foo = self.MockInst('notpresent', {'name': 'NotThere'})
        assert self.config[foo] == self.defaults

    def test_set_gets_defaults_and_match(self):
        foo = self.MockInst('foo', {'name': 'Foo'})
        bar = self.MockInst('bar', {'name': 'Bar'})
        baz = self.MockInst('baz', {'name': 'Baz'})
        assert self.config[foo] == {
            ** self.defaults,
            ** {'foo': 'values'}
        }
        assert self.config[bar] == {
            ** self.defaults,
            ** {'bar': 'values'}
        }
        assert self.config[baz] == {
            ** self.defaults,
            ** {'any': 'values'}
        }

    def test_iteratively_match(self):
        zap = self.MockInst('zap', {'name': 'Zap'})
        assert self.config[zap] == {
            ** self.defaults,
            ** {'zap': 'values', 'even_more': 'values'}
        }

    def test_iteratively_match_nested(self):
        doit = self.MockInst('DoIt', {'name': 'DoIt'})
        assert self.config[doit] == {
            ** self.defaults,
            ** {'hello': 'world', 'nested': {'foo': 42, 'bar': 10}},
        }
