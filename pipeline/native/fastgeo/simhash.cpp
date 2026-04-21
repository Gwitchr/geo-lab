#include "fastgeo/simhash.hpp"

#include <array>
#include <bitset>
#include <vector>

namespace fastgeo {

namespace {

// FNV-1a 64-bit constants -- must match _FNV_OFFSET_BASIS / _FNV_PRIME in
// fallback/fastgeo_py.py.
constexpr std::uint64_t kFnvOffsetBasis = 14695981039346656037ULL;
constexpr std::uint64_t kFnvPrime = 1099511628211ULL;

std::uint64_t fnv1a64(const std::string &token) {
    std::uint64_t hash = kFnvOffsetBasis;
    for (unsigned char byte : token) {
        hash ^= static_cast<std::uint64_t>(byte);
        hash *= kFnvPrime;
    }
    return hash;
}

// Word bytes: ASCII letters/digits, or any byte >= 0x80 (part of a
// multi-byte UTF-8 sequence -- keeps accented Spanish characters intact
// without a Unicode-aware library). Must match _is_word_byte() in
// fallback/fastgeo_py.py.
bool is_word_byte(unsigned char b) {
    return b >= 0x80 || (b >= '0' && b <= '9') || (b >= 'A' && b <= 'Z') || (b >= 'a' && b <= 'z');
}

std::vector<std::string> tokenize(const std::string &text) {
    std::vector<std::string> tokens;
    std::string current;

    for (unsigned char b : text) {
        if (is_word_byte(b)) {
            if (b >= 'A' && b <= 'Z') {
                b = static_cast<unsigned char>(b + ('a' - 'A'));
            }
            current.push_back(static_cast<char>(b));
        } else if (!current.empty()) {
            tokens.push_back(current);
            current.clear();
        }
    }
    if (!current.empty()) {
        tokens.push_back(current);
    }

    return tokens;
}

}  // namespace

std::uint64_t simhash64(const std::string &text) {
    const auto tokens = tokenize(text);
    if (tokens.empty()) {
        return 0;
    }

    std::array<long long, 64> weights{};
    for (const auto &token : tokens) {
        const std::uint64_t h = fnv1a64(token);
        for (int bit = 0; bit < 64; ++bit) {
            if ((h >> bit) & 1ULL) {
                weights[static_cast<std::size_t>(bit)] += 1;
            } else {
                weights[static_cast<std::size_t>(bit)] -= 1;
            }
        }
    }

    std::uint64_t result = 0;
    for (int bit = 0; bit < 64; ++bit) {
        if (weights[static_cast<std::size_t>(bit)] > 0) {
            result |= (1ULL << bit);
        }
    }

    return result;
}

int hamming(std::uint64_t a, std::uint64_t b) {
    return static_cast<int>(std::bitset<64>(a ^ b).count());
}

}  // namespace fastgeo
