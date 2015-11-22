import xlrd
from process.ArrayParsing import ArrayParsing
from process.ListParsing import ListParsing
from process.TextParsing import TextParsing
from equipment.Equipment import Equipment
from equipment.feature.Interface import Interface


class NetScriptGen(object):

    def __init__(self, excel_workbook, template):
        self.wb = xlrd.open_workbook(excel_workbook)
        self.template = template
        self.workbook = dict()
        self.list_of_equipments = list()
        self.list_of_scripts = list()

    def extract_data(self):
        sheet_names = self.wb.sheet_names()
        for sheet in sheet_names:
            xl_sheet = self.wb.sheet_by_name(sheet)
            if (xl_sheet.cell(0, 0).value == 'Function' and
                    xl_sheet.cell(0, 1).value == 'Variable' and
                    xl_sheet.cell(0, 2).value == 'Value'):
                self.workbook[sheet] = ListParsing(xl_sheet)
            elif xl_sheet.cell(0, 0).value == 'Text':
                self.workbook[sheet] = TextParsing(xl_sheet)
            elif sheet == 'Interfaces':
                self.workbook[sheet] = Interface(xl_sheet)
            else:
                self.workbook[sheet] = ArrayParsing(xl_sheet)

    def is_conform(self):
        sheet_names = self.wb.sheet_names()
        if 'Global' not in sheet_names:
            return "The sheet 'Global' does not exist"

    def get_all_equipment_names(self):
        glob = self.wb.sheet_by_name('Global')
        glob = ArrayParsing(glob)
        return glob.get_all_indexes()

    def get_number_of_equipments(self):
        return len(self.get_all_equipment_names())

    def get_all_equipments(self):
        for hostname in self.workbook['Global'].get_all_indexes():
            equipment = Equipment(hostname, self.template, self.workbook)
            self.list_of_scripts.append(equipment.fill_out_the_template())
            self.list_of_equipments.append(equipment)
        return self.list_of_equipments, self.list_of_equipments


class Integer(object):

    def __init__(self, integer):
        self.integer = integer

    def increment(self):
        self.integer += 1
        return self.integer

    def decrement(self):
        self.integer -= 1
        return self.integer

    def value(self):
        return self.integer
