import base64
import os
def Read_licence():
    #open the licence file
    try:
        
        with open(os.getcwd() +'/resources/licence.lic','rb') as f:
            lic = f.read()
    except FileNotFoundError:
        return False
    #decode
    lic = base64.b64decode(lic)
    key ='LICENCE-DJFKAL-3.13.2'
    #return content
    content = ''.join([chr(b^ ord(key[i % len(key)])) for i,b in enumerate(lic)])
    
    if content.find('is_pay=True'):
        return True
    return False
    

