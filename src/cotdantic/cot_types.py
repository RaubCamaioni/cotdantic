from dataclasses import dataclass, field


@dataclass
class cot_type:
	_name: str
	_chain: list = field(default_factory=lambda: [])

	def __getattribute__(self, attr):
		if attr == '_name':
			return super().__getattribute__(attr)

		elif attr == '_chain':
			return super().__getattribute__(attr)

		else:
			child = super().__getattribute__(attr)

			if self._name is None:
				child._chain = []

			else:
				child._chain = self._chain + [self._name]

			return child

	def __str__(self):
		return '.'.join([*self._chain, self._name])


@dataclass
class basic_type(cot_type):
	pass


@dataclass
class status(cot_type):
	areas = basic_type('A')
	bearing = basic_type('B')
	boundary = basic_type('T')
	civilian = basic_type('C')
	equipment = basic_type('E')
	installation = basic_type('I')
	lines = BaseException('L')
	military = basic_type('M')
	nbm = basic_type('N')
	points = basic_type('P')
	units = basic_type('U')


@dataclass
class dimension(cot_type):
	present = status('P')
	anticipated = status('A')
	hq_present = status('H')
	hq_planned = status('Q')


@dataclass
class affiliation(cot_type):
	space = dimension('O')
	air = dimension('A')
	ground = dimension('G')
	surface = dimension('S')
	subsurface = dimension('U')
	other = dimension('X')


@dataclass
class atom(cot_type):
	_name: str = 'a'
	pending = affiliation('p')
	unknown = affiliation('u')
	assumedfriend = affiliation('a')
	friend = affiliation('f')
	neutral = affiliation('n')
	suspect = affiliation('s')
	hostile = affiliation('h')
	joker = affiliation('j')
	faker = affiliation('k')
	nonspecified = affiliation('o')
	other = affiliation('x')


@dataclass
class bit(cot_type):
	_name: str = 'b'
	pass


@dataclass
class cot_types(cot_type):
	_name: str = None
	atom = atom()
	bit = bit()


COT_TYPES = cot_types()
