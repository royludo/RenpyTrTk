# encoding UTF8

import re
import argparse

def compare_2_files(filepath, filepath_out):
    with open(filepath, 'r', encoding='utf8') as f1:
        content1 = f1.readlines()
    with open(filepath_out, 'r', encoding='utf8') as f2:
        content2 = f2.readlines()

    count = 0
    for i, l in enumerate(content1):
        if content1[i] != content2[i]:
            print('----------------')
            print(content1[i], end="")
            print(content2[i], end="")
            count += 1
    print(count)


class TrUnit:
    """
    Represents a translation unit, the whole block of lines which is:
        - 2 lines of header
        - an indented block of potentially several lines
    """
    def __init__(self):
        self.game_line = ""
        self.extracted_file = ""
        self.extracted_line = 0

        self.translate_instruction_line = ""
        self.translate_language = ""
        self.id = ""

        self.sources = list()

        self.comments = list()

        self.translated_line = ""
        self.speaker = None

    def display(self):
        print('From: ', self.extracted_file, self.extracted_line)
        print('Instruction: ', self.translate_language, self.id)
        print('Speaker: ', self.speaker)
        i = 0
        for line in self.sources:
            print('L',i,': ',line)
            i += 1
        print('Translation: ', self.translated_line)

    def to_string(self):
        s = str()
        s += self.game_line + '\n'
        s += self.translate_instruction_line + '\n'
        s += '' + '\n'
        if self.speaker == 'Narrator':
            output_speaker = ""
        else:
            output_speaker = self.speaker+' '
        #for l in self.sources:
        #    s += '    # '+ output_speaker + '"' + l + '"' + '\n'
        # RU only
        s += '    # '+ output_speaker + '"' + self.sources[0] + '"' + '\n'
        for c in self.comments:
            s += '    ## '+ c + '\n'
        s += '    '+ output_speaker + '"' + self.translated_line + '"' + '\n'
        s += '' + '\n'
        return s

    def add_source_line(self, line):
        line = line.lstrip()
        m = re.match('^#\s(.+)$', line)
        m_com = re.match('^##\s(.+)$', line)
        if m:
            content = m.group(1)
            speaker, sentence = self.parse_line(content)
            # check speaker consistency if defined already
            if self.speaker is not None and self.speaker != 'Instruction':
                if speaker != self.speaker and speaker != 'Instruction':
                    raise Exception('Speaker inconsistency: ', self.speaker, line)
            else:
                self.speaker = speaker
            self.sources.append(sentence)
        elif m_com:
            self.comments.append(m_com.group(1))
        else:
            raise Exception('Could not parse source language dialog line: ', line)

    def add_translated_line(self, line):
        line = line.lstrip()
        speaker, sentence = self.parse_line(line)
        # check speaker consistency if defined already
        if self.speaker is None:
            raise Exception('Speaker should be now defined:', line)
        if speaker != self.speaker and speaker != 'Instruction':
            raise Exception('Speaker inconsistency: ', self.speaker, line)
        self.translated_line = sentence


    def parse_line(self, line):
        m = re.match('^((\w+)\s)?"(.+)"$', line)
        if m:
            speaker = m.group(2)
            sentence = m.group(3)
            if speaker is None:
                speaker = 'Narrator'
            elif speaker == 'Narrator': # a character is named Narrator in the game => conflict !!!
                raise Exception('Conflict of name for Narrator. A character named Narrator already exists in thegame.')
        else: # if problem, then probably a renpy instruction and not dialog.
            speaker = 'Instruction'
            sentence = line
        return speaker, sentence

    def process_game_line(self, line):
        self.game_line = line
        m = re.match('^#\s(\S+):(\d+)$', line)
        if m:
            self.extracted_file = m.group(1)
            self.extracted_line = m.group(2)
        else:
            raise Exception('Could not parse file line: ', line)

    def process_translate_line(self, line):
        self.translate_instruction_line = line
        m = re.match('^translate\s(\w+)\s(\w+):$', line)
        if m:
            self.translate_language = m.group(1)
            self.id = m.group(2)
        else:
            raise Exception('Could not parse translate instruction: ', line)

class RenpyTrFile:
    """
    The whole translation file. Just contains a list of all the translation units/blocks.
    """
    def __init__(self, filename):
        self.tr_units = list()
        first_TU = True
        current_TU = None
        with open(filename, 'r', encoding='utf-8-sig') as f:
            for line in f:
                line = line.rstrip()
                if line.startswith('# game'):
                    if not first_TU:
                        self.tr_units.append(current_TU)
                    first_TU = False
                    current_TU = TrUnit()
                    current_TU.process_game_line(line)
                elif line.startswith('translate'):
                    current_TU.process_translate_line(line)
                elif re.match('^\s+#', line):
                    current_TU.add_source_line(line)
                elif re.match('^.*\S+.*$', line):
                    current_TU.add_translated_line(line)
        self.tr_units.append(current_TU)

    def getall_speakers(self):
        speakers = dict()
        for tu in self.tr_units:
            speakers[tu.speaker] = 1
        return list(speakers.keys())


# ------- script start --------- #

parser = argparse.ArgumentParser()
parser.add_argument('-i', dest='input', required=True)
args = parser.parse_args()

renpyfile = RenpyTrFile(args.input)
TrUnit_list = renpyfile.tr_units
total = len(TrUnit_list)

tu_length_total = 0
tu_length_done = 0
tu_count = 0
for tu in TrUnit_list:
    tu_length_total += len(tu.translated_line)
    if len(tu.sources) > 1:
        tu_count += 1
        tu_length_done += len(tu.translated_line)

#with open(filepath_out, 'w', encoding='utf-8') as fout:
#    for tu in TUlist:
#        fout.write(tu.to_string())
#        #print(tu.to_string())


print('Translated items: ', tu_count)
print('Total items: ', total)
print('Progression: ', tu_count/total*100, '%')
print('Translated characters: ', tu_length_done)
print('Total characters: ', tu_length_total)
print('Progression: ',tu_length_done/tu_length_total*100, '%')

