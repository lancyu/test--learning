#include <gtest/gtest.h>
#include "radar_parser.h"

TEST(RadarParser, NormalSingle) {
    auto points = parseRadar("45.0,100.5,200");
    ASSERT_EQ(points.size(), 1);
    EXPECT_DOUBLE_EQ(points[0].angle, 45.0);
    EXPECT_DOUBLE_EQ(points[0].distance, 100.5);
    EXPECT_EQ(points[0].intensity, 200);
}

TEST(RadarParser, NormalMultiple) {
    auto points = parseRadar("45.0,100.5,200;90.0,50.0,100");
    ASSERT_EQ(points.size(), 2);
    EXPECT_DOUBLE_EQ(points[1].angle, 90.0);
}

TEST(RadarParser, Empty) {
    EXPECT_TRUE(parseRadar("").empty());
}

TEST(RadarParser, MalformedFieldCount) {
    EXPECT_TRUE(parseRadar("45.0,100.5").empty());
}

TEST(RadarParser, NonNumeric) {
    EXPECT_TRUE(parseRadar("abc,100,200").empty());
}

TEST(RadarParser, BoundaryMin) {
    auto points = parseRadar("0,0,0");
    ASSERT_EQ(points.size(), 1);
}

TEST(RadarParser, BoundaryMax) {
    auto points = parseRadar("360,100,255");
    ASSERT_EQ(points.size(), 1);
}

TEST(RadarParser, AngleOutOfRange) {
    EXPECT_TRUE(parseRadar("361,100,200").empty());
    EXPECT_TRUE(parseRadar("-1,100,200").empty());
}

TEST(RadarParser, DistanceNegative) {
    EXPECT_TRUE(parseRadar("45,-5,200").empty());
}

TEST(RadarParser, IntensityOutOfRange) {
    EXPECT_TRUE(parseRadar("45,100,256").empty());
    EXPECT_TRUE(parseRadar("45,100,-1").empty());
}

TEST(RadarParser, ExtraSemicolons) {
    auto points = parseRadar("45,100,200;;90,50,100");
    ASSERT_EQ(points.size(), 2);
}
TEST(RadarParserStrict, EmptyThrows) {
    EXPECT_THROW(parseRadarStrict(""), std::invalid_argument);
}

TEST(RadarParserStrict, FieldCountThrows) {
    EXPECT_THROW(parseRadarStrict("45.0,100.5"), std::invalid_argument);
}

TEST(RadarParserStrict, NonNumericThrows) {
    EXPECT_THROW(parseRadarStrict("abc,100,200"), std::invalid_argument);
}

TEST(RadarParserStrict, AngleOutOfRangeThrows) {
    EXPECT_THROW(parseRadarStrict("361,100,200"), std::out_of_range);
}

TEST(RadarParserStrict, NormalOk) {
    EXPECT_NO_THROW(parseRadarStrict("45.0,100.5,200"));
}
// 定义一个 fixture 类
class RadarParserTest : public ::testing::Test {
protected:
    // 每个测试前自动调用
    void SetUp() override {
        normalData = "45.0,100.5,200";
        multiData = "45.0,100.5,200;90.0,50.0,100";
        emptyData = "";
    }

    // 每个测试后自动调用
    void TearDown() override {
        // 清理资源，这里没有，留空
    }

    // 成员变量，所有测试都能用
    std::string normalData;
    std::string multiData;
    std::string emptyData;
};

// 用 TEST_F 而不是 TEST
TEST_F(RadarParserTest, NormalSingle) {
    auto points = parseRadar(normalData);
    ASSERT_EQ(points.size(), 1);
    EXPECT_DOUBLE_EQ(points[0].angle, 45.0);
}

TEST_F(RadarParserTest, NormalMultiple) {
    auto points = parseRadar(multiData);
    ASSERT_EQ(points.size(), 2);
}

TEST_F(RadarParserTest, Empty) {
    EXPECT_TRUE(parseRadar(emptyData).empty());
}
// 1. 定义参数化 fixture 类
class RadarParserParamTest
    : public ::testing::TestWithParam<std::tuple<std::string, int>> {
};

// 2. 写测试逻辑，用 GetParam() 拿参数
TEST_P(RadarParserParamTest, ExpectedCount) {
    auto [data, expectedCount] = GetParam();   // C++17 结构化绑定
    auto points = parseRadar(data);
    EXPECT_EQ(static_cast<int>(points.size()), expectedCount);
}

// 3. 实例化，提供多组数据
INSTANTIATE_TEST_SUITE_P(
    BoundaryValues,
    RadarParserParamTest,
    ::testing::Values(
        std::make_tuple("0,0,0", 1),           // 边界最小
        std::make_tuple("360,100,255", 1),     // 边界最大
        std::make_tuple("361,100,200", 0),     // 角度越界
        std::make_tuple("-1,100,200", 0),      // 角度负数
        std::make_tuple("45,-5,200", 0),       // 距离负数
        std::make_tuple("45,100,256", 0),      // 强度越界
        std::make_tuple("45,100,-1", 0),       // 强度负数
        //std::make_tuple("45, 100, 200", 0)     // 带空格，解析失败
        std::make_tuple("45, 100, 200", 1)
    )
);