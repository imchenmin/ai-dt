#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdio.h>

// Data parsing functions - 15 functions
int parse_integer(const char* str, int* result) {
    if (!str || !result) return 0;

    int i = 0;
    int sign = 1;
    int value = 0;

    // Skip whitespace
    while (isspace(str[i])) i++;

    // Handle sign
    if (str[i] == '-') {
        sign = -1;
        i++;
    } else if (str[i] == '+') {
        i++;
    }

    // Parse digits
    if (!isdigit(str[i])) return 0;

    while (isdigit(str[i])) {
        value = value * 10 + (str[i] - '0');
        i++;
    }

    *result = sign * value;
    return 1;
}

int parse_float(const char* str, float* result) {
    if (!str || !result) return 0;
    char* endptr;
    *result = strtof(str, &endptr);
    return endptr != str;
}

int parse_boolean(const char* str, int* result) {
    if (!str || !result) return 0;

    if (strcmp(str, "true") == 0 || strcmp(str, "1") == 0) {
        *result = 1;
        return 1;
    }
    if (strcmp(str, "false") == 0 || strcmp(str, "0") == 0) {
        *result = 0;
        return 1;
    }
    return 0;
}

int parse_csv_line(const char* line, char** fields, int max_fields) {
    if (!line || !fields || max_fields <= 0) return 0;

    int field_count = 0;
    int in_quotes = 0;
    int start = 0;
    int len = strlen(line);

    for (int i = 0; i <= len && field_count < max_fields; i++) {
        if ((i == len || line[i] == ',') && !in_quotes) {
            int field_len = i - start;
            fields[field_count] = (char*)malloc(field_len + 1);
            if (!fields[field_count]) return field_count;

            strncpy(fields[field_count], line + start, field_len);
            fields[field_count][field_len] = '\0';

            field_count++;
            start = i + 1;
        } else if (line[i] == '"') {
            in_quotes = !in_quotes;
        }
    }

    return field_count;
}

int is_valid_email(const char* email) {
    if (!email) return 0;

    int has_at = 0;
    int has_dot = 0;
    int len = strlen(email);

    for (int i = 0; i < len; i++) {
        if (email[i] == '@') has_at = 1;
        if (has_at && email[i] == '.') has_dot = 1;
    }

    return has_at && has_dot && len > 5;
}

int is_valid_phone(const char* phone) {
    if (!phone) return 0;

    int digits = 0;
    for (int i = 0; phone[i] != '\0'; i++) {
        if (isdigit(phone[i])) digits++;
        else if (phone[i] != '-' && phone[i] != '(' && phone[i] != ')' && phone[i] != ' ') {
            return 0;
        }
    }

    return digits >= 10;
}

int is_valid_url(const char* url) {
    if (!url) return 0;

    return (strncmp(url, "http://", 7) == 0 ||
            strncmp(url, "https://", 8) == 0 ||
            strncmp(url, "ftp://", 6) == 0);
}

char* trim_whitespace(const char* str) {
    if (!str) return NULL;

    int start = 0, end = strlen(str) - 1;
    while (start <= end && isspace(str[start])) start++;
    while (end >= start && isspace(str[end])) end--;

    int len = end - start + 1;
    char* trimmed = (char*)malloc(len + 1);
    if (!trimmed) return NULL;

    strncpy(trimmed, str + start, len);
    trimmed[len] = '\0';
    return trimmed;
}

int count_words(const char* text) {
    if (!text) return 0;

    int count = 0;
    int in_word = 0;

    for (int i = 0; text[i] != '\0'; i++) {
        if (!isspace(text[i])) {
            if (!in_word) {
                count++;
                in_word = 1;
            }
        } else {
            in_word = 0;
        }
    }

    return count;
}

char* extract_filename(const char* path) {
    if (!path) return NULL;

    int len = strlen(path);
    int last_slash = len;

    for (int i = len - 1; i >= 0; i--) {
        if (path[i] == '/' || path[i] == '\\') {
            last_slash = i + 1;
            break;
        }
    }

    int filename_len = len - last_slash;
    char* filename = (char*)malloc(filename_len + 1);
    if (!filename) return NULL;

    strncpy(filename, path + last_slash, filename_len);
    filename[filename_len] = '\0';
    return filename;
}

int is_numeric(const char* str) {
    if (!str) return 0;

    int i = 0;
    while (isspace(str[i])) i++;

    if (str[i] == '-' || str[i] == '+') i++;

    int has_digits = 0;
    while (isdigit(str[i])) {
        has_digits = 1;
        i++;
    }

    if (str[i] == '.') {
        i++;
        while (isdigit(str[i])) {
            has_digits = 1;
            i++;
        }
    }

    return has_digits && str[i] == '\0';
}

char* capitalize_words(const char* str) {
    if (!str) return NULL;

    int len = strlen(str);
    char* result = (char*)malloc(len + 1);
    if (!result) return NULL;

    int capitalize_next = 1;
    for (int i = 0; i <= len; i++) {
        if (i == len || isspace(str[i])) {
            capitalize_next = 1;
            result[i] = str[i];
        } else if (capitalize_next && isalpha(str[i])) {
            result[i] = toupper(str[i]);
            capitalize_next = 0;
        } else {
            result[i] = tolower(str[i]);
            capitalize_next = 0;
        }
    }

    return result;
}

int parse_hex_color(const char* hex, int* r, int* g, int* b) {
    if (!hex || !r || !g || !b) return 0;

    if (hex[0] != '#') return 0;
    if (strlen(hex) != 7) return 0;

    for (int i = 1; i < 7; i++) {
        if (!isxdigit(hex[i])) return 0;
    }

    sscanf(hex + 1, "%02x%02x%02x", r, g, b);
    return 1;
}