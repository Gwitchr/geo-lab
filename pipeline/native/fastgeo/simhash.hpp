// 64-bit simhash text fingerprint + Hamming distance.
//
// Mirrors pipeline/native/fallback/fastgeo_py.py's simhash64/hamming
// exactly: same FNV-1a 64-bit token hash, same byte-level tokenization
// (ASCII letters/digits and any byte >= 0x80 are word bytes; only ASCII
// uppercase is folded to lowercase), same per-bit majority-vote combine.
#pragma once

#include <cstdint>
#include <string>

namespace fastgeo {

std::uint64_t simhash64(const std::string &text);

int hamming(std::uint64_t a, std::uint64_t b);

}  // namespace fastgeo
