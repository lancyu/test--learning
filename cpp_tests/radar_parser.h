#ifndef RADAR_PARSER_H
#define RADAR_PARSER_H

#include <string>
#include <vector>
#include <stdexcept>

struct RadarPoint {
    double angle;
    double distance;
    int intensity;
};

std::vector<RadarPoint> parseRadar(const std::string& data);

// 新增：严格解析，非法数据抛异常
RadarPoint parseRadarStrict(const std::string& data);

#endif