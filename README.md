# BXSON: Base-X Structured Object Notation

## 💡 What is BXSON?

BXSON (Base-X Structured Object Notation) is a superset of JSON designed specifically for applications that frequently handle **binary data** alongside standard structured metadata (strings, numbers, booleans). It treats Base32, Base58, and Base64 as first-class citizens in the syntax, eliminating the need to wrap them in standard JSON strings.

This project was developed internally by **Teaserverse** to streamline configuration and asset management across various backend services.

### Key Features

- **First-Class Base-X Types:** Define binary data blocks directly in the syntax: `b32{...}`, `b58{...}`, and `b64{...}`.

- **Full JSON Superset:** Supports all standard JSON data types (strings, numbers, booleans, objects, arrays, null).

- **Teaser RUI Comments:** Supports single-line comments using the `;;` syntax.

- **Two-Way Sserialization:** Provides a full `load`/`loads` (parsing) and `dump`/`dumps` (serialization) API, similar to Python's `json` module.

- **Automatic Encoding/Decoding:** Can directly convert Python `bytes` objects into Base-X blocks during serialization, and Base-X blocks back into `bytes` during parsing.

## 💾 Installation

BXSON requires the `ply` (parser generator) and `base58` libraries.
```bash
pip install bxson

```

## 📜 BXSON Syntax Example (`config.bxson`)
```bxson
;; This is a standard Teaser RUI comment.

{
  "api_version": 1.1,
  "service_active": true,

  ;; --- Base64 (Binary assets/small images) ---
  "icon_data": b64{
    iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAA
  },

  ;; --- Base58 (e.g., Blockchain/Wallet addresses) ---
  "blockchain_key": b58{
    HwM8GgB1hS24u539Dq8R27R7Pz381P71P81d9A
  },

  ;; --- Base32 (Case-insensitive identifiers) ---
  "auth_token_32": b32{
    JBSWY3DPEHPK3PXP
  },

  "metadata": [1, 2, "test", null]
}
```

## 💻 Usage

The `bxson` module provides a familiar Python API (`load`, `loads`, `dump`, `dumps`) similar to the standard `json` library.

1. **Parsing and Decoding (The easy way!)**

Use the new `decode=True` parameter to parse and convert all Base-X tags directly into native Python `bytes` objects in one step.
```python
import bxson
import base58 # Used to confirm dependency

# 1. Loading from string with automatic decoding
bxson_string = '{"key": b64{AQIDBA}, "active": true}'
decoded_config = bxson.loads(bxson_string, decode=True)

# Output: decoded_config == {'key': b'\x01\x02\x03\x04', 'active': True}
print(f"Key data type: {type(decoded_config['key'])}")
# Output: Key data type: <class 'bytes'>
```

2. **Encoding and Dumping (Convert bytes back to BXSON)**

You can convert a standard Python dictionary containing `bytes` objects back into a formatted BXSON string. By default, `bytes` are encoded as **Base64**.
```python
import bxson
import base64
import json

# Python object with raw bytes
py_data = {
    "version": 2.0,
    "secret_key_bytes": b'\xf0\x9f\x98\x80' * 5, # 20 bytes
    "is_secure": True
}

# Convert to formatted BXSON string
bxson_output = bxson.dumps(py_data, indent=2)

print(bxson_output)
# Output:
# {
#   "version": 2.0,
#   "secret_key_bytes": b64{
#     8J+Ygf+Ygf+Ygf+Ygf+Yg
#   },
#   "is_secure": true
# }
```

3. **Using with Files**

The `load` and `dump` functions work exactly like their `json` library counterparts, supporting the new `decode` and `indent` features.

```python
import io
import bxson

# Assuming RAW_DATA = b'...'
raw_data = b'Teaserverse'

# Write data to a file (Output: BXSON string)
output_file = io.StringIO()
bxson.dump({"data": raw_data}, output_file, indent=4)
print("--- File writing successful ---")


# Read data from the file (Input: BXSON string, Output: Python dict with bytes)
output_file.seek(0)
loaded_data = bxson.load(output_file, decode=True)

print(f"Decoded data: {loaded_data['data']}")
# Output: Decoded data: b'Teaserverse'
```

4. **Command Line Tool**

You can also use the module directly to validate and inspect files:
```bash
# Parse file and show the intermediate structure with tags
python -m bxson <filename.bxson>

# Parse and decode file (converting Base-X tags to bytes)
python -m bxson <filename.bxson> --decode
```

## 💖 Contributing

We welcome contributions and suggestions! Feel free to open issues or submit pull requests on the official repository.