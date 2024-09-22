#define _GNU_SOURCE

#include <libfl/context.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

uid_t g_libfl_effective_gid;
uid_t g_libfl_effective_uid;
char *g_libfl_effective_root;
libfl_errno_t g_libfl_errno;

int libfl_init ( const char *effective_root ) {
  g_libfl_effective_root = strdup ( effective_root );
  if ( g_libfl_effective_root == NULL ) {
    return -1;
  }

  g_libfl_effective_uid = geteuid ();
  g_libfl_effective_gid = getegid ();
  return 0;
}

void libfl_destroy () { free ( g_libfl_effective_root ); }
