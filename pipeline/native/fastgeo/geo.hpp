// C++17 spatial hot path: point-in-polygon, batch assignment, haversine.
//
// This mirrors pipeline/native/fallback/fastgeo_py.py exactly -- see that
// file's docstrings for the semantics (boundary-inclusive point-in-polygon,
// degenerate-ring handling, dict-insertion-order batch_assign, Earth radius
// constant). Keep arithmetic order identical between the two implementations
// so results agree bit-for-bit (booleans/ints) or within tight float
// tolerance (distances).
#pragma once

#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace fastgeo {

using Point = std::pair<double, double>;  // (lat, lng)
using Ring = std::vector<Point>;          // (lat, lng) vertices, implicitly closed

// Ray-casting point-in-polygon test. Rings with fewer than 3 vertices have
// no area and always return false. Points exactly on an edge or vertex
// count as inside.
bool point_in_polygon(double lat, double lng, const Ring &ring);

// Assigns each point to the first polygon (in the given order) containing
// it; nullopt if no polygon contains the point. `polygons` order must match
// the Python dict's insertion order (handled by the pybind11 binding layer).
std::vector<std::optional<std::string>> batch_assign(
    const std::vector<Point> &points,
    const std::vector<std::pair<std::string, Ring>> &polygons);

// Pairwise great-circle distances (meters) between two point sets.
std::vector<std::vector<double>> haversine_matrix(
    const std::vector<Point> &points_a, const std::vector<Point> &points_b);

}  // namespace fastgeo
