#ifndef LIBFL_ERRNO_H_
#define LIBFL_ERRNO_H_

#include <stddef.h>
#include <stdint.h>

#define ATTRIBUTE_MALLOC __attribute__((malloc))

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
};

typedef uint64_t libfl_errno_t;

extern libfl_errno_t g_libfl_errno;

ATTRIBUTE_MALLOC char *smprintf ( char *fmt, ... );
#endif
