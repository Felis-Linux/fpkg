#ifndef LIBFL_ERRNO_H_
#define LIBFL_ERRNO_H_

#include <stddef.h>
#include <stdint.h>

#define ATTRIBUTE_MALLOC __attribute__ ( ( malloc ) )
#define ATTRIBUTE_NONNULL( ... ) __attribute__ ( ( nonnull ( __VA_ARGS__ ) ) )

#ifndef LIBFL_REALLOC_MIN
#define LIBFL_REALLOC_MIN 128
#endif

#define LIBFL_STRTOLL_DECIMAL 10

enum {
  FL_EOK = 0,
  FL_EALLOC,
  FL_EMKDIR,
  FL_EOPENDIR,
  FL_ESYMLINK,
  FL_EOPENFILE,
  FL_ESENDFILE,
  FL_ESTAT,
  FL_ERMDIR,
  FL_EMAPTOOBIG,
};

ATTRIBUTE_MALLOC char *smprintf ( char *fmt, ... );
ATTRIBUTE_MALLOC void *memdup ( void *data, size_t len );
ATTRIBUTE_NONNULL ( 2, 4 )
void carand ( size_t template_len, const char template[ template_len ],
              size_t result_len, char result[ result_len ] );
ATTRIBUTE_NONNULL ( 2, 4 )
void randpath ( size_t carand_template_len,
                const char carand_template[ carand_template_len ],
                size_t path_template_len,
                char path_template[ path_template_len ] );
#endif
