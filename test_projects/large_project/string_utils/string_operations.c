#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include <stdio.h>

// String utility functions - 15 functions
int string_length(const char* str) {
    if (!str) return 0;
    int length = 0;
    while (str[length] != '\0') {
        length++;
    }
    return length;
}

char* string_copy(const char* src) {
    if (!src) return NULL;
    int length = string_length(src);
    char* dest = (char*)malloc(length + 1);
    if (!dest) return NULL;
    for (int i = 0; i <= length; i++) {
        dest[i] = src[i];
    }
    return dest;
}

int string_compare(const char* str1, const char* str2) {
    if (!str1 || !str2) return -1;
    int i = 0;
    while (str1[i] != '\0' && str2[i] != '\0') {
        if (str1[i] != str2[i]) {
            return str1[i] - str2[i];
        }
        i++;
    }
    return str1[i] - str2[i];
}

char* string_concat(const char* str1, const char* str2) {
    if (!str1 || !str2) return NULL;
    int len1 = string_length(str1);
    int len2 = string_length(str2);
    char* result = (char*)malloc(len1 + len2 + 1);
    if (!result) return NULL;

    for (int i = 0; i < len1; i++) {
        result[i] = str1[i];
    }
    for (int i = 0; i <= len2; i++) {
        result[len1 + i] = str2[i];
    }
    return result;
}

int string_contains(const char* haystack, const char* needle) {
    if (!haystack || !needle) return 0;
    int hay_len = string_length(haystack);
    int needle_len = string_length(needle);

    if (needle_len > hay_len) return 0;

    for (int i = 0; i <= hay_len - needle_len; i++) {
        int match = 1;
        for (int j = 0; j < needle_len; j++) {
            if (haystack[i + j] != needle[j]) {
                match = 0;
                break;
            }
        }
        if (match) return 1;
    }
    return 0;
}

char* string_reverse(const char* str) {
    if (!str) return NULL;
    int length = string_length(str);
    char* reversed = (char*)malloc(length + 1);
    if (!reversed) return NULL;

    for (int i = 0; i < length; i++) {
        reversed[i] = str[length - 1 - i];
    }
    reversed[length] = '\0';
    return reversed;
}

char* string_to_upper(const char* str) {
    if (!str) return NULL;
    int length = string_length(str);
    char* upper = (char*)malloc(length + 1);
    if (!upper) return NULL;

    for (int i = 0; i <= length; i++) {
        upper[i] = toupper(str[i]);
    }
    return upper;
}

char* string_to_lower(const char* str) {
    if (!str) return NULL;
    int length = string_length(str);
    char* lower = (char*)malloc(length + 1);
    if (!lower) return NULL;

    for (int i = 0; i <= length; i++) {
        lower[i] = tolower(str[i]);
    }
    return lower;
}

int string_is_empty(const char* str) {
    return !str || str[0] == '\0';
}

int string_count_char(const char* str, char ch) {
    if (!str) return 0;
    int count = 0;
    for (int i = 0; str[i] != '\0'; i++) {
        if (str[i] == ch) count++;
    }
    return count;
}

char* string_trim(const char* str) {
    if (!str) return NULL;
    int start = 0, end = string_length(str) - 1;

    while (start <= end && isspace(str[start])) start++;
    while (end >= start && isspace(str[end])) end--;

    int length = end - start + 1;
    char* trimmed = (char*)malloc(length + 1);
    if (!trimmed) return NULL;

    for (int i = 0; i < length; i++) {
        trimmed[i] = str[start + i];
    }
    trimmed[length] = '\0';
    return trimmed;
}

int string_starts_with(const char* str, const char* prefix) {
    if (!str || !prefix) return 0;
    int str_len = string_length(str);
    int prefix_len = string_length(prefix);
    if (prefix_len > str_len) return 0;

    for (int i = 0; i < prefix_len; i++) {
        if (str[i] != prefix[i]) return 0;
    }
    return 1;
}

int string_ends_with(const char* str, const char* suffix) {
    if (!str || !suffix) return 0;
    int str_len = string_length(str);
    int suffix_len = string_length(suffix);
    if (suffix_len > str_len) return 0;

    int start = str_len - suffix_len;
    for (int i = 0; i < suffix_len; i++) {
        if (str[start + i] != suffix[i]) return 0;
    }
    return 1;
}

char* string_substring(const char* str, int start, int length) {
    if (!str || start < 0 || length < 0) return NULL;
    int str_len = string_length(str);
    if (start >= str_len) return NULL;
    if (start + length > str_len) length = str_len - start;

    char* substr = (char*)malloc(length + 1);
    if (!substr) return NULL;

    for (int i = 0; i < length; i++) {
        substr[i] = str[start + i];
    }
    substr[length] = '\0';
    return substr;
}