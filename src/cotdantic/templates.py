from cotdantic.models import *
from . import COTDANTIC_IOD, COTDANTIC_CALLSIGN, atom
from typing import Tuple


def default_marker(
	callsign: str,
	uid: str,
	lat: float,
	lon: float,
):
	point = Point(lat=lat, lon=lon)
	detail = Detail(contact=Contact(callsign=callsign))
	event = Event(type='a-u-G', uid=uid, point=point, detail=detail)
	return event


def default_blue_force(
	uid: str,
	callsign: str,
	group_name: str,
	group_role: str,
	address: str,
	lat: float,
	lon: float,
	type: str = 'a-f-G-U-C-I',
	unicast: str = 'udp',
):
	point = Point(lat=lat, lon=lon)
	contact = Contact(callsign=callsign, endpoint=f'{address}:4242:{unicast}')
	group = Group(name=group_name, role=group_role)
	detail = Detail(contact=contact, group=group)
	event = Event(type=type, uid=uid, point=point, detail=detail)

	return event


def echo_chat(sender: Event):
	sender_uid = sender.detail.chat.chatgrp.uid0
	message_id = sender.detail.chat.message_id
	uid = f'GeoChat.{COTDANTIC_IOD}.{sender_uid}.{message_id}'

	from_type = str(atom.friend.ground.unit.combat.infantry)
	point = Point(lat=0, lon=0)
	link = Link(type=from_type, uid=COTDANTIC_IOD, relation='p-p')
	chatgrp = ChatGroup(
		id=COTDANTIC_IOD,
		uid0=COTDANTIC_IOD,
		uid1=sender_uid,
	)
	chat = Chat(
		id=COTDANTIC_IOD,
		chatroom=sender.detail.chat.sender_callsign,
		sender_callsign=COTDANTIC_CALLSIGN,
		group_owner='false',
		message_id=f'{message_id}',
		chatgrp=chatgrp,
	)
	remarks = Remarks(
		source=COTDANTIC_CALLSIGN,
		source_id=COTDANTIC_IOD,
		to=sender_uid,
		text=sender.detail.remarks.text,
	)
	detail = Detail(chat=chat, link=[link], remarks=remarks)
	event = Event(
		uid=uid,
		how='h-g-i-g-o',
		type='b-t-f',
		point=point,
		detail=detail,
	)
	return event


def ack_message(chat_event: Event) -> Tuple[Event, Event]:
	from_type = str(atom.friend.ground.unit.combat.infantry)

	link = Link(type=from_type, uid=COTDANTIC_IOD, relation='p-p')

	chatgrp = ChatGroup(
		id=COTDANTIC_IOD,
		uid0=COTDANTIC_IOD,
		uid1=chat_event.detail.chat.id,
	)
	chat = Chat(
		id=COTDANTIC_IOD,
		chatroom=chat_event.detail.chat.sender_callsign,
		sender_callsign=COTDANTIC_CALLSIGN,
		group_owner='false',
		message_id=chat_event.detail.chat.message_id,
		chatgrp=chatgrp,
	)
	detail = Detail(chat=chat, link=[link])
	point = Point(lat=0, lon=0)
	event = Event(
		uid=chat_event.detail.chat.message_id,
		how='h-g-i-g-o',
		type='b-t-f-d',
		point=point,
		detail=detail,
	)
	event2 = event.model_copy()
	event2.type = 'b-t-f-r'
	return event, event2
