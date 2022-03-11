import unittest

from contextlib import contextmanager

from ..           import emitter_for_format
from ..descriptor import ComplexDescriptorEmitter
from ...types.descriptors.hid import \
    HIDDescriptor as HIDDescriptorType
from ...types.descriptors.hid import *

ReportDescriptorItemEmitter = emitter_for_format(ReportDescriptorItem)

from ...types.descriptors.hid import _hid_item_length, ItemFlags1, ItemFlags2

class HIDDescriptor(ComplexDescriptorEmitter):
    DESCRIPTOR_FORMAT = HIDDescriptorType

    def add_report_raw(self, report_data):
        """Append raw report item or bytes to HID report

        Arguments:
        report_data -- bytes-like or ReportDescriptor to be appended to
                       the HID report.
        """
        self._reports.append(report_data)

    def add_report_item(self, report_prefix, *report_data):
        """Convenience function to add formatted HID report item

        Arguments:
        report_prefix -- HIDPrefix enum representing report item type
        *report_data  -- Additional bytes-like report item data.
                         Valid lengths are 1, 2, or 4 bytes.
        """
        hid_report = ReportDescriptorItemEmitter()
        report_len = _hid_item_length.index(len(report_data))
        hid_report.bHeader = {
            "prefix": report_prefix,
            "bSize":  report_len
        }
        hid_report.data = report_data
        self._reports.append(hid_report)

    def add_input_item(self, *args, **kwargs):
        """Convenience function to add HID input item with preformatted flags.
           See HID 1.11 section 6.2.2.5 for flag meanings.

           See add_inpout_item for argument names and defaults.
        """

        return self.add_inpout_item(HIDPrefix.INPUT, *args, **kwargs)

    def add_output_item(self, *args, **kwargs):
        """Convenience function to add HID output item with preformatted flags.
           See HID 1.11 section 6.2.2.5 for flag meanings.

           See add_inpout_item for argument names and defaults.
        """

        return self.add_inpout_item(HIDPrefix.OUTPUT, *args, **kwargs)

    def add_inpout_item(self, item,
                  data_constant = False,
                  array_variable = True,
                  absolute_relative = False,
                  wrap = False,
                  linear = False,
                  preferred = True,
                  null = False,
                  volatile = False,
                  bitfield_bufferedbytes = False):

        if bitfield_bufferedbytes:
            itmf = ItemFlags2
        else:
            itmf = ItemFlags1

        item_flags = itmf.build({
            "data_constant": data_constant,
            "array_variable": array_variable,
            "absolute_relative": absolute_relative,
            "wrap": wrap,
            "nLinear": not linear,
            "nPreferred": not preferred,
            "null": null,
            "volatile": volatile,
        })
        self.add_report_item(item, item_flags)

    def __init__(self, parent_descriptor):
        super().__init__()
        # The HID Report Descriptor sits under a different USB Descriptor,
        # we need access to the descriptor root to create this.
        self._parent_descriptor = parent_descriptor
        self._reports = []

    def _pre_emit(self):
        report_descriptor = []
        for report in self._reports:
            if hasattr(report, "emit"):
                report_descriptor.append(report.emit()) 
            else:
                report_descriptor.append(report)
        report_descriptor = b"".join(report_descriptor)
        descriptor_len = len(report_descriptor)
        self.wDescriptorLength = descriptor_len
        self._parent_descriptor.add_descriptor(report_descriptor, descriptor_type=0x22)

from ..descriptors import DeviceDescriptorCollection
import unittest

class TestHIDEmitter(unittest.TestCase):
	def test_hidemitter(self):
		collection = DeviceDescriptorCollection()

		hd = HIDDescriptor(collection)

		hd.add_report_item(HIDPrefix.USAGE_PAGE, 1)
		hd.add_report_item(HIDPrefix.USAGE, 6)
		hd.add_report_item(HIDPrefix.COLLECTION, 1)
		hd.add_report_item(HIDPrefix.USAGE_PAGE, 7)
		hd.add_report_item(HIDPrefix.USAGE_MIN, 224)
		hd.add_report_item(HIDPrefix.USAGE_MAX, 231)
		hd.add_report_item(HIDPrefix.LOGICAL_MIN, 0)
		hd.add_report_item(HIDPrefix.LOGICAL_MAX, 1)
		hd.add_report_item(HIDPrefix.REPORT_SIZE, 1)
		hd.add_report_item(HIDPrefix.REPORT_COUNT, 8)
		hd.add_input_item(data_constant=False, array_variable=True, absolute_relative=False)

		import codecs
		print(repr(codecs.encode(hd.emit(), 'hex')))
