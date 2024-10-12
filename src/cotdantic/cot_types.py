from dataclasses import dataclass, field

# TODO: pick up from line 134 cottypes.xml


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

			elif self._name:
				child._chain = self._chain + [self._name]

			return child

	def __str__(self):
		return '.'.join([*self._chain, self._name])


@dataclass
class basic_type(cot_type):
	pass


@dataclass
class command(cot_type):
	corps = basic_type('C')
	theater = basic_type('T')


@dataclass
class administrative(cot_type):
	corps = basic_type('C')
	finance = command('F')


@dataclass
class size_type(cot_type):
	recovery = basic_type('R')


@dataclass
class size(cot_type):
	light = size_type('L')
	medium = size_type('M')
	heavy = size_type('H')


@dataclass
class recon(cot_type):
	aew = basic_type('W')
	photo = basic_type('X')
	esm = basic_type('Z')


@dataclass
class patrol(cot_type):
	mine_coutermeasures = basic_type('M')
	asuw = basic_type('N')


@dataclass
class flight_status(cot_type):
	drone = basic_type('Q')
	gunship = basic_type('g')
	attack = basic_type('A')
	bomber = basic_type('B')
	transport = size('C')
	c2 = basic_type('D')
	fighter = basic_type('F')
	interceptor = basic_type('I')
	csar = basic_type('H')
	jammer = basic_type('J')
	tanker = basic_type('K')
	vstol = basic_type('L')
	sof = basic_type('M')
	medevac = basic_type('O')
	patrol = patrol('P')
	recon = recon('R')
	asw = basic_type('S')
	trainer = basic_type('T')
	utility = size('U')
	c3i = basic_type('Y')


@dataclass
class flight_type(cot_type):
	fixed = flight_status('F')
	rotary = flight_status('H')
	blimp = basic_type('L')


@dataclass
class sam(cot_type):
	fixed_site = basic_type('f')
	manpad = basic_type('i')
	mobile = basic_type('m')


@dataclass
class missile_target(cot_type):
	air = basic_type('A')
	surface = basic_type('S')


@dataclass
class missile_launch(cot_type):
	air = missile_target('A')
	surface = sam('S')
	attack = basic_type('L')
	subsurface = basic_type('U')


@dataclass
class weapon(cot_type):
	decoy = basic_type('D')
	missile = missile_launch('M')


@dataclass
class sensor(cot_type):
	emplaced = basic_type('E')
	radar = basic_type('R')


@dataclass
class equipment(cot_type):
	sensor = sensor('S')


@dataclass
class acp(cot_type):
	recovery = basic_type('R')


@dataclass
class engineer(cot_type):
	mine_clearing = basic_type('A')


@dataclass
class vehicle_armored(cot_type):
	gun = basic_type('')
	apc = acp('A')
	infantry = basic_type('I')
	light = basic_type('L')
	service = basic_type('S')
	tank = size('T')
	civilian = basic_type('C')
	engineer = basic_type('E')


@dataclass
class vehicle_type(cot_type):
	armored = vehicle_armored('A')


@dataclass
class status(cot_type):
	areas = basic_type('A')
	bearing = basic_type('B')
	boundary = basic_type('T')
	civilian = flight_type('C')
	equipment = equipment('E')
	installation = basic_type('I')
	lines = BaseException('L')
	military = basic_type('M')
	nbm = basic_type('N')
	points = basic_type('P')
	units = basic_type('U')
	admin = administrative('A')
	weapon = weapon('W')


@dataclass
class dimension(cot_type):
	present = status('P')
	anticipated = status('A')
	hq_present = status('H')
	hq_planned = status('Q')
	support = status('S')
	none = status('')


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


@dataclass
class cot_types(cot_type):
	_name: str = None
	atom = atom()
	bit = bit()


COT_TYPES = cot_types()
