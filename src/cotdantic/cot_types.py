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

		elif attr == 'gen':
			return super().__getattribute__(attr)

		else:
			child = super().__getattribute__(attr)

			if self._name is None:
				child._chain = []

			elif self._name:
				child._chain = self._chain + [self._name]

			return child

	def __str__(self):
		return '-'.join([*self._chain, self._name])

	def gen(self):
		return str(self)


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
	recoilless = size_type('R')


@dataclass
class recon(cot_type):
	aew = basic_type('W')
	esm = basic_type('Z')
	photo = basic_type('X')


@dataclass
class patrol(cot_type):
	asuw = basic_type('N')
	mine_coutermeasures = basic_type('M')


@dataclass
class fighter_status(cot_type):
	interceptor = basic_type('I')


@dataclass
class tanker_status(cot_type):
	boom_only = basic_type('B')
	drogue_only = basic_type('D')


@dataclass
class flight_status(cot_type):
	# wintak
	c2 = basic_type('D')
	asw = basic_type('S')
	attack = basic_type('A')
	bomber = basic_type('B')
	transport = size('C')
	csar = basic_type('H')
	c3i = basic_type('Y')
	ecm = basic_type('J')
	fighter = fighter_status('F')
	medevac = basic_type('O')
	patrol = patrol('P')
	recon = recon('R')
	sof = basic_type('M')
	tanker = tanker_status('K')
	trainer = basic_type('T')
	utility = size('U')
	vstol = basic_type('L')
	# extras
	gunship = basic_type('g')
	interceptor = basic_type('I')


@dataclass
class drone_status(flight_status):
	""""""


@dataclass
class flight_status_all(flight_status):
	drone = drone_status('Q')


@dataclass
class flight_type(cot_type):
	fixed = flight_status('F')
	rotary = flight_status('H')
	blimp = basic_type('L')


@dataclass
class sam(cot_type):
	ballistic = basic_type('B')
	air = basic_type('S')
	subsurface = basic_type('U')
	surface = basic_type('S')
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
	ballistic = basic_type('B')
	cruise = basic_type('C-M')
	surface = sam('S')
	attack = basic_type('L')
	subsurface = basic_type('U')


@dataclass
class weapon(cot_type):
	bomb = basic_type('B')
	decoy = basic_type('D')
	missile = missile_launch('M')


@dataclass
class sensor(cot_type):
	emplaced = basic_type('E')
	radar = basic_type('R')


@dataclass
class mines(cot_type):
	claymore = basic_type('C')
	less_than_lethal = basic_type('L')


@dataclass
class special(cot_type):
	flame_thrower = basic_type('F')
	land_mines = mines('M')
	laser = basic_type('L')
	ied = basic_type('I')
	nbc = basic_type('N')


@dataclass
class missile_subtype(cot_type):
	telar = basic_type('E')
	tlar = basic_type('R')


@dataclass
class missile_type(cot_type):
	intermediate = missile_subtype('I')
	long = missile_subtype('L')
	short = missile_subtype('S')
	theater = missile_subtype('T')


@dataclass
class missile_launcher(cot_type):
	air_defence = basic_type('A')
	anti_tank = basic_type('T')
	surf_surf = basic_type('S')


@dataclass
class equipment_weapon(cot_type):
	air_defence_gun = size('A')
	anti_tank_gun = size('G')
	anti_tank_rocket_launcher = size('T')
	direct_fire_gun = size('D')
	gernade_launchers = size('Z')
	howitzer = size('H')
	missile_launcher = missile_launcher('M')
	mortar = size('O')
	multiple_rocket_launcher = size('X')
	rifle = basic_type('R')
	single_rocket_launcher = size('S')


@dataclass
class equipment(cot_type):
	sensor = sensor('S')
	special = special('X')
	weapon = equipment_weapon('W')


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
class combat_status(cot_type):
	infantry = basic_type('I')


@dataclass
class unit_status(cot_type):
	combat = combat_status('C')


@dataclass
class status(cot_type):
	# wintak air
	civilian = flight_type('C')
	military = flight_type('M')
	weapon = weapon('W')
	# wintak ground
	equipment = equipment('E')
	installation = basic_type('I')
	unit = unit_status('U')
	# wintak sea
	combatant = basic_type('C')
	noncombatant = basic_type('N')
	nonmilitary = basic_type('X')
	owntrack = basic_type('O')
	convoy = basic_type('G-C')
	navy_task_force = basic_type('G-T')
	navy_task_group = basic_type('G-G')
	navy_task_unit = basic_type('G-U')
	asw_ship = basic_type('S-A')
	picket = basic_type('S-P')
	# wintak space
	crewed_vehicle = basic_type('V')
	satellite = basic_type('S')
	launch_vehicle = basic_type('L')
	station = basic_type('T')
	# wintak sof
	aviation = basic_type('A')
	ground = basic_type('G')
	naval = basic_type('N')
	support = basic_type('B')
	# wintak sub surface
	non_submarine = basic_type('U-N')
	submarine = basic_type('U-S')
	underwater_decoy = basic_type('U-W-D')
	underwater_weapon = basic_type('U-W')


# @dataclass
# class dimension(cot_type):
# 	# wintak
# 	none = status('')
# 	# extras
# 	present = status('P')
# 	anticipated = status('A')
# 	hq_present = status('H')
# 	hq_planned = status('Q')
# 	support = status('S')


@dataclass
class affiliation(cot_type):
	# wintak
	air = status('A')
	ground = status('G')
	sea = status('S')
	space = status('O')
	sof = status('F')
	subsurface = status('U')
	# extras
	other = status('X')


@dataclass
class _atom(cot_type):
	# wintak
	unknown = affiliation('u')
	friend = affiliation('f')
	neutral = affiliation('n')
	hostile = affiliation('h')
	# extras
	assumed_friend = affiliation('a')
	suspect = affiliation('s')
	joker = affiliation('j')
	faker = affiliation('k')
	nonspecified = affiliation('o')
	other = affiliation('x')
	pending = affiliation('p')


atom = _atom('a')
