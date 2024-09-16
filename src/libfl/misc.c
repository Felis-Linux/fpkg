#include <libfl/misc.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

libfl_errno_t g_libfl_errno;

ATTRIBUTE_MALLOC char *smprintf ( char *fmt, ... ) {
  va_list args;
  va_start ( args, fmt );
  int len = ( vsnprintf ( NULL, 0, fmt, args ) ) + 1;
  va_end ( args );
  va_start ( args, fmt );
  char *buf = malloc ( sizeof ( char ) * len );
  if ( buf == NULL ) {
    g_libfl_errno = FL_EALLOC;
    return NULL;
  }
  if ( vsnprintf ( buf, len, fmt, args ) < 0 ) {
    g_libfl_errno = FL_EALLOC;
    return NULL;
  }

  va_end ( args );
  return buf;
}
