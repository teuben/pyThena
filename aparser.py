from re import match

# ^\s*((?:set)\s+)?([^#]+)\s*=([^#]+)(#.*)?#>\s+([^\s]+)(.*=[^\s]*)?(.+)?$
# requires that each line has a #>
def parse_generic(filename, silent=False):
    with open(filename) as file:
        return parse_s(file.readlines(), filename=filename, silent=silent)

def parse_s(lines, filename=None, silent=False):
    #lines = file.readlines()
    recognized = ['.sh', '.csh', '.py', '.athinput'] # recognized filetypes
    data = {} # data from the file
    info = {} # info about the file (if athinput, then from the comment block usually)
    type = None # the type of the file (sh, csh, etc.)
    block = '' # keeps track of the current block (athinput files only)
    
    def sprint(s):
        if not silent:
            print(s)

    # check if filename has an extension
    m = match('^([^\.]+)(..*)?$', filename) if filename else None
    if m:
        ext = m.group(2)
        if m.group(1) == 'athinput': # currently athinput.* is the only prefix file type
            type = 'athinput'
        elif ext in recognized:
            type = ext[1:] # remove the dot
        else:
            sprint('File type not recognized, trying to determine from file content')

    for line in lines:

        # check for block line
        m = match('^\s*<(.+)>.*', line)
        if m:
            block = m.group(1).strip() + '/'
            if not type:
                sprint('File type deduced to be athinput')
                type = 'athinput'
            continue

        # group 1 -> either 'set' or empty; can be used to determine if csh or not
        # group 2 -> variable name
        # group 3 -> variable value
        # group 4 -> either help info or empty
        # group 5 -> GUI type
        # group 6 -> either old csh (repeated) name=value or empty; can be ignored
        # group 7 -> GUI params
        m = match('^\s*(set\s+)?([^#]+)\s*=([^#]+)(#.*)?#>\s+([^\s]+)(.*=[^\s]*)?(.+)?$', line)
        if m:
            
            # attempt to deduce type if not already known
            if not type:
                # if the set keyword is used, then its a csh file
                if m.group(1):
                    sprint('File type deduced to be csh')
                    type = 'csh'
                # else still undetermined
            
            # process data
            help = m.group(4)
            gparams = m.group(7)
            value = m.group(3).strip()
            
            # unwrap value if it is in quotes
            if match('^\'.*\'|\".*\"$', value):
                # for now, assume that quotes => python, otherwise impossible to deduce python code
                if not type:
                    sprint('File type deduced to be python')
                    type = 'python'
                value = value[1:-1]

            # block_name/variable
            data[f'{block}{m.group(2).strip()}'] = {
                'value': value,
                'help': '' if not help else help.strip(),
                'gtype': m.group(5).strip(),
                'gparams': '' if not gparams else gparams.strip()
            }
            continue
 
        # only need to build the info dictionary for athinput files
        if type == 'athinput' and block == 'comment/':
            # this regex matches the name / abstract
            m = match('^([^#]+)\s*=\s*([^#]+).*$', line)
            if m: # probably definitely matches, but just a formality
                info[m.group(1).strip()] = m.group(2).strip()
                continue
    
    # default to sh if a type was not deduced
    if not type:
        sprint('Unable to deduce file type from content, defaulting to sh')
        type = 'sh'

    # for athinput files, info should be empty
    return data, info, type

# parses the athinput file and returns a dictionary
def parse(filename):
    file = open(filename, 'r')
    lines = file.readlines()
    data = {}
    info = {}
    prefix = ''
    # looking for name and abstract
    # assuming name and abstract lines have no comments in them
    for line in lines:
        # this regex matches the section line:
        # <[string]>
        m = match('^\s*<(.+)>.*', line)
        if m:
            prefix = m.group(1).strip()
            continue
        # this regex matches strings of the form:
        # [string] = [string with spaces] # comment
        m = match('^([^#]+)\s*=\s*([^#]+).*', line)
        if m:
            # strip the leading and trailing whitespace
            # dictionary entry is a list
            name = m.group(1).strip()
            if prefix == 'comment':
                info[name] = m.group(2).strip()
            else:
                data[f'{prefix}_{name}'] = m.group(2).strip()
    return data, info

# parse_special is similar but more primitive than parse_generic
# parse but with special formatting
def parse_special(filename):
    file = open(filename, 'r')
    lines = file.readlines()
    data = {}
    info = {}
    prefix = ''
    # looking for name and abstract
    # assuming name and abstract lines have no comments in them
    for line in lines:
        # this regex matches the section line:
        # <[string]>
        m = match('^\s*<(.+)>.*', line)
        if m:
            prefix = m.group(1)
            continue
        # this regex matches strings of the form:
        # [string] = [string with spaces] # comment #> [string] [string]
        m = match('^([^#]+)\s*=\s*([^#]+).*#>\s+([^\s]+)(\s+.+|\s*)$', line)
        if m:
            # strip the leading and trailing whitespace
            # dictionary entry is a list
            data[f'{prefix}_{m.group(1)}'.strip()] = [
                m.group(2).strip(), 
                m.group(3).strip(), 
                m.group(4).strip()
            ]
            continue
        # this regex matches the name / abstract
        m = match('^([^#]+)\s*=\s*([^#]+).*$', line)
        if m:
            info[m.group(1).strip()] = m.group(2).strip()
    return data, info