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

#endif
