# setup.py for BXSON (Base-X Structured Object Notation)

from setuptools import setup, find_packages

setup(
    name='bxson',
    # UPDATE: Bump version to 0.2.0 for new features
    version='0.2.0',
    description='A JSON-like configuration format supporting native Base32, Base58, and Base64 data types, with Teaser RUI-style ;; comments.',
    long_description=open('README.md').read(),
    long_description_content_type='text_markdown',
    author='Teaserverse',
    url='https://github.com/TeaserLang/bxson',
    license='MIT',
    packages=find_packages(exclude=['*.egg-info', 'build', 'venv', 'dist', '__pycache__']), # Loại trừ các thư mục không cần thiết
    py_modules=['bxson'],
    install_requires=[
        'ply>=3.11',  # Lex and Yacc implementation
        'base58>=2.1.1', # For Base58 decoding functionality
    ],
    classifiers=[
        # UPDATE: Status -> 4 - Beta (since it's more feature-complete)
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    keywords=['json', 'base64', 'base32', 'base58', 'parser', 'configuration', 'config', 'serialization', 'teaser'],
)
