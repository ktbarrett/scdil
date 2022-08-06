# Simple Configuration and Data Interchange Language Specification

**Parse Rules**
```
scdil() variable N = node(N)
```

## Ignored Productions

Whitespace and comments are ignored by the parser.

### Whitespace and Newlines

Newlines include `\n`, `\r\n` and `\r` characters.
Whitespace includes spaces (` `) and any newline characters.
Tab characters are *not* allowable whitespace.
Non-breaking spaces (U+00A0) are *not* allowable whitespace.
All whitespace is ignored by the parser.

**Parse Rules**
```
ws = " " | nl
nl = "\n" | "\r\n" | "\r"
```

### Comments

Comments start with `#` and run until the end of the line.
Comments are ignored by the parser.

**Examples**
```
# this is a comment
a: 1  # this is also a comment
```

**Parse Rules**
```
comment = "#" (!nl .)*
```

## Scalar Types

**Parse Rules**
```
scalar(N) = null@N | boolean@N | integer@N | float@N | string@N
```

### `null`

**Parse Rules**
```
null = "null"
```

### Booleans

**Parse Rules**
```
boolean = "true" | "false".
```

### Integers

**Examples**
```
0
-1
42
0xDEADbeef
0b001100010010011110100001101101110011
0o644
```

**Parse Rules**
```
integer = "[+-]"? ("0" | decimal_literal | hex_literal | octal_literal | binary_literal)
decimal_literal = "[+-]?[0-9]+"
hex_literal = "0[xX][0-9A-Fa-f]+"
octal_literal = "0[oO][0-7]+"
binary_literal = "0[bB][01]+"
```

**Implementation Note**: Integers are preferably arbitrary-precision integers,
but should be signed 64-bit integers (int64_t or similar) at a minimum.

**Implementation Note**:
Implementations with limited-precision integers should provide a mechanism to inform the code loading the document when integer overflow occurs.
When overflow occurs, the resulting value is allowed to be implementation-defined.

### Floats

**Examples**
```
+0.123
-1234123e4
12.34e-5
+inf
nan
```

**Parse Rules**
```
float = decimal_literal (fractional exponent? | exponent) | "[+-]?inf" | "nan"
fractional = "\.[0-9]*"
exponent = "[eE][+-]?[0-9]+"
```

**Implementation Note**: Floats natively are preferably double-precision IEEE754 floating point numbers;
although single-precision is allowable.

**Implementation Note**: Float support is preferable, but optional. This is to allow supporting targets that have no native floating point type.
Implementations that don't support floats should provide a mechanism to inform the code loading the document when a float is seen.
The resulting value is allowed to be implementation-defined.

### Escape Codes and Characters

Characters in strings and block strings can be any Unicode codepoint besides:
* the C0 control character set (U+0000 through U+001F)
* the C1 control character set (U+0080 through U+009F)
* the DEL codepoint (U+007F)

**Note**: Newlines (`\n`, `\r\n`, or `\r`) and tabs (`\t`) are in the C0 character set and are ***not allowed in strings***.
Instead, the user is expected to use escape codes.
This is intentional.

Escape codes supported in strings and escaped block strings are:
* `\n`: newline
* `\t`: tab character
* `\r`: carriage return
* `\"`: the `"` character
* `\\`: the `\` character
* `\b`: backspace
* `\f`: form feed
* `\/`: the `/` character
* `\x{hex}{hex}`: byte literal for sending binary data
* `\u{hex}{hex}{hex}{hex}`: unicode codepoint
* `\U{hex}{hex}{hex}{hex}{hex}{hex}{hex}{hex}`: extended unicode codepoint

**Note** the DEL character and the C1 control characters are not supported; however, they are supported in JSON.
While this breaks JSON support, it is intentional.

**Parse Rules**
```
character = "[\U00000020-\U0000007E\U000000A0-\U0010FFFF]"
escape = "\\\\"
       | "\\/"
       | "\\\""
       | "\\b"
       | "\\f"
       | "\\n"
       | "\\r"
       | "\\t"
       | "\\x[0-9a-fA-F]{2}"
       | "\\u[0-9a-fA-F]{4}"
       | "\\U[0-9a-fA-F]{8}"
```

### Strings

Strings are a sequence of characters or escape code delimited with `"` characters.

**Examples**
```
"Hello, World!\n"
"\xDE\xAD\xBE\xEF"
"\U0001F604"
```

**Parse Rules**
```
string = "\"" (escape | !"\"" character)* "\""
```

## Composite Types

Composite types are primarily for program-to-program data interchange or as a terse single-line syntax at leafs of configuration files.
Composites are comprised solely of scalars or nested compsites; no block entities are allowed.
Whitespace is not significant inside of a composite.

**Parse Rules**
```
composite(N) = sequence(N) | mapping(N)
value(N) = scalar(N) | composite(N)
```

### Sequences

Sequences are heterogenously-typed ordered collections.
Newlines are ignored as insignificant whitespace while parsing a sequence.

**Examples**
```
[1, "2", null]
[
    {"a": 1}, [5, 6, 4, 3]
    1, 2, 3
]
```

**Parse Rules**
```
sequence(N) = "["@N (value(_) ",")* (value(_) ","?)? "]"
```

### Mappings

Mappings are heterogenously-typed unordered associative collections.
Mapping keys must be unique.
Newlines are ignored as insignificant whitespace while parsing a mapping.

**Examples**
```
{"a": 6, 1: null, [1, 2, 3]: {}}
{
    0: false,
            1: true
}
```

**Parse Rules**
```
mapping(N) = "{"@N (value(_) ":" value(_) ",")* (value(_) ":" value(_) ","?)? "}"
```

## Blocks

Blocks organize data in an easily readible way, and are primarily for human-to-program data interchange (AKA configuration).
Blocks start when the first element of the block is seen at an logical indentation level greater than the encompasing block.
Then they end when an element of some other block at a lower indentation level is seen.
Each element of a block must start on the next non-empty line.

**Parse Rules**
```
block(N) = block_sequence(N) | block_mapping(N) | block_string(N)
node(N) = value(N) | block(N)
```

### Block Sequences

Block sequences are the block form of sequences.
Each element in the sequence starts on a different line with the `-` character.

**Examples**
```
- 1
- 2
-        # start new block on next line
  - 3
  - - 4  # start block on the same line
    - 5
```

**Parse Rules**
```
block_sequence(N) = block_sequence_element(N)+
block_sequence_element(N) variable M where M>N = "-"@N node(M))
```

### Block Mappings

Block mappings are the block form of mappings.
Each element in the mapping starts on a different line with either an unquoted name or a string, followed by the `:` character.
Names are unquoted strings with no spaces, and are limited in which characters can be used (to ease parsing).
Names are prefered for block mapping keys, but if you need to use a character that isn't supported by names, you can use a quoted string instead.
If your mapping contains key types other than strings, it is recommended to use a non-block mapping.

**Examples**
```
a: 1
b:            # start block on the next line
  c: 1
  d: e: 1     # start block on the same line
     "\n": 2  # use a string instead of a name
```

**Parse Rules**
```
block_mapping(N) = block_mapping_element(N)+
block_mapping_element(N) variable M where M>N = (name@N | string@N) ":" node(M))
name = letter (letter | "[0-9]")*
letter = "[_a-zA-Z\U000000A0-\U0010FFFF]"
```

### Block Strings

Block strings allow the user to write multi-line string literals.
This is often used to embed other data formats directly into your document.

There are four kinds of lines in a block string depending on the character used to start the line.
* `|`: don't convert any escape codes and include the trailing space and newline.
* `>`: don't convert any escape codes and "fold" the line into the next one.
* `\|`: convert any escape codes and include any trailing space and newline.
* `\>`: convert any escape codes and "fold" the line into the next one.

Line "folding" is done by:
1. Striping any space at the beginning of the line.
2. Replacing any trailing whitespace and the newline with a single space.
3. Unless the line is empty; in which case the line is replaced with a single newline.

This folding logic is similar to how Github renders Markdown, or LaTeX renders text.


**Examples**
```
a:
  |for i in range(10):
  |    if i % 2 == 0:
  |        print(i)
  |
b:
  > Writing one sentence per line.
  > SCDIL will join them together.
  >
  > But not this one.
```

**Parse Rules**
```
block_string(N) = literal_lines(N) | folded_lines(N) | escaped_literal_lines(N) | escaped_folded_lines(N)
literal_lines(N) = (literal_line@N)+
folded_lines(N) = (folded_line@N)+
escaped_literal_lines(N) = (escaped_literal_line@N)+
escaped_folded_lines(N) = (escaped_folded_line@N)+
literal_line = "\|" character*
folded_line = ">" character*
escaped_literal_line = "\\\|" (escape | character)*
escaped_folded_line = "\\>" (escape | character)*
```

**Warning**: Comments in block strings will be interpreted as a part of the string.

## Total Language

The language description uses a combination of RegEx and PEG notation.
The syntax `@N` means that the token it's aplied to must start at charno=N in the line.
Rules that use context-dependent features like `@N` take context variables as an argument and are described with function-like syntax.
Function-like Rules may have variables and guard clauses.

**Nodes**
```
scdil() variable N = node(N)
node(N) = block(N) | value(N)
value(N) = scalar(N) | composite(N)
scalar(N) = null@N | boolean@N | integer@N | float@N | string@N
composite(N) = sequence(N) | mapping(N)
sequence(N) = "["@N (value(_) ",")* (value(_) ","?)? "]"
mapping(N) = "{"@N (value(_) ":" value(_) ",")* (value(_) ":" value(_) ","?)? "}"
block(N) = block_sequence(N) | block_mapping(N) | block_string(N)
block_sequence(N) = block_sequence_element(N)+
block_sequence_element(N) variable M where M>N = "-"@N node(M))
block_mapping(N) = block_mapping_element(N)+
block_mapping_element(N) variable M where M>N = (name@N | string@N) ":" node(M))
block_string(N) = literal_lines(N) | folded_lines(N) | escaped_literal_lines(N) | escaped_folded_lines(N)
literal_lines(N) = (literal_line@N)+
folded_lines(N) = (folded_line@N)+
escaped_literal_lines(N) = (escaped_literal_line@N)+
escaped_folded_lines(N) = (escaped_folded_line@N)+
```

**Tokens and Character Sets**
```
null = "null"
boolean = "true" | "false"
integer = decimal_literal | hex_literal | octal_literal | binary_literal
decimal_literal = "[+-]?[0-9]+"
hex_literal = "0[xX][0-9A-Fa-f]+"
octal_literal = "0[oO][0-7]+"
binary_literal = "0[bB][01]+"
float = decimal_literal (fractional exponent? | exponent) | "[+-]?inf" | "nan"
fractional = "\.[0-9]*"
exponent = "[eE][+-]?[0-9]+"
character = "[\U00000020-\U0000007E\U000000A0-\U0010FFFF]"
escape = "\\\\"
       | "\\/"
       | "\\\"
       | "\\b"
       | "\\f"
       | "\\n"
       | "\\r"
       | "\\t"
       | "\\x[0-9a-fA-F]{2}"
       | "\\u[0-9a-fA-F]{4}"
       | "\\U[0-9a-fA-F]{8}"
string = "\"" (escape | !"\"" character)* "\""
name = letter (letter | "[0-9]")*
letter = "[_a-zA-Z\U000000A0-\U0010FFFF]"
literal_line = "\|" character*
folded_line = ">" character*
escaped_literal_line = "\\\|" (escape | character)*
escaped_folded_line = "\\>" (escape | character)*
```

**Ignored**
```
ws = " " | nl
nl = "\n" | "\r\n" | "\r"
comment = "#" (!nl .)*
```
