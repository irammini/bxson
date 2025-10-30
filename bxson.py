# BXSON - Base-X Structured Object Notation (Teaser RUI Edition)
# A JSON-like format supporting b32{}, b58{}, b64{}, and ;; comments.

import ply.lex as lex
import ply.yacc as yacc
import json
import base64 
import sys
import base58 # Required for Base58 decoding

# --- Lexer Definition (Phần Phân tích Từ vựng) ---

states = (
   ('base32', 'exclusive'),
   ('base58', 'exclusive'),
   ('base64', 'exclusive'),
)

tokens = (
    'STRING', 'NUMBER',
    'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET',
    'COLON', 'COMMA',
    'TRUE', 'FALSE', 'NULL',
    'BASE32_OPEN', 'BASE32_DATA',
    'BASE58_OPEN', 'BASE58_DATA',
    'BASE64_OPEN', 'BASE64_DATA',
)

# Base-X OPEN tokens (Trạng thái INITIAL)
def t_BASE32_OPEN(t):
    r'b32\{'
    t.lexer.begin('base32')
    return t

def t_BASE58_OPEN(t):
    r'b58\{'
    t.lexer.begin('base58')
    return t

def t_BASE64_OPEN(t):
    r'b64\{'
    t.lexer.begin('base64')
    return t

# Standard JSON tokens
t_LBRACE    = r'\{'
t_RBRACE    = r'\}'
t_LBRACKET  = r'\['
t_RBRACKET  = r'\]'
t_COLON     = r':'
t_COMMA     = r','
t_TRUE      = r'true'
t_FALSE     = r'false'
t_NULL      = r'null'

def t_STRING(t):
    r'\"([^\\\n]|(\\.))*?\"'
    return t

def t_NUMBER(t):
    r'-?\d+(\.\d+)?([eE][-+]?\d+)?'
    try:
        t.value = float(t.value) if '.' in t.value or 'e' in t.value or 'E' in t.value else int(t.value)
    except ValueError:
        print(f"Invalid number value: {t.value}")
        t.value = 0
    return t

# Teaser RUI Comment (;; comment)
def t_ignore_COMMENT(t):
    r';;.*'
    pass

t_ignore = ' \t'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Lexer Error: Illegal character '{t.value[0]}' at line {t.lexer.lineno}")
    t.lexer.skip(1)

# --- Base-X Data States ---

# Base32
def t_base32_BASE32_DATA(t): r'[^}]+'; t.value = t.value.strip(); return t
def t_base32_RBRACE(t): 
    r'\}'
    t.lexer.begin('INITIAL') 
    return t
def t_base32_error(t): print(f"Lexer Error (b32): Illegal character '{t.value[0]}' at line {t.lexer.lineno}"); t.lexer.skip(1)
t_base32_ignore = ''

# Base58
def t_base58_BASE58_DATA(t): r'[^}]+'; t.value = t.value.strip(); return t
def t_base58_RBRACE(t): 
    r'\}'
    t.lexer.begin('INITIAL') 
    return t
def t_base58_error(t): print(f"Lexer Error (b58): Illegal character '{t.value[0]}' at line {t.lexer.lineno}"); t.lexer.skip(1)
t_base58_ignore = ''

# Base64
def t_base64_BASE64_DATA(t): r'[^}]+'; t.value = t.value.strip(); return t
def t_base64_RBRACE(t): 
    r'\}'
    t.lexer.begin('INITIAL') 
    return t
def t_base64_error(t): print(f"Lexer Error (b64): Illegal character '{t.value[0]}' at line {t.lexer.lineno}"); t.lexer.skip(1)
t_base64_ignore = ''

lexer = lex.lex()

# --- Parser Definition (Phần Phân tích Cú pháp) ---

start = 'document'

def p_document(p):
    '''document : value'''
    p[0] = p[1]

def p_value(p):
    '''value : object
             | array
             | STRING
             | NUMBER
             | TRUE
             | FALSE
             | NULL
             | base32_value
             | base58_value
             | base64_value'''
    if p.slice[1].type == 'STRING':
        try:
            p[0] = json.loads(p[1])
        except json.JSONDecodeError:
            p[0] = p[1]
    elif p.slice[1].type == 'TRUE': p[0] = True
    elif p.slice[1].type == 'FALSE': p[0] = False
    elif p.slice[1].type == 'NULL': p[0] = None
    else: p[0] = p[1]

# Base-X Value Rules (Returns a dict tag for later decoding)
def p_base32_value(p): '''base32_value : BASE32_OPEN BASE32_DATA RBRACE'''; p[0] = {"$bxson_type": "b32", "data": p[2]}
def p_base32_value_empty(p): '''base32_value : BASE32_OPEN RBRACE'''; p[0] = {"$bxson_type": "b32", "data": ""}

def p_base58_value(p): '''base58_value : BASE58_OPEN BASE58_DATA RBRACE'''; p[0] = {"$bxson_type": "b58", "data": p[2]}
def p_base58_value_empty(p): '''base58_value : BASE58_OPEN RBRACE'''; p[0] = {"$bxson_type": "b58", "data": ""}

def p_base64_value(p): '''base64_value : BASE64_OPEN BASE64_DATA RBRACE'''; p[0] = {"$bxson_type": "b64", "data": p[2]}
def p_base64_value_empty(p): '''base64_value : BASE64_OPEN RBRACE'''; p[0] = {"$bxson_type": "b64", "data": ""}

# Standard JSON Rules
def p_object(p):
    '''object : LBRACE members RBRACE'''
    p[0] = dict(p[2])
def p_object_empty(p): '''object : LBRACE RBRACE'''; p[0] = {}

def p_members_1(p):
    '''members : pair'''
    p[0] = [p[1]]
def p_members_2(p):
    '''members : pair COMMA members'''
    p[0] = [p[1]] + p[3]
    
def p_pair(p):
    '''pair : STRING COLON value'''
    try: key = json.loads(p[1])
    except json.JSONDecodeError: key = p[1]
    p[0] = (key, p[3])
    
def p_array(p):
    '''array : LBRACKET elements RBRACKET'''
    p[0] = p[2]
def p_array_empty(p): '''array : LBRACKET RBRACKET'''; p[0] = []

def p_elements_1(p):
    '''elements : value'''
    p[0] = [p[1]]
def p_elements_2(p):
    '''elements : value COMMA elements'''
    p[0] = [p[1]] + p[3]

def p_error(p):
    if p:
        raise SyntaxError(f"Syntax Error at token '{p.type}' (value: '{p.value}') at line {p.lineno}")
    else:
        raise SyntaxError("Syntax Error: Unexpected end of file (EOF)!")

parser = yacc.yacc(debug=False, write_tables=False)

# --- Core API Functions (Chức năng Module chính) ---

def loads(s):
    """Parses a BXSON string (s) into a Python structure."""
    return parser.parse(s, lexer=lexer)

def load(fp):
    """Parses BXSON content from a file-like object (fp)."""
    return loads(fp.read())

def _decode_recursive(data):
    """Recursively traverses the structure and decodes Base-X blocks."""
    if isinstance(data, dict):
        if data.get("$bxson_type") in ["b32", "b58", "b64"]:
            bx_type = data["$bxson_type"]
            bx_data_str = data["data"].strip()
            bx_data = bx_data_str.encode('utf-8')
            
            try:
                if bx_type == "b64":
                    # Giải pháp: Thêm padding thiếu cho Base64
                    padding_needed = (4 - len(bx_data_str) % 4) % 4
                    padded_data = bx_data_str + '=' * padding_needed
                    return base64.b64decode(padded_data.encode('utf-8'))

                elif bx_type == "b32":
                    # Base32: Không cần padding thủ công trong Python 3.x
                    return base64.b32decode(bx_data)
                
                elif bx_type == "b58":
                    # Base58
                    return base58.b58decode(bx_data) 
            except Exception as e:
                # Báo lỗi giải mã rõ ràng hơn
                print(f"Warning: Failed to decode {bx_type} data. Returning raw string. Error: {e}")
                return data["data"]

        return {k: _decode_recursive(v) for k, v in data.items()}
    
    elif isinstance(data, list):
        return [_decode_recursive(item) for item in data]
        
    return data

def decode(data_structure):
    """Decodes all Base-X tagged blocks into bytes objects."""
    return _decode_recursive(data_structure)


# --- Command-Line Interpreter (CLI) (Trình thông dịch) ---

if __name__ == "__main__":
    import pprint
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(f"Usage: python {sys.argv[0]} <filename.bxson> [--decode]")
        sys.exit(1)

    filepath = sys.argv[1]
    should_decode = (len(sys.argv) == 3 and sys.argv[2] == '--decode')

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            bxson_data = load(f)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
    except SyntaxError as e:
        print(f"BXSON Syntax Error in {filepath}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading or parsing file: {e}")
        sys.exit(1)

    print(f"--- BXSON Parsing Successful: {filepath} ---")
    
    if should_decode:
        decoded_result = decode(bxson_data)
        print("\n--- DECODED RESULT (Bytes Objects) ---")
        pprint.pprint(decoded_result)
    else:
        print("\n--- RAW PARSE RESULT (BXSON Tags) ---")
        pprint.pprint(bxson_data)
        print("\nTip: Run with '--decode' to see Base-X data converted to Python bytes.")
