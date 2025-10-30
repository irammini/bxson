# BXSON: Base-X Structured Object Notation

## 💡 What is BXSON?

BXSON (Base-X Structured Object Notation) is a superset of JSON designed specifically for applications that frequently handle **binary data** alongside standard structured metadata (strings, numbers, booleans). It treats Base32, Base58, and Base64 as first-class citizens in the syntax, eliminating the need to wrap them in standard JSON strings.

This project was developed internally by **Teaserverse** to streamline configuration and asset management across various backend services.

### Key Features

- **First-Class Base-X Types:** Define binary data blocks directly in the syntax: `b32{...}`, `b58{...}`, and `b64{...}`.

- **Teaser RUI Comments:** Supports single-line comments using the `;;` syntax.

- **Clean Output:** The built-in decoder automatically converts these blocks into native Python `bytes` objects.

## 💾 Installation

BXSON requires the `ply` (parser generator) and `base58` libraries.
```bash
pip install bxson

```

## 📜 BXSON Syntax Example (`config.bxson`)
```bxson
;; The Teaser RUI comment style is simple and distinctive.

{
  "api_version": 1.1,
  "service_active": true,

  ;; --- Base64 (Standard binary asset) ---
  "default_icon_png": b64{
    iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAA
  },

  ;; --- Base58 (Used for Crypto/Wallet addresses) ---
  "blockchain_key": b58{
    HwM8GgB1hS24u539Dq8R27R7Pz381P71P81d9A
  },

  ;; --- Base32 (Used for case-insensitive identifiers) ---
  "auth_token_32": b32{
    JBSWY3DPEHPK3PXP
  },

  "metadata": [1, 2, "test", null]
}
```

## 💻 Usage

The `bxson` module provides a familiar Python API (`load` and `loads`) similar to the standard `json` library, plus a powerful `decode` function.

1. **Reading and Decoding Data**
```python
import bxson
import os

# 1. Load from a file
with open('config.bxson', 'r') as f:
    # 'data' contains structure with special {'$bxson_type': 'b64', 'data': '...'} tags
    data_structure = bxson.load(f)

# 2. Decode the structure to convert Base-X tags into Python 'bytes' objects
decoded_config = bxson.decode(data_structure)

# Accessing decoded bytes:
icon_bytes = decoded_config['default_icon_png']
print(f"Icon data type: {type(icon_bytes)}")
# Output: Icon data type: <class 'bytes'>
```

2. **Command Line Tool**

You can also use the module directly to validate and inspect files:
```bash
# Parse file and show the intermediate structure with tags
python -m bxson <filename.bxson>

# Parse and decode file (converting Base-X tags to bytes)
python -m bxson <filename.bxson> --decode
```

## 💖 Contributing

We welcome contributions and suggestions! Feel free to open issues or submit pull requests on the official repository.