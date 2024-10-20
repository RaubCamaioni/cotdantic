from .multicast import TcpListener
from .cot_types import atom
from typing import Tuple
from .models import *
import uuid


def pli_cot(address: str, port: int, unicast: str) -> Event:
	uid = f'cotdantic-{uuid.getnode()}'
	cot_type = str(atom.friend.ground.unit.combat.infantry)
	point = Point(lat=38.691420, lon=-77.134600)
	contact = Contact(callsign='CotDantic', endpoint=f'{address}:{port}:{unicast}')
	group = Group(name='Cyan', role='Team Member')
	detail = Detail(contact=contact, group=group)
	event = Event(
		uid=uid,
		type=cot_type,
		point=point,
		detail=detail,
	)
	return event


def echo_chat(sender: Event):
	condantic_callsign = 'CotDantic'
	cotdantic_uid = f'cotdantic-{uuid.getnode()}'

	sender_uid = sender.detail.chat.chatgrp.uid0
	message_id = sender.detail.chat.message_id
	uid = f'GeoChat.{cotdantic_uid}.{sender_uid}.{message_id}'

	from_type = str(atom.friend.ground.unit.combat.infantry)
	point = Point(lat=38.691420, lon=-77.134600)
	link = Link(type=from_type, uid=cotdantic_uid, relation='p-p')
	chatgrp = ChatGroup(
		id=cotdantic_uid,
		uid0=cotdantic_uid,
		uid1=sender_uid,
	)
	chat = Chat(
		id=cotdantic_uid,
		chatroom=sender.detail.chat.sender_callsign,
		sender_callsign=condantic_callsign,
		group_owner='false',
		message_id=f'{message_id}',
		chatgrp=chatgrp,
	)
	remarks = Remarks(
		source=condantic_callsign,
		source_id=cotdantic_uid,
		to=sender_uid,
		text=sender.detail.remarks.text,
	)
	detail = Detail(chat=chat, link=link, remarks=remarks)
	event = Event(
		uid=uid,
		how='h-g-i-g-o',
		type='b-t-f',
		point=point,
		detail=detail,
	)
	return event


def ack_message(chat_event: Event) -> Tuple[Event, Event]:
	condantic_callsign = 'CotDantic'
	cotdantic_uid = f'cotdantic-{uuid.getnode()}'
	from_type = str(atom.friend.ground.unit.combat.infantry)

	link = Link(type=from_type, uid=cotdantic_uid, relation='p-p')

	chatgrp = ChatGroup(
		id=cotdantic_uid,
		uid0=cotdantic_uid,
		uid1=chat_event.detail.chat.id,
	)
	chat = Chat(
		id=cotdantic_uid,
		chatroom=chat_event.detail.chat.sender_callsign,
		sender_callsign=condantic_callsign,
		group_owner='false',
		message_id=chat_event.detail.chat.message_id,
		chatgrp=chatgrp,
	)
	detail = Detail(chat=chat, link=link)
	point = Point(lat=38.691420, lon=-77.134600)
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
