"""Pruebas del analizador léxico de Mini C segun la especificación de la skill."""

import pytest

from minic.diagnostics.diagnostic_code import LEX001
from minic.lexer.lexer import Lexer
from minic.lexer.token_type import TokenType
from minic.output.diagnostic_printer import format_diagnostic
from minic.output.token_printer import format_token


def test_section_7_valid_source() -> None:
    source = "int2 = 12abc;\nwhilex == -5"
    tokens, diagnostics = Lexer(source).scan()

    assert diagnostics == []

    formatted = [format_token(t) for t in tokens]
    expected = [
        "IDENTIFIER 'int2' 1 1",
        "ASSIGN '=' 1 6",
        "INTEGER_LITERAL '12' 1 8",
        "IDENTIFIER 'abc' 1 10",
        "SEMICOLON ';' 1 13",
        "IDENTIFIER 'whilex' 2 1",
        "EQUAL_EQUAL '==' 2 8",
        "MINUS '-' 2 11",
        "INTEGER_LITERAL '5' 2 12",
        "EOF '' 2 13",
    ]
    assert formatted == expected

    # Verificar literales
    assert tokens[2].literal == 12
    assert tokens[8].literal == 5
    for i, t in enumerate(tokens):
        if i not in (2, 8):
            assert t.literal is None


def test_section_7_source_with_errors() -> None:
    source = "int x = @;\nx ! = 0; // fin"
    tokens, diagnostics = Lexer(source).scan()

    formatted_tokens = [format_token(t) for t in tokens]
    expected_tokens = [
        "KW_INT 'int' 1 1",
        "IDENTIFIER 'x' 1 5",
        "ASSIGN '=' 1 7",
        "SEMICOLON ';' 1 10",
        "IDENTIFIER 'x' 2 1",
        "ASSIGN '=' 2 5",
        "INTEGER_LITERAL '0' 2 7",
        "SEMICOLON ';' 2 8",
        "IDENTIFIER 'fin' 2 13",
        "EOF '' 2 16",
    ]
    assert formatted_tokens == expected_tokens

    formatted_diagnostics = [format_diagnostic(d) for d in diagnostics]
    expected_diagnostics = [
        "LEX001 error 1:9 Carácter no reconocido: '@'",
        "LEX001 error 2:3 Carácter no reconocido: '!'",
        "LEX001 error 2:10 Carácter no reconocido: '/'",
        "LEX001 error 2:11 Carácter no reconocido: '/'",
    ]
    assert formatted_diagnostics == expected_diagnostics


def test_empty_source() -> None:
    tokens, diagnostics = Lexer("").scan()
    assert diagnostics == []
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF
    assert tokens[0].lexeme == ""
    assert tokens[0].line == 1
    assert tokens[0].column == 1


def test_keywords_vs_identifiers() -> None:
    source = "int while int2 whilex _int _while INT WHILE"
    tokens, diagnostics = Lexer(source).scan()
    assert diagnostics == []
    types = [t.type for t in tokens[:-1]]
    assert types == [
        TokenType.KW_INT,
        TokenType.KW_WHILE,
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
    ]


def test_operators_maximum_munch() -> None:
    source = "== != = === !=="
    tokens, diagnostics = Lexer(source).scan()
    assert diagnostics == []
    types = [t.type for t in tokens[:-1]]
    assert types == [
        TokenType.EQUAL_EQUAL,
        TokenType.NOT_EQUAL,
        TokenType.ASSIGN,
        TokenType.EQUAL_EQUAL,
        TokenType.ASSIGN,
        TokenType.NOT_EQUAL,
        TokenType.ASSIGN,
    ]


def test_all_delimiters_and_single_operators() -> None:
    source = "+ - ( ) { } ; ="
    tokens, diagnostics = Lexer(source).scan()
    assert diagnostics == []
    types = [t.type for t in tokens[:-1]]
    assert types == [
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.LBRACE,
        TokenType.RBRACE,
        TokenType.SEMICOLON,
        TokenType.ASSIGN,
    ]


def test_integer_literal_leading_zeros() -> None:
    source = "007 0 42"
    tokens, diagnostics = Lexer(source).scan()
    assert diagnostics == []
    assert tokens[0].type == TokenType.INTEGER_LITERAL
    assert tokens[0].lexeme == "007"
    assert tokens[0].literal == 7

    assert tokens[1].type == TokenType.INTEGER_LITERAL
    assert tokens[1].lexeme == "0"
    assert tokens[1].literal == 0

    assert tokens[2].type == TokenType.INTEGER_LITERAL
    assert tokens[2].lexeme == "42"
    assert tokens[2].literal == 42


def test_whitespace_and_tab_positions() -> None:
    # \t cuenta como 1 columna
    source = "\t\tint x;\r\ny;"
    tokens, diagnostics = Lexer(source).scan()
    assert diagnostics == []
    # col 1 es \t, col 2 es \t, col 3 es 'i'
    assert tokens[0].line == 1
    assert tokens[0].column == 3
    assert tokens[0].type == TokenType.KW_INT

    # \r\n abre línea 2, 'y' en col 1
    assert tokens[3].line == 2
    assert tokens[3].column == 1
    assert tokens[3].type == TokenType.IDENTIFIER
