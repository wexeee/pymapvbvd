import re
import numpy as np

def parse_ascconv(buffer):
    #print(buffer)
    vararray = re.finditer(r'(?P<name>\S*)\s*=\s*(?P<value>\S*)\n',buffer)
    #print(vararray)
    mrprot ={}
    for v in vararray:
        try:
            value = float(v.group('value'))
        except ValueError:
            value = v.group('value')
            
        #now split array name and index (if present)
        vvarray = re.finditer(r'(?P<name>\w+)(\[(?P<ix>[0-9]+)\])?',v.group('name'))
        
        currKey = []
        for vv in vvarray:
            #print(vv.group('name'))
            currKey.append(vv.group('name'))
            if vv.group('ix') is not None:
                #print(vv.group('ix'))
                currKey.append(vv.group('ix'))
        
        mrprot.update({tuple(currKey):value})
        
    return mrprot

def parse_xprot(buffer):
    xprot = {}
    tokens = re.finditer(r'<Param(?:Bool|Long|String)\."(\w+)">\s*{([^}]*)',buffer)
    
    for t in tokens:
        #print(t.group(1))
        #print(t.group(2))
        name = t.group(1)
        
        value = re.sub(r'("*)|( *<\w*> *[^\n]*)','',t.group(2))
        value.strip()
        value = re.sub(r'\s*',' ',value)

        try:
            value = float(value)
        except ValueError:
            pass
        
        xprot.update({name : value})
        
    return xprot

def parse_buffer(buffer):
    reASCCONV = re.compile(r'### ASCCONV BEGIN[^\n]*\n(.*)\s### ASCCONV END ###',re.DOTALL)
    #print(f'buffer = {buffer[0:10]}')
    #import pdb; pdb.set_trace()
    
    ascconv = reASCCONV.search(buffer)
    #print(f'ascconv = {ascconv}')
    if ascconv is not None:
        prot =  parse_ascconv(ascconv.group(0)) 
    else:
        prot = {}
        
    
    xprot = reASCCONV.split(buffer)
    #print(f'xprot = {xprot[0][0:10]}')
    if xprot is not None:
        xprot = ''.join([found for found in xprot])
        prot2 = parse_xprot(xprot)
        
        prot.update(prot2)
        
    return prot
    
def read_twix_hdr(fid):
    #function to read raw data header information from siemens MRI scanners 
    #(currently VB and VD software versions are supported and tested).
    
    nbuffers = np.fromfile(fid, dtype=np.uint32, count=1)
    
    prot = {}
    for _ in range(nbuffers[0]):
        tmpBuff = np.fromfile(fid, dtype=np.uint8, count=10)
        bufname = ''.join([chr(item) for item in tmpBuff])
        bufname = re.match(r'^\w*', bufname).group(0)
        
        fid.seek(len(bufname)-9,1)
        buflen = np.fromfile(fid, dtype=np.uint32, count=1)
        tmpBuff = np.fromfile(fid, dtype=np.uint8, count=buflen[0])
        buffer = ''.join([chr(item) for item in tmpBuff])
        buffer = re.sub(r'\n\s*\n', '', buffer)
        
        prot.update({bufname:parse_buffer(buffer)})
        
    return prot