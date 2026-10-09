#include "radar_parser.h"
#include <sstream>

std::vector<RadarPoint> parseRadar(const std::string& data) {
    std::vector<RadarPoint> points;
    if (data.empty()) return points;

    //切分，c++标准库没有split，用getline和stringstream来模拟
    std::stringstream ss(data);
    std::string seg;
    while (std::getline(ss, seg, ';')) {
        if (seg.empty()) continue;

        //对每一段再按逗号切分。
        std::stringstream segss(seg);
        std::string field;
        std::vector<std::string> fields;
        while (std::getline(segss, field, ',')) {
            fields.push_back(field);
        }
        if (fields.size() != 3) continue;

        try {
            RadarPoint p;
            p.angle = std::stod(fields[0]);
            p.distance = std::stod(fields[1]);
            p.intensity = std::stoi(fields[2]);

            if (p.angle < 0 || p.angle > 360) continue;
            if (p.distance < 0) continue;
            if (p.intensity < 0 || p.intensity > 255) continue;

            points.push_back(p);
        } catch (...) {
            continue;
        }
    }
    return points;
}
RadarPoint parseRadarStrict(const std::string& data) {
    if (data.empty()) {
        throw std::invalid_argument("empty data");
    }

    std::stringstream ss(data);
    std::string field;
    std::vector<std::string> fields;
    while (std::getline(ss, field, ',')) {
        fields.push_back(field);
    }

    if (fields.size() != 3) {
        throw std::invalid_argument("field count != 3");
    }

    RadarPoint p;
    try {
        p.angle = std::stod(fields[0]);
        p.distance = std::stod(fields[1]);
        p.intensity = std::stoi(fields[2]);
    } catch (...) {
        throw std::invalid_argument("non-numeric field");
    }

    if (p.angle < 0 || p.angle > 360) {
        throw std::out_of_range("angle out of range");
    }
    if (p.distance < 0) {
        throw std::out_of_range("distance negative");
    }
    if (p.intensity < 0 || p.intensity > 255) {
        throw std::out_of_range("intensity out of range");
    }

    return p;
}