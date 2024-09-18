#ifndef LIBFL_IO_H_
#define LIBFL_IO_H_

#include <stdio.h>

#define libfl_io_log(fmt, ...) \
  do { \
    printf ( "libfl::%s: " #fmt "\n" , __PRETTY_FUNCTION__, __VA_ARGS__ ); \
  } while ( 0 )

#define libfl_io_elog(fmt, ...) \
  do { \
    (void)fprintf( stderr, "libfl::%s: " #fmt "\n", __PRETTY_FUNCTION__, __VA_ARGS__ ); \
  } while ( 0 )

typedef struct libfl_io_tmp libfl_io_tmp_t;
struct libfl_io_tmp {
  char *dir_path;
  int dir_fd;
};


void libfl_io_tmp_init ( libfl_io_tmp_t *tmp );
void libfl_io_tmp_cleanup ( libfl_io_tmp_t *tmp );

#endif
