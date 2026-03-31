#include "fastgeo/geo.hpp"

#include <cmath>

namespace fastgeo {

namespace {

// Mean Earth radius in meters -- must match _EARTH_RADIUS_M in
// fallback/fastgeo_py.py.
constexpr double kEarthRadiusMeters = 6371000.0;

// True if (px, py) lies exactly on the closed segment [(ax, ay), (bx, by)].
// Epsilon-free: exact cross-product-zero collinearity check, then a
// bounding-box containment check. Must mirror _on_segment() in
// fallback/fastgeo_py.py operation-for-operation for bit-exact parity.
bool on_segment(double px, double py, double ax, double ay, double bx, double by) {
    const double cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax);
    if (cross != 0.0) {
        return false;
    }
    const double min_x = ax <= bx ? ax : bx;
    const double max_x = ax <= bx ? bx : ax;
    const double min_y = ay <= by ? ay : by;
    const double max_y = ay <= by ? by : ay;
    return px >= min_x && px <= max_x && py >= min_y && py <= max_y;
}

double haversine_meters(double lat1, double lng1, double lat2, double lng2) {
    constexpr double kDegToRad = M_PI / 180.0;
    const double phi1 = lat1 * kDegToRad;
    const double phi2 = lat2 * kDegToRad;
    const double dphi = (lat2 - lat1) * kDegToRad;
    const double dlambda = (lng2 - lng1) * kDegToRad;
    const double sin_dphi = std::sin(dphi / 2.0);
    const double sin_dlambda = std::sin(dlambda / 2.0);
    const double a = sin_dphi * sin_dphi + std::cos(phi1) * std::cos(phi2) * sin_dlambda * sin_dlambda;
    const double c = 2.0 * std::atan2(std::sqrt(a), std::sqrt(1.0 - a));
    return kEarthRadiusMeters * c;
}

}  // namespace

bool point_in_polygon(double lat, double lng, const Ring &ring) {
    const std::size_t n = ring.size();
    if (n < 3) {
        return false;
    }

    const double x = lng;
    const double y = lat;
    bool inside = false;

    for (std::size_t i = 0; i < n; ++i) {
        const std::size_t j = (i + 1) % n;
        const double ax = ring[i].second;
        const double ay = ring[i].first;
        const double bx = ring[j].second;
        const double by = ring[j].first;

        if (on_segment(x, y, ax, ay, bx, by)) {
            return true;
        }

        if ((ay > y) != (by > y)) {
            const double x_intersect = ax + (y - ay) * (bx - ax) / (by - ay);
            if (x < x_intersect) {
                inside = !inside;
            }
        }
    }

    return inside;
}

std::vector<std::optional<std::string>> batch_assign(
    const std::vector<Point> &points,
    const std::vector<std::pair<std::string, Ring>> &polygons) {
    std::vector<std::optional<std::string>> result;
    result.reserve(points.size());

    for (const auto &pt : points) {
        std::optional<std::string> assigned;
        for (const auto &entry : polygons) {
            if (point_in_polygon(pt.first, pt.second, entry.second)) {
                assigned = entry.first;
                break;
            }
        }
        result.push_back(std::move(assigned));
    }

    return result;
}

std::vector<std::vector<double>> haversine_matrix(
    const std::vector<Point> &points_a, const std::vector<Point> &points_b) {
    std::vector<std::vector<double>> matrix;
    matrix.reserve(points_a.size());

    for (const auto &a : points_a) {
        std::vector<double> row;
        row.reserve(points_b.size());
        for (const auto &b : points_b) {
            row.push_back(haversine_meters(a.first, a.second, b.first, b.second));
        }
        matrix.push_back(std::move(row));
    }

    return matrix;
}

}  // namespace fastgeo
