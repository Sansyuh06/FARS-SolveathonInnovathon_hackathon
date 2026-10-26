import struct

def build_sfo(entries_dict):
    """
    Builds a PlayStation SFO binary file from a dictionary of key-value pairs.
    Format spec:
    Header (20 bytes):
      magic: '\x00PSF'
      version: 0x00000101
      key_table_offset (uint32)
      data_table_offset (uint32)
      num_entries (uint32)
    Index entries (16 bytes each):
      key_offset (uint16)
      param_fmt (uint16)
      param_len (uint32)
      param_max_len (uint32)
      data_offset (uint32)
    """
    keys = sorted(entries_dict.keys())
    num_entries = len(keys)
    
    # Pre-calculate tables
    key_table = bytearray()
    key_offsets = {}
    for k in keys:
        key_offsets[k] = len(key_table)
        key_table.extend(k.encode('ascii') + b'\x00')
        
    # Align key table to 4 bytes
    while len(key_table) % 4 != 0:
        key_table.append(0)
        
    data_table = bytearray()
    data_offsets = {}
    for k in keys:
        fmt, val, max_len = entries_dict[k]
        data_offsets[k] = len(data_table)
        if fmt == 0x0204: # string
            val_bytes = val.encode('utf-8') + b'\x00'
            if len(val_bytes) > max_len:
                val_bytes = val_bytes[:max_len-1] + b'\x00'
            # Pad to max_len
            padded = val_bytes.ljust(max_len, b'\x00')
            data_table.extend(padded)
        elif fmt == 0x0404: # uint32
            data_table.extend(struct.pack('<I', val))
            
    header_size = 20
    index_table_size = num_entries * 16
    key_table_offset = header_size + index_table_size
    data_table_offset = key_table_offset + len(key_table)
    
    # Build header
    out = bytearray()
    out.extend(b'\x00PSF')
    out.extend(struct.pack('<IIII', 0x00000101, key_table_offset, data_table_offset, num_entries))
    
    # Build index entries
    for k in keys:
        fmt, val, max_len = entries_dict[k]
        k_off = key_offsets[k]
        d_off = data_offsets[k]
        if fmt == 0x0204:
            p_len = len(val.encode('utf-8')) + 1
        else:
            p_len = 4
        out.extend(struct.pack('<HHIII', k_off, fmt, p_len, max_len, d_off))
        
    out.extend(key_table)
    out.extend(data_table)
    return bytes(out)

if __name__ == '__main__':
    sample = {
        'APP_VER': (0x0204, '01.00', 8),
        'ATTRIBUTE': (0x0404, 32768, 4),
        'ATTRIBUTE2': (0x0404, 0, 4),
        'ATTRIBUTE_MINOR': (0x0404, 16, 4),
        'BOOT_FILE': (0x0204, '', 32),
        'CATEGORY': (0x0204, 'gd', 4),
        'CONTENT_ID': (0x0204, '', 48),
        'EBOOT_APP_MEMSIZE': (0x0404, 0, 4),
        'EBOOT_ATTRIBUTE': (0x0404, 0, 4),
        'EBOOT_PHY_MEMSIZE': (0x0404, 0, 4),
        'LAREA_TYPE': (0x0404, 0, 4),
        'NP_COMMUNICATION_ID': (0x0204, '', 16),
        'PARENTAL_LEVEL': (0x0404, 0, 4),
        'PSP2_DISP_VER': (0x0204, '00.000', 8),
        'PSP2_SYSTEM_VER': (0x0404, 0, 4),
        'STITLE': (0x0204, 'FARSverse Pocket', 52),
        'TITLE': (0x0204, 'FARSverse Pocket', 128),
        'TITLE_ID': (0x0204, 'FARS00001', 12),
        'VERSION': (0x0204, '01.00', 8),
    }
    sfo = build_sfo(sample)
    print(f'Built SFO successfully: {len(sfo)} bytes')
    with open(r'd:\fyeshi\project\rohit\vita_port\param.sfo', 'wb') as f:
        f.write(sfo)
