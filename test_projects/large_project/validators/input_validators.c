#include <string.h>
#include <ctype.h>
#include <stdlib.h>
#include <stdio.h>

// Input validation functions - 15 functions
int is_valid_name(const char* name) {
    if (!name) return 0;

    int len = strlen(name);
    if (len < 2 || len > 50) return 0;

    for (int i = 0; i < len; i++) {
        if (!isalpha(name[i]) && name[i] != ' ' && name[i] != '-' && name[i] != '\'') {
            return 0;
        }
    }

    return 1;
}

int is_valid_password(const char* password) {
    if (!password) return 0;

    int len = strlen(password);
    if (len < 8 || len > 128) return 0;

    int has_upper = 0, has_lower = 0, has_digit = 0, has_special = 0;

    for (int i = 0; i < len; i++) {
        if (isupper(password[i])) has_upper = 1;
        else if (islower(password[i])) has_lower = 1;
        else if (isdigit(password[i])) has_digit = 1;
        else if (strchr("!@#$%^&*()_+-=[]{}|;:,.<>?", password[i])) has_special = 1;
    }

    return has_upper && has_lower && has_digit && has_special;
}

int is_valid_credit_card(const char* card) {
    if (!card) return 0;

    int len = strlen(card);
    if (len < 13 || len > 19) return 0;

    int sum = 0;
    int double_digit = 0;

    for (int i = len - 1; i >= 0; i--) {
        if (!isdigit(card[i])) return 0;

        int digit = card[i] - '0';

        if (double_digit) {
            digit *= 2;
            if (digit > 9) digit = digit / 10 + digit % 10;
        }

        sum += digit;
        double_digit = !double_digit;
    }

    return sum % 10 == 0;
}

int is_valid_date(const char* date) {
    if (!date) return 0;

    int year, month, day;
    if (sscanf(date, "%d-%d-%d", &year, &month, &day) != 3) return 0;

    if (year < 1900 || year > 2100) return 0;
    if (month < 1 || month > 12) return 0;

    int days_in_month[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};

    // Leap year check
    if ((year % 400 == 0) || (year % 100 != 0 && year % 4 == 0)) {
        days_in_month[1] = 29;
    }

    return day >= 1 && day <= days_in_month[month - 1];
}

int is_valid_ip_address(const char* ip) {
    if (!ip) return 0;

    int octets[4];
    int count = sscanf(ip, "%d.%d.%d.%d", &octets[0], &octets[1], &octets[2], &octets[3]);

    if (count != 4) return 0;

    for (int i = 0; i < 4; i++) {
        if (octets[i] < 0 || octets[i] > 255) return 0;
    }

    return 1;
}

int is_valid_port(int port) {
    return port >= 1 && port <= 65535;
}

int is_valid_username(const char* username) {
    if (!username) return 0;

    int len = strlen(username);
    if (len < 3 || len > 20) return 0;

    if (!isalpha(username[0])) return 0;

    for (int i = 0; i < len; i++) {
        if (!isalnum(username[i]) && username[i] != '_') return 0;
    }

    return 1;
}

int is_valid_zip_code(const char* zip) {
    if (!zip) return 0;

    int len = strlen(zip);
    if (len != 5 && len != 9) return 0;

    for (int i = 0; i < len; i++) {
        if (!isdigit(zip[i])) return 0;
    }

    return 1;
}

int is_valid_ssn(const char* ssn) {
    if (!ssn) return 0;

    if (strlen(ssn) != 11) return 0;

    for (int i = 0; i < 11; i++) {
        if (i == 3 || i == 6) {
            if (ssn[i] != '-') return 0;
        } else {
            if (!isdigit(ssn[i])) return 0;
        }
    }

    return 1;
}

int is_valid_currency(const char* amount) {
    if (!amount) return 0;

    int len = strlen(amount);
    if (len < 1) return 0;

    int has_decimal = 0;
    int digit_count = 0;

    for (int i = 0; i < len; i++) {
        if (isdigit(amount[i])) {
            digit_count++;
        } else if (amount[i] == '.' && !has_decimal) {
            has_decimal = 1;
        } else if (amount[i] == '$' && i == 0) {
            continue;
        } else {
            return 0;
        }
    }

    return digit_count > 0;
}

int is_valid_percentage(const char* percentage) {
    if (!percentage) return 0;

    int len = strlen(percentage);
    if (len < 2) return 0;

    if (percentage[len - 1] != '%') return 0;

    for (int i = 0; i < len - 1; i++) {
        if (!isdigit(percentage[i]) && percentage[i] != '.') return 0;
    }

    return 1;
}

int is_valid_time(const char* time) {
    if (!time) return 0;

    int hours, minutes;
    if (sscanf(time, "%d:%d", &hours, &minutes) != 2) return 0;

    return hours >= 0 && hours <= 23 && minutes >= 0 && minutes <= 59;
}

int is_valid_hex_string(const char* hex) {
    if (!hex) return 0;

    int len = strlen(hex);
    if (len == 0) return 0;

    for (int i = 0; i < len; i++) {
        if (!isxdigit(hex[i])) return 0;
    }

    return 1;
}

int is_valid_base64(const char* base64) {
    if (!base64) return 0;

    int len = strlen(base64);
    if (len == 0) return 0;

    for (int i = 0; i < len; i++) {
        char c = base64[i];
        if (!isalnum(c) && c != '+' && c != '/' && c != '=') return 0;
    }

    return 1;
}

int is_valid_json_key(const char* key) {
    if (!key) return 0;

    int len = strlen(key);
    if (len == 0) return 0;

    if (key[0] != '"' || key[len - 1] != '"') return 0;

    return 1;
}