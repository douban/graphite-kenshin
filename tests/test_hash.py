#!/usr/bin/env python
# encoding: utf-8

from kenshin_api.fnv1a import get_int32_hash


def cmp_hash(int32_h, uint32_h):
    if uint32_h >= 0x80000000:
        uint32_h -= 0x100000000
    assert int32_h == uint32_h


def test_fnv1a_hash():
    test_cases = [
        ("", 0x811c9dc5),
        ("a", 0xe40c292c),
        ("foobar", 0xbf9cf968),
        ("hello", 0x4f9f2cab),
        (b"\xff\x00\x00\x01", 0xc48fb86d),
    ]

    for s, uint32_h in test_cases:
        int32_h = get_int32_hash(s)
        cmp_hash(int32_h, uint32_h)
