#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>

// Type conversion functions - 14 functions
char* int_to_string(int value) {
    char* str = (char*)malloc(32);
    if (!str) return NULL;
    sprintf(str, "%d", value);
    return str;
}

char* float_to_string(float value) {
    char* str = (char*)malloc(64);
    if (!str) return NULL;
    sprintf(str, "%.6f", value);
    return str;
}

char* double_to_string(double value) {
    char* str = (char*)malloc(64);
    if (!str) return NULL;
    sprintf(str, "%.15g", value);
    return str;
}

char* bool_to_string(int value) {
    char* str = (char*)malloc(6);
    if (!str) return NULL;
    strcpy(str, value ? "true" : "false");
    return str;
}

int string_to_int(const char* str, int* success) {
    if (!str) {
        if (success) *success = 0;
        return 0;
    }

    char* endptr;
    int result = (int)strtol(str, &endptr, 10);

    if (success) {
        *success = (endptr != str && *endptr == '\0');
    }

    return result;
}

float string_to_float(const char* str, int* success) {
    if (!str) {
        if (success) *success = 0;
        return 0.0f;
    }

    char* endptr;
    float result = strtof(str, &endptr);

    if (success) {
        *success = (endptr != str);
    }

    return result;
}

double string_to_double(const char* str, int* success) {
    if (!str) {
        if (success) *success = 0;
        return 0.0;
    }

    char* endptr;
    double result = strtod(str, &endptr);

    if (success) {
        *success = (endptr != str);
    }

    return result;
}

int string_to_bool(const char* str, int* success) {
    if (!str) {
        if (success) *success = 0;
        return 0;
    }

    int result = 0;
    if (strcmp(str, "true") == 0 || strcmp(str, "1") == 0 ||
        strcmp(str, "yes") == 0 || strcmp(str, "on") == 0) {
        result = 1;
    } else if (strcmp(str, "false") == 0 || strcmp(str, "0") == 0 ||
               strcmp(str, "no") == 0 || strcmp(str, "off") == 0) {
        result = 0;
    } else {
        if (success) *success = 0;
        return 0;
    }

    if (success) *success = 1;
    return result;
}

char* bytes_to_hex(const unsigned char* bytes, int length) {
    if (!bytes || length <= 0) return NULL;

    char* hex = (char*)malloc(length * 2 + 1);
    if (!hex) return NULL;

    for (int i = 0; i < length; i++) {
        sprintf(hex + i * 2, "%02x", bytes[i]);
    }
    hex[length * 2] = '\0';

    return hex;
}

unsigned char* hex_to_bytes(const char* hex, int* out_length) {
    if (!hex || !out_length) return NULL;

    int len = strlen(hex);
    if (len % 2 != 0) {
        *out_length = 0;
        return NULL;
    }

    unsigned char* bytes = (unsigned char*)malloc(len / 2);
    if (!bytes) {
        *out_length = 0;
        return NULL;
    }

    for (int i = 0; i < len; i += 2) {
        unsigned int byte;
        if (sscanf(hex + i, "%2x", &byte) != 1) {
            free(bytes);
            *out_length = 0;
            return NULL;
        }
        bytes[i / 2] = (unsigned char)byte;
    }

    *out_length = len / 2;
    return bytes;
}

char* to_uppercase(const char* str) {
    if (!str) return NULL;

    int len = strlen(str);
    char* result = (char*)malloc(len + 1);
    if (!result) return NULL;

    for (int i = 0; i <= len; i++) {
        result[i] = toupper(str[i]);
    }

    return result;
}

char* to_lowercase(const char* str) {
    if (!str) return NULL;

    int len = strlen(str);
    char* result = (char*)malloc(len + 1);
    if (!result) return NULL;

    for (int i = 0; i <= len; i++) {
        result[i] = tolower(str[i]);
    }

    return result;
}

int celsius_to_fahrenheit(int celsius) {
    return (celsius * 9 / 5) + 32;
}

int fahrenheit_to_celsius(int fahrenheit) {
    return (fahrenheit - 32) * 5 / 9;
}