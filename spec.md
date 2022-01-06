# Simple Configuration and Data Interchange Language Specification

## Comments

Comments start with `#` and run until the end of the line.

```
# comment
a: 1  # also comment
```

## Scalar Types

**Regex/PEG**
```
scalar = null / boolean / number / string
```

### `null`

**Regex/PEG**
```
null = "null"
```

### Booleans

**Regex/PEG**
```
boolean = "true" / "false".
```

### Numbers

Numbers are IEE754-esque floating point numbers.
A number literal is an integer part (required),
prefixed with an optional positive or negative sign,
postfixed with an optional decimal point and fractional part,
further postfixed with an optional exponential part.

Additionally, there are the special number values that are spelled with keywords:
* `.inf` for positive infinity
* `-.inf` for negative infinity
* `.nan` for "not a number"

**Example**
```
0
-0.00001
1123.0e+4
```

**Regex/PEG**
```
number_keywords = -?\.inf / \.nan
number = "0" / ( "-"? "[1-9]" "[0-9]"* ( "." "[0-9]"+ )? ( "[eE]" "[+-]"? "[0-9]"* )? ) / number_keywords
```

### Strings

Strings are delimited with `"` characters.
Strings cannot contain any non-visible character, including newlines and horizontal tabs; and instead rely on escape codes.

Allowable escape codes are:
* `\n`: newline
* `\t`: tab character
* `\r`: carriage return
* `\"`: the `"` character
* `\\`: the `\` character
* `\b`: backspace
* `\f`: form feed
* `\/`: the `/` character
* `\x{hex}{hex}`: byte literal for sending binary data
* `\u{hex}{hex}{hex}{hex}`: unicode code point
* `\U{hex}{hex}{hex}{hex}{hex}{hex}{hex}{hex}`: extended unicode code point

**Example**
```
"Hello! \U0001F603"
">\t prompt"Composite
"\xDE\xAD\xBE\xEF"
```

**Regex/PEG**
```
hex = "[0-9a-fA-F]"
character = "[\U00000020-\U0000007E\U000000A0-\U0010FFFF]"
escape = "\\" ("[\"\\/bfnrt]" / ("x" hex^2 ) / ("u" hex^4) / ("U" hex^8) )
string = "\"" ( escape / (character - "\"") )* "\""
```

**Note** the DEL character and the C1 control character set are not supported.
This does subtly break JSON support.

## Composite Types

Composite types are primarily for program-to-program data interchange or as a terse single-line syntax at leafs of configuration files.

**Regex/PEG**
```
composite = sequence / mapping
```

### Sequences

Sequences are started with the `[` character,
end with the `]` character,
and each element is separated with a `,` character.
Sequences can contain any scalar or composite value as elements.
Sequences are heterogenously-typed.
All newlines inside a sequence definition are ignored as whitespace.

**Example**
```
[1, "2", null]
[{"a": 1}, [5, 6, 4, 3]]
```

**Regex/PEG**
```
sequence = "[" (value ",")* (value ","?)? "]"
```

### Mappings

Mappings are started with the `{` character,
end with the `}` character,
and each element is a key-value pair separated with a `,` character.
Key-value pairs are a "key", which is any scalar or composite value;
and a "value", which is any scalar or composite value;
separated by a `:` character.
Mappings are heterogenously-typed in both their keys and values.
All newlines inside a mapping definition are ignored as whitespace.

**Example**
```
{"a": 6, 1: null  , [1, 2, 3]: {}}
```

**Regex/PEG**
```
mapping = "{" (value ":" value ",")* (value ":" value ","?)? "}"
```

## Structural Features

Structural features organize data in an easily readible way, and are primarily for human-to-program data interchange.

**Regex/PEG**
```
struct = sections / items / paragraph
```

### Sections

Sections are a more readible and writable way to create mappings.
Keys in sections are typically specifically with identifiers.
Sections can be started in any structural context.
Keys in sections are names or quoted strings, they are followed by the `:` character, and then any structural, composite, or scalar value.
Successive key-value pairs must appear on successing lines with the same level of indentation as the first key-value pair in the section.

**Example**
```
config:
  param: "value"
  optional_param: null
  constructed_param: ["type", {"a": 1, "b": 2}]
  files:
    "../../file.txt": "set1"
    "file2.py": "set2"
```

**Regex/PEG**
```
letter = "[_a-zA-Z\U000000A0-\UFFFFFFFF]"
identifier = letter (letter / "[0-9]")*
sections = indent (identifier / string) ":" (struct / value) (nodent (identifier / string) ":" (struct / value))* dedent
```

### Items

Items are a more readible and writable way to do sequences.
Items can be started in any structural context.
Elements are prefix with `-` and at least one space followed by any value.
Each element must appear on a new line with the same level of indentation as the list element in the list.

**Example**
```
- 1
- null
- [1, 2, 3]
-
  - 1
  -
    a: 1
    b: 2
- "value"
```

**Regex/PEG**
```
items = (indent / nodent) "-" (struct / value) (nodent "-" (struct / value))* dedent
```

### Paragraphs

Paragraphs are multi-line string literals, allowing you to embed other formats directly into your data.
Paragraphs are started with a `|` character.
The paragraph text starts on the line after the `|` character with an increase in indentation.
The paragraph text ends when the next line is a decrease in indentation.
Whatever the indentation of the first line in the paragraph is is subtracted from the succeeding lines in the paragraph.

**Warning**: you cannot use comments in the paragraph text, they will be interpreted as a part of the value.

**Example**
```
a: |
  The quick brown fox jumped over the lazy dog.
  Then the young pup quickly persued.
b: 1
```

**Regex/PEG**
```
paragraph = "|" indent character* (nodent character*)* dedent
```


## Total Language

```
scdil = struct / (indent value dedent)
value = scalar / composite
scalar = null / boolean / number / string
composite = sequence / mapping
struct = sections / items / paragraph
null = "null"
boolean = "true" / "false"
number_keywords = -?\.inf / \.nan
number = "0" / ( "-"? "[1-9]" "[0-9]"* ( "." "[0-9]"+ )? ( "[eE]" "[+-]"? "[0-9]"* )? ) / number_keywords
hex = "[0-9a-fA-F]"
character = "[\U00000020-\U0000007E\U000000A0-\U0010FFFF]"
escape = "\\" ("[\"\\/bfnrt]" / ("x" hex^2 ) / ("u" hex^4) / ("U" hex^8) )
string = "\"" ( escape / (character - "\"") )* "\""
sequence = "[" (value ",")* (value ","?)? "]"
mapping = "{" (value ":" value ",")* (value ":" value ","?)? "}"
letter = "[_a-zA-Z\U000000A0-\UFFFFFFFF]"
identifier = letter (letter / "[0-9]")*
sections = indent (identifier / string) ":" (struct / value) (nodent (identifier / string) ":" (struct / value))* dedent
items = (indent / nodent) "-" (struct / value) (nodent "-" (struct / value))* dedent
paragraph = "|" indent character* (nodent character*)* dedent
indent = newline with increase in indentation compared to last line that had code
dedent = newline with decrease in indentation compared to last line that had code
nodent = newline with no change in indentation compared to that last line that had code
```
