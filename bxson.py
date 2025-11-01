# BXSON - Base-X Structured Object Notation (Teaser RUI Edition)
# A JSON-like format supporting b32{}, b58{}, b64{}, and ;; comments.

import ply.lex as lex
import ply.yacc as yacc
import json
import base64 
import sys
import base58 # Required for Base58 decoding
from typing import Any, Dict, List, Union, TextIO

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
            p[0] = json.loads(p[1]) # Gỡ escape-sequences (ví dụ: \n, \t, \uXXXX)
        except json.JSONDecodeError:
            p[0] = p[1] # Giữ nguyên nếu không phải JSON string hợp lệ (dự phòng)
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

# --- API: Loading (Parsing & Decoding) ---

def loads(s: str, *, decode: bool = False) -> Union[Dict, List, Any]:
    """
    Parses a BXSON string (s) into a Python structure.

    Args:
        s (str): The BXSON string to parse.
        decode (bool, optional): If True, automatically decodes Base-X
                                 blocks into bytes. Defaults to False.

    Returns:
        Union[Dict, List, Any]: The parsed Python structure.
    """
    data = parser.parse(s, lexer=lexer)
    if decode:
        return _decode_recursive(data)
    return data

def load(fp: TextIO, *, decode: bool = False) -> Union[Dict, List, Any]:
    """
    Parses BXSON content from a file-like object (fp).

    Args:
        fp (TextIO): The file-like object (e.g., open('f.bxson', 'r')).
        decode (bool, optional): If True, automatically decodes Base-X
                                 blocks into bytes. Defaults to False.

    Returns:
        Union[Dict, List, Any]: The parsed Python structure.
    """
    return loads(fp.read(), decode=decode)

def _decode_recursive(data: Any) -> Any:
    """Recursively traverses the structure and decodes Base-X blocks."""
    if isinstance(data, dict):
        # Kiểm tra xem đây có phải là một tag BXSON không
        if data.get("$bxson_type") in ["b32", "b58", "b64"]:
            bx_type = data["$bxson_type"]
            bx_data_str = data["data"].strip()
            
            try:
                if bx_type == "b64":
                    # UPDATE: Thêm padding thiếu cho Base64
                    padding_needed = (4 - len(bx_data_str) % 4) % 4
                    padded_data = bx_data_str + '=' * padding_needed
                    return base64.b64decode(padded_data.encode('utf-8'))

                elif bx_type == "b32":
                    # UPDATE: Thêm padding thiếu cho Base32
                    padding_needed = (8 - len(bx_data_str) % 8) % 8
                    # Chuỗi Base32 phải là chữ hoa
                    padded_data = bx_data_str.upper() + '=' * padding_needed
                    return base64.b32decode(padded_data.encode('utf-8'))
                
                elif bx_type == "b58":
                    # Base58 (thư viện `base58` tự xử lý)
                    return base58.b58decode(bx_data_str.encode('utf-8'))
            except Exception as e:
                # Báo lỗi giải mã rõ ràng hơn
                print(f"Warning: Failed to decode {bx_type} data ('{bx_data_str[:20]}...'). Returning raw string. Error: {e}")
                return data["data"]

        # Đệ quy cho các giá trị trong dict
        return {k: _decode_recursive(v) for k, v in data.items()}
    
    elif isinstance(data, list):
        # Đệ quy cho các item trong list
        return [_decode_recursive(item) for item in data]
        
    # Trả về các kiểu dữ liệu cơ bản (str, int, float, bool, None)
    return data

def decode(data_structure: Any) -> Any:
    """
    Recursively decodes a pre-parsed BXSON structure,
    converting all Base-X tagged blocks into bytes objects.

    Args:
        data_structure (Any): The Python structure (often from 'load' or 'loads')
                              containing BXSON tags.

    Returns:
        Any: The structure with Base-X tags converted to bytes.
    """
    return _decode_recursive(data_structure)

# --- API: Encoding (Python -> BXSON Tags) ---

def encode(data: Any, *, default_encoding: str = 'b64') -> Any:
    """
    Recursively encodes Python 'bytes' objects into BXSON tagged dictionaries.

    Args:
        data (Any): The Python structure (dict, list, etc.) containing bytes.
        default_encoding (str, optional): The default format ('b64', 'b32', 'b58')
                                          to use when encoding 'bytes'. Defaults to 'b64'.

    Returns:
        Any: A new structure where 'bytes' are replaced with
             {'$bxson_type': ..., 'data': ...} dictionaries.
    """
    if isinstance(data, dict):
        return {k: encode(v, default_encoding=default_encoding) for k, v in data.items()}
    
    if isinstance(data, list):
        return [encode(item, default_encoding=default_encoding) for item in data]

    if isinstance(data, bytes):
        try:
            if default_encoding == 'b64':
                data_str = base64.b64encode(data).decode('utf-8')
            elif default_encoding == 'b32':
                data_str = base64.b32encode(data).decode('utf-8')
            elif default_encoding == 'b58':
                data_str = base58.b58encode(data).decode('utf-8')
            else:
                raise ValueError(f"Unknown default_encoding: {default_encoding}")
            
            # Xóa padding Base64 và Base32 để giữ cú pháp BXSON gọn gàng,
            # vì Decoder đã tự xử lý việc thêm padding
            if default_encoding == 'b64':
                 data_str = data_str.rstrip('=')
            # Base32 nên giữ nguyên chữ hoa và xóa padding
            elif default_encoding == 'b32':
                 data_str = data_str.upper().rstrip('=')

            return {"$bxson_type": default_encoding, "data": data_str}
        except Exception as e:
            print(f"Warning: Failed to encode bytes to {default_encoding}. Error: {e}")
            return None # Hoặc trả về một giá trị lỗi

    return data

# --- API: Dumping (Tagged Structure -> BXSON String) ---

def _dumps_recursive(data: Any, indent_level: int, indent_str: Union[str, None]) -> str:
    """Internal recursive function to format the BXSON string."""
    
    current_indent = ""
    next_indent = ""
    space_after_colon = "" # Mặc định: không khoảng trắng
    newline = ""

    if indent_str is not None:
        newline = "\n"
        space_after_colon = " " # Có khoảng trắng khi có indent
        current_indent = indent_str * indent_level
        next_indent = indent_str * (indent_level + 1)

    # Case 1: BXSON Tag (b32, b58, b64)
    if isinstance(data, dict) and data.get("$bxson_type") in ["b32", "b58", "b64"]:
        bx_type = data["$bxson_type"]
        bx_data_str = data.get("data", "").strip() # Lấy data, strip() để dọn dẹp
        
        # Ngắt dòng nếu có indent và data dài
        if indent_str is not None and len(bx_data_str) > 60:
             # Đơn giản hóa: Ngắt dòng 1 lần
             return f"{bx_type}{{{newline}{next_indent}{bx_data_str}{newline}{current_indent}}}"
        else:
             # Dữ liệu ngắn hoặc không indent: trên 1 dòng
             return f"{bx_type}{{{bx_data_str}}}"

    # Case 2: Dictionary
    if isinstance(data, dict):
        if not data:
            return "{}"
        
        items = []
        # Tham số 'separators' giúp kiểm soát khoảng trắng cho JSON key:value string
        separators = (',', ':') if indent_str is None else (f',{newline}', f':{space_after_colon}')

        for k, v in data.items():
            key_str = json.dumps(k) # Đảm bảo key là string JSON hợp lệ
            value_str = _dumps_recursive(v, indent_level + 1, indent_str)
            # FIX: Loại bỏ khoảng trắng trong JSON key string nếu không indent
            if indent_str is None:
                key_str = key_str.replace(': ', ':')
            
            items.append(f"{next_indent}{key_str}{separators[1]}{value_str}")
        
        return f"{{{newline}{separators[0].join(items)}{newline}{current_indent}}}"

    # Case 3: List
    if isinstance(data, list):
        if not data:
            return "[]"
            
        items = []
        separators = (',', '') if indent_str is None else (f',{newline}', f'{space_after_colon}')
        
        for item in data:
            # FIX: Bỏ space_after_colon ở đây vì đây là list, không phải key:value
            items.append(f"{next_indent}{_dumps_recursive(item, indent_level + 1, indent_str)}")
            
        return f"[{newline}{separators[0].join(items)}{newline}{current_indent}]"

    # Case 4: Primitives (str, int, float, bool, None)
    # Sử dụng json.dumps để xử lý chuẩn xác.
    # Khi không indent, json.dumps tạo ra khoảng trắng sau ':' trong dict,
    # nhưng ở đây data là một giá trị đơn lẻ, nên không cần replace.
    return json.dumps(data, ensure_ascii=False)


def dumps(data_structure: Any, *, indent: Union[int, None] = None) -> str:
    """
    Serializes a Python structure (potentially with BXSON tags or bytes)
    into a BXSON formatted string.

    If the structure contains raw 'bytes' objects, they will be encoded
    using the 'b64' format by default.

    Args:
        data_structure (Any): The Python object to serialize.
        indent (int, optional): If specified, formats the output
                                string with newlines and indentation.

    Returns:
        str: The resulting BXSON formatted string.
    """
    
    # Tự động 'encode' (bytes -> tags) nếu cần
    tagged_data = encode(data_structure, default_encoding='b64')

    indent_str = None
    if indent is not None and indent > 0:
        indent_str = " " * indent
        
    return _dumps_recursive(tagged_data, indent_level=0, indent_str=indent_str)

def dump(data_structure: Any, fp: TextIO, *, indent: Union[int, None] = None) -> None:
    """
    Serializes a Python structure to a BXSON formatted stream (file-like object).

    Args:
        data_structure (Any): The Python object to serialize.
        fp (TextIO): The file-like object (e.g., open('f.bxson', 'w')).
        indent (int, optional): If specified, formats the output
                                with newlines and indentation.
    """
    fp.write(dumps(data_structure, indent=indent))


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
            # Sử dụng shorthand --decode ngay tại CLI
            bxson_data = load(f, decode=should_decode)
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
        print("\n--- DECODED RESULT (Bytes Objects) ---")
        pprint.pprint(bxson_data)
    else:
        print("\n--- RAW PARSE RESULT (BXSON Tags) ---")
        pprint.pprint(bxson_data)
        print("\nTip: Run with '--decode' to see Base-X data converted to Python bytes.")
