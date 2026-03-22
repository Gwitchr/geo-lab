// pybind11 bindings exposing the fastgeo C++17 module. API and semantics
// must match pipeline/native/fallback/fastgeo_py.py exactly -- see
// pipeline/tests/test_parity.py.
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <string>
#include <utility>
#include <vector>

#include "fastgeo/geo.hpp"
#include "fastgeo/simhash.hpp"

namespace py = pybind11;

PYBIND11_MODULE(fastgeo, m) {
    m.doc() = "geo-lab fastgeo: C++17 spatial hot path (point-in-polygon, "
              "batch assignment, haversine, simhash) via pybind11. Pure-Python "
              "reference/spec: pipeline/native/fallback/fastgeo_py.py";

    m.def("point_in_polygon", &fastgeo::point_in_polygon, py::arg("lat"), py::arg("lng"),
          py::arg("ring"),
          "Ray-casting point-in-polygon test; boundary points count as inside.");

    m.def(
        "batch_assign",
        [](const std::vector<fastgeo::Point> &points, const py::dict &polygons) {
            // Convert to an order-preserving vector: iterating a py::dict
            // walks it in CPython insertion order, matching the Python
            // reference implementation's semantics for "first polygon that
            // contains the point".
            std::vector<std::pair<std::string, fastgeo::Ring>> ordered;
            ordered.reserve(polygons.size());
            for (const auto &item : polygons) {
                ordered.emplace_back(py::cast<std::string>(item.first),
                                      py::cast<fastgeo::Ring>(item.second));
            }

            const auto result = fastgeo::batch_assign(points, ordered);

            py::list out;
            for (const auto &assigned : result) {
                if (assigned.has_value()) {
                    out.append(*assigned);
                } else {
                    out.append(py::none());
                }
            }
            return out;
        },
        py::arg("points"), py::arg("polygons"),
        "Assign each point to the first polygon (dict insertion order) containing it, "
        "or None.");

    m.def("haversine_matrix", &fastgeo::haversine_matrix, py::arg("points_a"), py::arg("points_b"),
          "Pairwise great-circle distances (meters) between two point sets.");

    m.def("simhash64", &fastgeo::simhash64, py::arg("text"),
          "64-bit simhash fingerprint of text.");

    m.def("hamming", &fastgeo::hamming, py::arg("a"), py::arg("b"),
          "Hamming distance between two values, treated as 64-bit unsigned.");
}
