# Common Utilities
global debug

debug = False
#debug = True

def d(txt):
    global debug
    if( debug == True):
        if((txt is not None) or (txt is not 'None')):
            print(txt)

