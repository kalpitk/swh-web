#!/usr/bin/rdmd
// Computes average line length for standard input.
import std.stdio;

/+
  this is a /+ nesting +/ comment
+/

enum COMPILED_ON = __TIMESTAMP__;  // special token

enum character = '©';
enum copy_valid = '&copy;';
enum backslash_escaped = '\\';

// string literals
enum str = `hello "world"!`;
enum multiline = r"lorem
ipsum
dolor";  // wysiwyg string, no escapes here allowed
enum multiline2 = "sit
amet
\"adipiscing\"
elit.";
enum hex = x"66 6f 6f";   // same as "foo"

#line 5

// float literals
enum f = [3.14f, .1, 1., 1e100, 0xc0de.01p+100];

static if (something == true) {
   import std.algorithm;
}

void main() pure nothrow @safe {
    ulong lines = 0;
    double sumLength = 0;
    foreach (line; stdin.byLine()) {
        ++lines;
        sumLength += line.length;
    }
    writeln("Average line length: ",
        lines ? sumLength / lines : 0);
}