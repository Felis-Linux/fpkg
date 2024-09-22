#define _GNU_SOURCE
#define _POSIX_C_SOURCE 200809L
#include <libfl/context.h>
#include <libfl/misc.h>
#include <libfl/types.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

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

ATTRIBUTE_MALLOC void *memdup ( void *data, size_t len ) {
  byte_t *new_data = malloc ( len );
  if ( new_data == NULL ) {
    return NULL;
  }
  memcpy ( new_data, data, len );
  return new_data;
}

ATTRIBUTE_NONNULL ( 2, 4 )
void carand ( size_t template_len, const char template[ template_len ],
              size_t result_len, char result[ result_len ] ) {
  struct timespec tsp;
  clock_gettime ( CLOCK_REALTIME, &tsp );
  srandom ( tsp.tv_nsec );

  for ( size_t i = 0; i < result_len; ++i ) {
    result[ i ] = template[ random () % template_len ];
  }
}

ATTRIBUTE_NONNULL ( 2, 4 )
void randpath ( size_t carand_template_len,
                const char carand_template[ carand_template_len ],
                size_t path_template_len,
                char path_template[ path_template_len ] ) {
  char *modifier_string = path_template;
  while ( modifier_string ) {
    modifier_string++;
    if ( ( *modifier_string ) == '@' ) {
      break;
    }
  }

  size_t modifier_string_len = strlen ( modifier_string );
  carand ( carand_template_len, carand_template, modifier_string_len,
           modifier_string );
}
