# Conditional Expressions

This document explains how Globifest processes conditional expressions

## 0 Legal Stuff

Please read the Software License ([LICENSE.md](../LICENSE.md)) and Contributor License Agreement ([CLA.md](../CLA.md)).

## 1 Parsing the Expression

Whitespace is ignored, but each token in the sequence must be identifiable as one of the following:

* Predefined value (`TRUE` or `FALSE`)
* Identifier (Sequence of `A-Z`, `a-z`, `0-9`, or `_`)
* Integer (Sequence of `0-9` or `-`)
* String (Text beginning with `"` or `'` and ending with the same character)
* Operator (listed below)

The data types used in conditional expression roughly correspond to the same types used by the configuration system.

Examples:

* `TRUE` and `FALSE` are `bool`
* `-10`, `0` and `42` are all `int`
* `"hello"` is a `string`
* `my_value` is an `identifier`

## 2 Evaluation

Any conditional expression must ultimately simplify to a `bool` expression which is equal to `TRUE` or `FALSE`.

### 2.1 Operators

There are several operators recognized by the parser, and some have required type constraints.

#### 2.1.1 Unary Operators

Unary operators only take one parameter.

##### 2.1.1.1 Logical Inverse

Usage: `!<bool>`

Examples:

* `!TRUE` evaluates to `FALSE`
* `!FALSE` evaluates to `TRUE`
* When `my_var` is set to `FALSE`, `!my_var` evaluates to `TRUE`

#### 2.1.2 Binary Operators

Binary operators take two parameters.

Usage: `<value1><op><value2>`

##### 2.1.2.1 Standard Comparison Operators

The allowed values of `<op>` are:

* `==` Equal to (may also use `=`)
* `!=` Not equal to
* `<=` Less than or equal to
* `<` Less than
* `>=` Greater than or equal to
* `>` Greater than

The parameters `<value1>` and `<value2>` can be any value that is convertible to the same type.  For example, assume the following conditions:

* `my_int1` has a value of `1`
* `my_int2` has a value of `1`

Then the following expressions will evaluate:

* `1 == 1` evaluates to `TRUE`
* `1 == 2` evaluates to `FALSE`
* `my_int1 == 1` evaluates to `TRUE`
* `2 == my_int2` evaluates to `TRUE`
* `my_int1 == my_int2` evaluates to `FALSE`

##### 2.1.2.2 Logical Comparison Operators

The allowed values of `<op>` are:

* `&&` Logical AND
* `||` Logical OR

The parameters `<value1>` and `<value2>` must be a `bool` constant or identifier.  For example, assume the following conditions:

* `a` has a value of `TRUE`
* `b` has a value of `FALSE`

Then the following expressions will evaluate:

* `TRUE && TRUE` evaluates to `TRUE`
* `a && TRUE` evaluates to `TRUE`
* `b && TRUE` evaluates to `FALSE`
* `FALSE && b` evaluates to `FALSE`
* `a || b` evaluates to `TRUE`
* `b || FALSE` evaluates to `FALSE`

### 2.2 Order of Operations

The order of operations is left-to-right.  Example:

The expression `FALSE || FALSE == FALSE || TRUE` simplifies as follows:

1. `FALSE == FALSE || TRUE`
2. `TRUE || TRUE`
3. `TRUE`

### 2.3 Nested Expressions

Any part of the expression can be surrounded by Parentheses `(` and `)` to cause the contents of the section to be evaluated prior to generating a result.  Example:

The expression `(FALSE || FALSE) == (FALSE || TRUE)` simplifies as follows:

1. `FALSE == (FALSE || TRUE)`
2. `FALSE == TRUE`
3. `FALSE`
