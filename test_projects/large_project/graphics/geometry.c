#include <math.h>
#include <stdlib.h>

typedef struct {
    double x;
    double y;
} Point;

typedef struct {
    Point center;
    double radius;
} Circle;

typedef struct {
    Point p1;
    Point p2;
} Rectangle;

// Geometry functions - 15 functions
Point create_point(double x, double y) {
    Point p = {x, y};
    return p;
}

double distance_between_points(Point p1, Point p2) {
    double dx = p2.x - p1.x;
    double dy = p2.y - p1.y;
    return sqrt(dx * dx + dy * dy);
}

Circle create_circle(Point center, double radius) {
    Circle c = {center, radius};
    return c;
}

int point_in_circle(Point p, Circle c) {
    double distance = distance_between_points(p, c.center);
    return distance <= c.radius;
}

double circle_area(Circle c) {
    return M_PI * c.radius * c.radius;
}

double circle_perimeter(Circle c) {
    return 2 * M_PI * c.radius;
}

Rectangle create_rectangle(Point p1, Point p2) {
    Rectangle r = {p1, p2};
    return r;
}

double rectangle_area(Rectangle r) {
    double width = fabs(r.p2.x - r.p1.x);
    double height = fabs(r.p2.y - r.p1.y);
    return width * height;
}

double rectangle_perimeter(Rectangle r) {
    double width = fabs(r.p2.x - r.p1.x);
    double height = fabs(r.p2.y - r.p1.y);
    return 2 * (width + height);
}

int point_in_rectangle(Point p, Rectangle r) {
    double min_x = r.p1.x < r.p2.x ? r.p1.x : r.p2.x;
    double max_x = r.p1.x > r.p2.x ? r.p1.x : r.p2.x;
    double min_y = r.p1.y < r.p2.y ? r.p1.y : r.p2.y;
    double max_y = r.p1.y > r.p2.y ? r.p1.y : r.p2.y;

    return p.x >= min_x && p.x <= max_x && p.y >= min_y && p.y <= max_y;
}

Point rotate_point(Point p, double angle_rad, Point origin) {
    double cos_angle = cos(angle_rad);
    double sin_angle = sin(angle_rad);

    double x = p.x - origin.x;
    double y = p.y - origin.y;

    double rotated_x = x * cos_angle - y * sin_angle;
    double rotated_y = x * sin_angle + y * cos_angle;

    Point result = {rotated_x + origin.x, rotated_y + origin.y};
    return result;
}

double triangle_area(Point p1, Point p2, Point p3) {
    return fabs((p1.x * (p2.y - p3.y) +
                 p2.x * (p3.y - p1.y) +
                 p3.x * (p1.y - p2.y)) / 2.0);
}

int points_collinear(Point p1, Point p2, Point p3) {
    double area = triangle_area(p1, p2, p3);
    return area < 1e-10;
}

Point point_midpoint(Point p1, Point p2) {
    Point mid = {(p1.x + p2.x) / 2.0, (p1.y + p2.y) / 2.0};
    return mid;
}

double dot_product(Point v1, Point v2) {
    return v1.x * v2.x + v1.y * v2.y;
}