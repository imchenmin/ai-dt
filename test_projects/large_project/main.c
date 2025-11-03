#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <ctype.h>

// Forward declarations for all functions
int add(int a, int b);
int is_prime(int n);
int string_length(const char* str);
int string_contains(const char* haystack, const char* needle);
int bubble_sort(int* arr, int size);
double distance_between_points(double x1, double y1, double x2, double y2);
int is_valid_email(const char* email);
int is_valid_name(const char* name);
char* int_to_string(int value);

int main() {
    printf("Large C Project with 100+ Functions\n");
    printf("==================================\n");

    // Test some functions from each module
    printf("Math: 2 + 3 = %d\n", add(2, 3));
    printf("Math: Prime(17) = %d\n", is_prime(17));

    printf("String: Length of 'hello' = %d\n", string_length("hello"));
    printf("String: 'test' contains 'es' = %d\n", string_contains("test", "es"));

    int arr[] = {5, 2, 8, 1, 9};
    bubble_sort(arr, 5);
    printf("Algorithms: Sorted array[0] = %d\n", arr[0]);

    printf("Graphics: Distance between (0,0) and (3,4) = %.2f\n", distance_between_points(0, 0, 3, 4));

    printf("Parsers: Valid email 'test@example.com' = %d\n", is_valid_email("test@example.com"));
    printf("Validators: Valid name 'John Doe' = %d\n", is_valid_name("John Doe"));

    char* num_str = int_to_string(123);
    printf("Converters: 123 to string = %s\n", num_str);
    free(num_str);

    printf("\nProject loaded successfully with multiple modules!\n");
    return 0;
}