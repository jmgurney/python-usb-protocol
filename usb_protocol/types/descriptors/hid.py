#
# This file is part of usb-protocol.
#
""" Structures describing Communications Device Class descriptors. """

import unittest
from enum import IntEnum, unique

import construct
from   construct  import this, IfThenElse, Default, GreedyRange
from   construct  import Probe

from .. import LanguageIDs
from ..descriptor import \
    DescriptorField, DescriptorNumber, DescriptorFormat, \
    BCDFieldAdapter, DescriptorLength

__all__ = [
	'HIDPrefix',
	'HIDDescriptor',
	'ReportDescriptor',
	'ReportDescriptorItem',
	'ItemFlags',
]

@unique
class HIDPrefix(IntEnum):
    # Main items
    INPUT          = 0b1000_00
    OUTPUT         = 0b1001_00
    FEATURE        = 0b1011_00
    COLLECTION     = 0b1010_00
    END_COLLECTION = 0b1100_00
    # Global items
    USAGE_PAGE     = 0b0000_01
    LOGICAL_MIN    = 0b0001_01
    LOGICAL_MAX    = 0b0010_01
    PHYSICAL_MIN   = 0b0011_01
    PHYSICAL_MAX   = 0b0100_01
    UNIT_EXPONENT  = 0b0101_01
    UNIT           = 0b0110_01
    REPORT_SIZE    = 0b0111_01
    REPORT_ID      = 0b1000_01
    REPORT_COUNT   = 0b1001_01
    PUSH           = 0b1010_01
    POP            = 0b1011_01
    # Local Items
    USAGE          = 0b0000_10
    USAGE_MIN      = 0b0001_10
    USAGE_MAX      = 0b0010_10
    DESIGNATOR_IDX = 0b0011_10
    DESIGNATOR_MIN = 0b0100_10
    DESIGNATOR_MAX = 0b0101_10
    STRING_IDX     = 0b0111_10
    STRING_MIN     = 0b1000_10
    STRING_MAX     = 0b1001_10
    DELIMITER      = 0b1010_10

HIDDescriptor = DescriptorFormat(
    "bLength"             / construct.Const(0x09, construct.Int8ul),
    "bDescriptorType"     / DescriptorNumber(33),
    "bcdHID"              / DescriptorField("HID Protocol Version", default=1.11),
    "bCountryCode"        / DescriptorField("HID Device Language", default=0),
    "bNumDescriptors"     / DescriptorField("Number of HID Descriptors", default=1),
    "bRepDescriptorType"  / DescriptorField("HID Descriptor Type", default=34),
    "wDescriptorLength"   / DescriptorField("HID Descriptor Length")
    # bDescriptorType and wDescriptorLength repeat bNumDescriptors times
)

# Flags for INPUT/OUTPUT/FEATURE items. Named under one of the following conventions:
# valA_valB: valA when 0, valB when 1
# flag:      Flag disabled when 0, flag enabled when 1
# nFlag:     Flag enabled when 0, flag disabled when 1
ItemFlags2 = construct.BitStruct(
    "reserved6" / construct.Flag,
    "reserved5" / construct.Flag,
    "reserved4" / construct.Flag,
    "reserved3" / construct.Flag,
    "reserved2" / construct.Flag,
    "reserved1" / construct.Flag,
    "reserved0" / construct.Flag,
    "bitfield_bufferedbytes" / construct.Flag,
    "volatile"          / construct.Flag,
    "null"              / construct.Flag,
    "nPreferred"        / construct.Flag,
    "nLinear"           / construct.Flag,
    "wrap"              / construct.Flag,
    "absolute_relative" / construct.Flag,
    "array_variable"    / construct.Flag,
    "data_constant"     / construct.Flag,
)
ItemFlags1 = construct.BitStruct(
    "volatile"          / construct.Flag,
    "null"              / construct.Flag,
    "nPreferred"        / construct.Flag,
    "nLinear"           / construct.Flag,
    "wrap"              / construct.Flag,
    "absolute_relative" / construct.Flag,
    "array_variable"    / construct.Flag,
    "data_constant"     / construct.Flag,
)
_hid_item_flags = dict(enumerate([ construct.Byte[0], ItemFlags1, ItemFlags2, construct.Byte[4] ]))
ItemFlags = construct.Switch(this.bHeader.bSize, _hid_item_flags)

def HasItemFlags(ctx):
	# Cannot use in w/ this inline, known issue.
	v = ctx.bHeader.prefix
	print(type(v))
	if not isinstance(v, HIDPrefix):
		v = v.intvalue
	return v in { HIDPrefix.INPUT, HIDPrefix.OUTPUT, HIDPrefix.FEATURE }

_hid_item_length = [ 0, 1, 2, 4 ]
ReportDescriptorItem = DescriptorFormat(
    "bHeader" / construct.BitStruct(
        # prefix technically consists of a 4 byte tag and a 2 byte type,
        # however, they're all listed together in the HID spec
        "prefix"  / construct.Enum(construct.BitsInteger(6), HIDPrefix),
        "bSize"   / construct.BitsInteger(2),
    ),
    "data"    / IfThenElse(HasItemFlags, ItemFlags, construct.Byte[lambda ctx: _hid_item_length[ctx.bHeader.bSize]]),
)
ReportDescriptor = GreedyRange(ReportDescriptorItem)

import unittest

class TestHIDDescriptor(unittest.TestCase):
	def test_bitstruct(self):
		rditem = ReportDescriptor.parse(b'\x81\x02')

		self.assertEqual(len(rditem), 1)

		ifs = rditem[0].data

		self.assertEqual(ifs.volatile, False)
		self.assertEqual(ifs.null, False)
		self.assertEqual(ifs.nPreferred, False)
		self.assertEqual(ifs.nLinear, False)
		self.assertEqual(ifs.wrap, False)
		self.assertEqual(ifs.absolute_relative, False)
		self.assertEqual(ifs.array_variable, True)
		self.assertEqual(ifs.data_constant, False)

		rditem = ReportDescriptor.parse(b'\x82\x01\x02')

		self.assertEqual(len(rditem), 1)

		ifs = rditem[0].data

		self.assertEqual(ifs.bitfield_bufferedbytes, True)
		self.assertEqual(ifs.volatile, False)
		self.assertEqual(ifs.null, False)
		self.assertEqual(ifs.nPreferred, False)
		self.assertEqual(ifs.nLinear, False)
		self.assertEqual(ifs.wrap, False)
		self.assertEqual(ifs.absolute_relative, False)
		self.assertEqual(ifs.array_variable, True)
		self.assertEqual(ifs.data_constant, False)

		construct.setGlobalPrintFullStrings(True)

		rditem = ReportDescriptor.parse(b'\x95\x08')

		self.assertEqual(len(rditem), 1)

		it = rditem[0]

		self.assertEqual(it.bHeader.prefix.intvalue, HIDPrefix.REPORT_COUNT)
		self.assertEqual(it.data, [8])

	def test_hid_desc(self):
		# sample from USB HID E.4
		hid_descriptor = bytes([
			0x09,
			0x21,
			0x11, 0x01,
			0x00,
			0x01,
			0x22,
			0x3f, 0x00,
		])

		parsed = HIDDescriptor.parse(hid_descriptor)

		self.assertEqual(parsed.bLength, 9)
		self.assertEqual(parsed.bDescriptorType, 0x21)
		self.assertEqual(parsed.bcdHID, 1.11)
		self.assertEqual(parsed.bCountryCode, 0x00)
		self.assertEqual(parsed.bNumDescriptors, 0x01)
		self.assertEqual(parsed.bRepDescriptorType, 0x22)
		self.assertEqual(parsed.wDescriptorLength, 0x3f)

	def test_report_desc(self):
		# sample from USB HID E.6
		report_descriptor = bytes([
			0x05, 0x01,
			0x09, 0x06,
			0xa1, 0x01,
			0x05, 0x07,
			0x19, 0xe0,
			0x29, 0xe7,
			0x15, 0x00,
			0x25, 0x01,
			0x75, 0x01,
			0x95, 0x08,
			0x81, 0x02,
			0x95, 0x01,
			0x75, 0x08,
			0x81, 0x01,
			0x95, 0x05,
			0x75, 0x01,
			0x05, 0x08,
			0x19, 0x01,
			0x29, 0x05,
			0x91, 0x02,
			0x95, 0x01,
			0x75, 0x03,
			0x91, 0x01,
			0x95, 0x06,
			0x75, 0x08,
			0x15, 0x00,
			0x25, 0x65,
			0x05, 0x07,
			0x19, 0x00,
			0x29, 0x65,
			0x81, 0x00,
			0xc0,
		])

		parsed = ReportDescriptor.parse(report_descriptor)

		#print(repr(parsed))

		self.assertEqual(len(parsed), 32)

		self.assertEqual(parsed[0].bHeader.prefix.intvalue, HIDPrefix.USAGE_PAGE)
		self.assertEqual(parsed[5].bHeader.prefix.intvalue, HIDPrefix.USAGE_MAX)
		self.assertEqual(parsed[5].data, [ 231 ])
		self.assertEqual(parsed[9].data, [ 8 ])
		self.assertEqual(parsed[10].bHeader.prefix.intvalue, HIDPrefix.INPUT)
		self.assertEqual(parsed[10].data.data_constant, False)
		self.assertEqual(parsed[10].data.array_variable, True)
		self.assertEqual(parsed[10].data.absolute_relative, False)
		self.assertEqual(parsed[-1].bHeader.prefix.intvalue, HIDPrefix.END_COLLECTION)

		#print(repr(parsed))
