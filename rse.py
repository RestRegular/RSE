import os
import re
import sys
import rcolor as rc
import rseerrors as rtme

replacements = []

holding_contents = []

except_contents = {'\\%': '','\\': '\\\\','.': '\\.', '?': '\\?', '+': '\\+', '*': '\\*', '-': '\\-', '^': '\\^',
                   '$': '\\$', '[': '\\[', ']': '\\]', '{': '\\{', '}': '\\}', '(': '\\(', ')': '\\)', '|': '\\|'}


def getReplacement(match):
    if not hasattr(getReplacement, 'index'):
        getReplacement.index = 0
    index = getReplacement.index
    getReplacement.index += 1
    if index < len(replacements):
        return replacements[index]
    else:
        raise rtme.TargetCountMismatchedError(len(replacements), index)


def compileSpaces(origin: str):
    return re.sub(r'\s+', ' ', origin)


def compileBeginAndEnd(origin: str):
    origin = re.sub(r'\bbegin\b', '^', origin)
    return re.sub(r'\bend\b', '$', origin)


def compileStr(origin: str):
    contents = re.findall(r'\bstr\(([^)]*)\)', origin)
    global holding_contents
    holding_contents = contents
    origin = re.sub(r'\bstr\([^)]*\)', '@', origin)
    return origin


def matchGroupSign(origin_content, begin_sign, left_sign: str, right_sign: str):
    index = 0
    matched_contents = []
    while index < len(origin_content):
        lit = origin_content[index]
        index += 1
        while index < len(origin_content) and lit != begin_sign:
            lit = origin_content[index]
            index += 1
        stack = [left_sign]
        content = ''
        while len(stack) > 0 and index < len(origin_content):
            lit = origin_content[index]
            if lit == begin_sign:
                content = ''
            elif lit == left_sign:
                stack.append(left_sign)
                content += lit
            elif lit == right_sign:
                stack.pop()
                if len(stack) == 0:
                    break
                else:
                    content += lit
            else:
                content += lit
            index += 1
        if index < len(origin_content):
            matched_contents.append(content)
        index += 1
    return matched_contents


def rewriteMatchSign(origin_content, begin_sign, end_sign, left_sign: str, right_sign: str):
    index = 0
    new_content = origin_content
    while index < len(origin_content):
        lit = origin_content[index]
        index += 1
        while index < len(origin_content) and lit != begin_sign:
            lit = origin_content[index]
            index += 1
        stack = [left_sign]
        while len(stack) > 0 and index < len(origin_content):
            lit = origin_content[index]
            if lit == begin_sign:
                stack.append(begin_sign)
            elif lit == left_sign:
                stack.append(left_sign)
            elif lit == right_sign:
                stack.pop()
                if len(stack) == 0:
                    new_content = new_content[0:index] + end_sign + new_content[index + 1: len(new_content)]
                    break
            index += 1
        index += 1
    return new_content


def compileUngroup(origin):
    return newCompileNestedSign(origin, 'ungroup')


def compileGroup(origin):
    return newCompileNestedSign(origin, 'group')


def compileUnRand(origin):
    return newCompileNestedSign(origin, 'unrand')


def compileRand(origin):
    return newCompileNestedSign(origin, 'rand')


def compileExact(origin):
    contents = re.findall(r'\.exact\s*[\[(]\s*\d+\s*,?\s*\d*\s*[])]', origin)
    global replacements
    replacements = []
    for content in contents:
        replacements.append('{' + re.findall(r'\[([^]]+)', content)[0] + '}')
    getReplacement.index = 0
    origin = re.sub(r'\.exact\s*[\[(]\s*\d+\s*,?\s*\d*\s*[])]', getReplacement, origin)
    return origin


def compileReuse(origin):
    global replacements
    contents = re.findall(r'\breuse\s*\{\s*([a-zA-Z]+\w*)\s*}', origin)
    replacements = []
    getReplacement.index = 0
    for content in contents:
        replacements.append(f'(?P={content})')
    origin = re.sub(r'\breuse\s*\{\s*[a-zA-Z]+\w*\s*}', getReplacement, origin)
    contents = re.findall(r'\breuse\s*\{\s*(\d+)\s*}', origin)
    replacements = []
    getReplacement.index = 0
    for number in contents:
        replacements.append(f'\\{number}')
    origin = re.sub(r'\breuse\s*\{\s*\d+\s*}', getReplacement, origin)
    return origin


def getPreInfo(pre: str, origin):
    info = {}
    if pre == 'fpre':
        info['3'] = '(?=@)'
    elif pre == 'unfpre':
        info['3'] = '(?!@)'
    elif pre == 'rpre':
        info['3'] = '(?<=@)'
    elif pre == 'unrpre':
        info['3'] = '(?<!@)'
    origin = re.sub(r'\b' + pre + r'\s*\{', '&', origin)
    contents = matchGroupSign(origin, '&', '{', '}')
    origin = rewriteMatchSign(origin, '&', '%', '{', '}')
    info['4'] = contents
    info['5'] = origin
    return info


def compilePre(origin):
    global replacements
    pres = ['fpre', 'unfpre', 'rpre', 'unrpre']
    for pre in pres:
        info = getPreInfo(pre, origin)
        contents = info['4']
        origin = info['5']
        replacements = []
        getReplacement.index = 0
        for content in contents:
            replacements.append(info['3'].replace('@', content))
        origin = re.sub(r'&[^%]+%', getReplacement, origin)
    return origin


volumes = {'zemo': '*', 'onmo': '+', 'zeon': '?', 'sigl': '.', 'lett': 'a-zA-Z', 'blett': 'A-Z', 'slett': 'a-z',
           'or': '|'}


def compileVolume(origin):
    for key in volumes:
        origin = re.sub(r'\.\s*' + key + r'\b', volumes[key], origin)
    origin = re.sub(r'\bbr\b', r'\\b', origin)
    origin = re.sub(r'\bspace\b', r'\\s', origin)
    origin = re.sub(r'\blenum\b', r'\\w', origin)
    origin = re.sub(r'\bnum\b', r'\\d', origin)
    origin = re.sub(r'\blett\b', r'a-zA-Z', origin)
    origin = re.sub(r'\bblett\b', r'A-Z', origin)
    origin = re.sub(r'\bslett\b', r'a-z', origin)
    origin = re.sub(r'\bsigl\b', r'.', origin)
    origin = re.sub(r'\bor\b', r'|', origin)
    origin = re.sub(r'\bunnum\b', r'\\D', origin)
    origin = re.sub(r'\bunspace\b', r'\\S', origin)
    origin = re.sub(r'\bunlenum\b', r'\\W', origin)
    origin = re.sub(r'\bunbr\b', r'\\B', origin)
    origin = re.sub(r'\bchar\b', r'\\s\\S', origin)
    return origin


def compileRestSpaces(origin):
    return re.sub(r'\s+', '', origin)


def exceptContent(content: str):
    real_content = content
    for c in except_contents:
        real_content = real_content.replace(c, except_contents[c])
    return real_content


def compileRewriteHolder(origin):
    global replacements, holding_contents
    real_contents = []
    for item in holding_contents:
        real_contents.append(exceptContent(item))
    replacements = real_contents
    getReplacement.index = 0
    origin = re.sub(r'@', getReplacement, origin)
    return origin


def removeAnnotation(origin):
    origin = re.sub(r'//\s[^\n]*', '', origin)
    origin = re.sub(r'/:[\s\S]*?:/', '', origin)
    return origin


def sortSigns(origin: str, sign: str, left: str, right: str):
    new_content = ""
    stack = []
    i = 0
    record = []
    while i < len(origin):
        lit = origin[i]
        if lit == sign:
            stack.append(sign)
            new_content += f'{sign}{len(stack)}/'
            record.append(len(stack))
        elif lit == left:
            new_content += lit
            stack.append(left)
        elif lit == right:
            if stack[len(stack) - 1] == sign:
                new_content += f'{right}{len(stack)}/'
                stack.pop()
            else:
                new_content += lit
                stack.pop()
        else:
            new_content += lit
        i += 1
    return new_content, record


def replaceByHand(origin, fsign, sign, re_sign):
    new_content = ''
    i = 0
    while i < len(origin):
        c = origin[i]
        if c != fsign:
            new_content += c
        else:
            while c != sign:
                new_content += c
                i += 1
                c = origin[i]
            new_content += re_sign
        i += 1
    return new_content


def newCompileNestedSign(origin, sign, ):
    global replacements
    if sign == 'group':
        origin = re.sub(r'\bgroup\b', '&', origin)
        origin = replaceByHand(origin, '&', '{', '%')
        sort_origin = sortSigns(origin, '&', '{', '}')
        origin = sort_origin[0]
        sort_origin[1].sort(reverse=True)
        record = sort_origin[1]
        for num in record:
            names = re.findall(r'&' + str(num) + r'/(.*?)%', origin)
            inner_contents = re.findall(r'&' + str(num) + r'/.*?%(.+?)}' + str(num) + r'/', origin)
            replacements = []
            i = 0
            while i < len(inner_contents):
                if names[i] == '':
                    replacements.append(f'({inner_contents[i]})')
                else:
                    replacements.append(f'(?P<{names[i].strip()}>{inner_contents[i]})')
                i += 1
            getReplacement.index = 0
            origin = re.sub(r'&' + str(num) + r'/.+?}' + str(num) + r'/', getReplacement, origin)
    else:
        origin = re.sub(r'\b' + sign + r'\s*\{', '&', origin)
        sort_origin = sortSigns(origin, '&', '{', '}')
        origin = sort_origin[0]
        sort_origin[1].sort(reverse=True)
        record = sort_origin[1]
        for num in record:
            inner_contents = re.findall(r'&' + str(num) + r'/(.+?)}' + str(num) + r'/', origin)
            replacements = []
            for content in inner_contents:
                if sign == 'ungroup':
                    replacements.append(f'(?:{content})')
                if sign == 'rand':
                    replacements.append(f'[{content}]')
                if sign == 'unrand':
                    replacements.append(f'[^{content}]')
            getReplacement.index = 0
            origin = re.sub(r'&' + str(num) + r'/.+?}' + str(num) + r'/', getReplacement, origin)
    return origin


def printGray(content):
    print(rc.colortext(rc.Color.Dark_GRAY, content))


def addRestSpace(msg, num: int):
    return msg + ' ' * (num - len(msg))


def compileRTM(_rtm_code):
    code = removeAnnotation(_rtm_code)
    code = compileStr(code)
    code = compileSpaces(code)
    num = len(code) + 8

    def getCompileProcessLog(_type:str | None, msg: str):
        if _type is None:
            if (num + 9) <= 137:
                log = str(msg) + '-' * (num + 9)
            else:
                log = str(msg) + '-' * 137 + '...'
        else:
            log = ' ' * 4 + addRestSpace(_type, 12) + '-    ' + str(msg)
            if len(log) > 153:
                log = log[0:153] + '...'
        return str(log)

    printGray(getCompileProcessLog(None, 'start to compile'))
    printGray(getCompileProcessLog('str', code))
    printGray(getCompileProcessLog('spaces', code))
    code = compileBeginAndEnd(code)
    printGray(getCompileProcessLog('begin&end', code))
    code = compileUngroup(code)
    printGray(getCompileProcessLog('ungroup', code))
    code = compileGroup(code)
    printGray(getCompileProcessLog('group', code))
    code = compileReuse(code)
    printGray(getCompileProcessLog('reuse', code))
    code = compilePre(code)
    printGray(getCompileProcessLog('pre', code))
    code = compileUnRand(code)
    printGray(getCompileProcessLog('unrand', code))
    code = compileRand(code)
    printGray(getCompileProcessLog('rand', code))
    code = compileExact(code)
    printGray(getCompileProcessLog('exact', code))
    code = compileVolume(code)
    printGray(getCompileProcessLog('volume', code))
    code = compileRestSpaces(code)
    printGray(getCompileProcessLog('rest-spaces', code))
    code = compileRewriteHolder(code)
    printGray(getCompileProcessLog('holder', code))
    printGray(getCompileProcessLog(None, 'compile finished'))
    return code


def compileRTM_noPrint(_rtm_code):
    code = removeAnnotation(_rtm_code)
    code = compileStr(code)
    code = compileSpaces(code)
    code = compileBeginAndEnd(code)
    code = compileUngroup(code)
    code = compileGroup(code)
    code = compileReuse(code)
    code = compilePre(code)
    code = compileUnRand(code)
    code = compileRand(code)
    code = compileExact(code)
    code = compileVolume(code)
    code = compileRestSpaces(code)
    code = compileRewriteHolder(code)
    return code


def analyzeInstruction(instruction: str):
    instruction = re.split(r'\s+', instruction)
    for item in instruction:
        if item != '@' and item not in instruction_library:
            raise rtme.InstructionNotFoundError(item)


def preprocessInstruction(instruction):
    tidy_instructions = re.sub(r'("[^"]+")', '@', instruction)
    instruction = re.findall(r'("[^"]+")', instruction)
    return {'1': tidy_instructions, '2': instruction}


def preprocessParam(param: str):
    if param[0] == '"' and param[len(param) - 1] == '"':
        return param[1:len(param) - 1]
    else:
        raise rtme.InvalidFilePathError(param)


instruction_library = ['-help', '-?', 'RSE', '-comp', '-p', '-t', '-rse', '-re', '-exe', '-cls', '-e', '-exit']

help_msg = """--------------------------------------------------------------------------------------------------
introduction: element with * have no symbol
-...        =>        instruction
<...>       =>      * parameter
(...)       =>      * necessary parameter
.. | ..     =>        one or the other parameter 

-comp -p (<RSE file path>)                  compile RSE file content to Regular Expression

-exe -rse (<RSE file path>  (-t <single line initial text> | -p <initial text file path>))
                                            match the initial text with the patten defined by RSE

-exe -re (<regular expression> (-t <single line initial text> | -p <initial text file path>))
                                            match the initial text with the patten defined by RE

-cls                                        clear final shell

-e | -exit                                  exit the RSE instruction environment
--------------------------------------------------------------------------------------------------"""


def outputResult(result):
    index = 1
    for item in result:
        print(rc.colortext(rc.Color.Dark_GRAY,' ' * 7 + addRestSpace(str(index), 9) + '-    ' + str(item)))
        index += 1
    print(rc.colortext(rc.Color.GREEN, ' ' * 4 + addRestSpace('[result]', 12) + '>    ' + str(result)))


def inLineInstruction(instruction: list):
    try:
        instruction = instruction[1:len(instruction)]
        if instruction[0] == '-exit' or instruction[0] == '-e':
            return
        elif instruction[0] == '-?' or instruction[0] == '-help' or instruction[0] == 'RSE':
            print(help_msg)
        elif instruction[0] == '-cls':
            os.system('cls')
        else:
            if instruction[0] == '-comp':
                if len(instruction) == 3:
                    if instruction[1] == '-p':
                        try:
                            with open(instruction[2], 'r', encoding='utf-8') as rtmFile:
                                _rtm_code = rtmFile.read()
                                code = compileRTM(_rtm_code)
                                print(rc.colortext(rc.Color.GREEN,
                                                   ' ' * 4 + addRestSpace('[result]', 12) + '>    ' + code))
                        except FileNotFoundError:
                            raise rtme.InvalidFilePathError(instruction[2])
                    else:
                        raise rtme.WrongInstructionPartError(instruction[1])
                else:
                    raise rtme.InstructionParamCountMismatchedError(instruction[0], 3, len(instruction))
            elif instruction[0] == '-exe':
                if len(instruction) == 5:
                    if instruction[1] == '-rse':
                        if instruction[3] == '-p':
                            with open(instruction[4], 'r', encoding='utf-8') as textFile:
                                _text_content = textFile.read()
                        elif instruction[3] == '-t':
                            _text_content = instruction[4]
                        else:
                            raise rtme.WrongInstructionPartError(instruction[3])
                        with open(instruction[2], 'r', encoding='utf-8') as rtmFile:
                            _rtm_code = rtmFile.read()
                            code = compileRTM_noPrint(_rtm_code)
                            result = re.findall(code, _text_content, re.MULTILINE)
                            print(rc.colortext(rc.Color.CYAN ,
                                               ' ' * 4 + addRestSpace('[regex]', 12) + '>    ' + code))
                            outputResult(result)
                    elif instruction[1] == '-re':
                        if instruction[3] == '-p':
                            with open(instruction[4], 'r', encoding='utf-8') as textFile:
                                _text_content = textFile.read()
                        elif instruction[3] == '-t':
                            _text_content = instruction[4]
                        else:
                            raise rtme.WrongInstructionPartError(instruction[3])
                        _re_code = instruction[2]
                        result = re.findall(_re_code, _text_content, re.MULTILINE)
                        outputResult(result)
                    else:
                        raise rtme.WrongInstructionPartError(instruction[1])
                else:
                    raise rtme.InstructionParamCountMismatchedError(instruction[0], 5, len(instruction))
            else:
                raise rtme.WrongInstructionPartError(instruction[0])
    except Exception as e:
        print('ERO > ' + rc.colortext(rc.Color.RED, str(e)))


def instructionLine():
    while True:
        try:
            instruction = input('RSE > ').strip()
            tidy_instructions = preprocessInstruction(instruction)
            if instruction == '':
                continue
            if instruction == '-exit' or instruction == '-e':
                break
            analyzeInstruction(tidy_instructions['1'])
            if instruction == '-?' or instruction == '-help' or instruction == 'RSE':
                print(help_msg)
            elif instruction == '-cls':
                os.system('cls')
            else:
                tem_instruction = re.split(r'\s+', tidy_instructions['1'])
                instruction = []
                index = 0
                for item in tem_instruction:
                    if item == '@':
                        instruction.append(tidy_instructions['2'][index])
                        index += 1
                    else:
                        instruction.append(item)

                if instruction[0] == '-comp':
                    if len(instruction) == 3:
                        if instruction[1] == '-p':
                            if '"' in instruction[2]:
                                try:
                                    with open(preprocessParam(instruction[2]), 'r', encoding='utf-8') as rtmFile:
                                        _rtm_code = rtmFile.read()
                                        code = compileRTM(_rtm_code)
                                        print(rc.colortext(rc.Color.GREEN,
                                                           ' ' * 4 + addRestSpace('[result]', 12) + '>    '
                                                           + code))
                                except FileNotFoundError:
                                    raise rtme.InvalidFilePathError(instruction[2])
                            else:
                                raise rtme.WrongInstructionPartError(instruction[2])
                        else:
                            raise rtme.WrongInstructionPartError(instruction[1])
                    else:
                        raise rtme.InstructionParamCountMismatchedError(instruction[0], 3, len(instruction))
                elif instruction[0] == '-exe':
                    if len(instruction) == 5:
                        if instruction[1] == '-rse':
                            if '"' in instruction[2] and '"' in instruction[4]:
                                if instruction[3] == '-p':
                                    with open(preprocessParam(instruction[4]), 'r', encoding='utf-8') as textFile:
                                        _text_content = textFile.read()
                                elif instruction[3] == '-t':
                                    _text_content = preprocessParam(instruction[4])
                                else:
                                    raise rtme.WrongInstructionPartError(instruction[3])
                                with open(preprocessParam(instruction[2]), 'r', encoding='utf-8') as rtmFile:
                                    _rtm_code = rtmFile.read()
                                    code = compileRTM_noPrint(_rtm_code)
                                    print(rc.colortext(rc.Color.CYAN,' ' * 4 + addRestSpace('[regex]', 12) +
                                                       '>    ' + code))
                                    result = re.findall(code, _text_content, re.MULTILINE)
                                    outputResult(result)
                            else:
                                def getErrorInfo():
                                    if '"' in instruction[2]:
                                        return instruction[2]
                                    else:
                                        return instruction[4]

                                raise rtme.WrongInstructionPartError(getErrorInfo())
                        elif instruction[1] == '-re':
                            if '"' in instruction[2] and '"' in instruction[4]:
                                if instruction[3] == '-p':
                                    with open(preprocessParam(instruction[4]), 'r', encoding='utf-8') as textFile:
                                        _text_content = textFile.read()
                                elif instruction[3] == '-t':
                                    _text_content = preprocessParam(instruction[4])
                                else:
                                    raise rtme.WrongInstructionPartError(instruction[3])
                                _re_code = preprocessParam(instruction[2])
                                result = re.findall(_re_code, _text_content, re.MULTILINE)
                                outputResult(result)
                            else:
                                def getErrorInfo():
                                    if '"' in instruction[2]:
                                        return instruction[2]
                                    else:
                                        return instruction[4]

                                raise rtme.WrongInstructionPartError(getErrorInfo())
                        else:
                            raise rtme.WrongInstructionPartError(instruction[1])
                    else:
                        raise rtme.InstructionParamCountMismatchedError(instruction[0], 5, len(instruction))
                else:
                    raise rtme.WrongInstructionPartError(instruction[0])
        except Exception as e:
            print('ERO > ' + rc.colortext(rc.Color.RED, str(e)))


def main(args):
    try:
        instruction = args
        if len(instruction) == 1:
            print("""Welcome use RSE. Version: 1.0.0
type '-help', '-?', 'RSE' for help""")
            instructionLine()
            print('RSE > '+rc.colortext(rc.Color.RED,'exit RSE'))
        else:
            if len(instruction) == 2:
                if instruction[1] == '-envi':
                    print("""Welcome use RSE. Version: 1.0.0
type '-help', '-?', 'RSE' for help""")
                    instructionLine()
                    print('RSE > '+rc.colortext(rc.Color.RED,'exit RSE'))
                else:
                    print(f'RSE > -comp -p "{instruction[1]}"')
                    inLineInstruction([instruction[0], '-comp', '-p', instruction[1]])
                    os.system('pause')
            else:
                inLineInstruction(instruction)
    except KeyboardInterrupt:
        print(rc.colortext(rc.Color.RED,'exit RSE'))


if __name__ == '__main__':
    main(sys.argv)
