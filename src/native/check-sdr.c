#include <stdio.h>
#include <string.h>
#include <rtl-sdr.h>

/* Enumerate only: never claim a receiver or change its tuning. */
int main(int argc, char **argv)
{
    uint32_t count = rtlsdr_get_device_count();
    if (argc == 2 && strcmp(argv[1], "--count") == 0) {
        printf("%u\n", count);
        return 0;
    }
    printf("RTL-SDR receivers found: %u\n", count);
    for (uint32_t i = 0; i < count; i++)
        printf("  %u: %s\n", i, rtlsdr_get_device_name(i));
    return 0;
}
