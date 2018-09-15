parsers = {
    'NONE': none_parser,
    'CUSTOM': custom_parser,
    'ONCE': once_parser,
    'MULTI': multi_parser,
    'MONO': mono_parser,
}

def none_parser(cards):
    '''
    parser for NONE [0] issue mode
    No issuance allowed.
    '''

    return None

def custom_parser():
	pass

def once_parser():
	pass

def multi_parser():
	pass

def mono_parser():
	pass

