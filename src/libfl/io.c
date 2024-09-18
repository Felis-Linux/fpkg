#define _GNU_SOURCE

#include <errno.h>
#include <fcntl.h>
#include <ftw.h>
#include <libfl/io.h>
#include <libfl/misc.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define LIBFL_IO_TMP_PATTERN "/tmp/flXXXXXX"

void libfl_io_tmp_init ( libfl_io_tmp_t *tmp ) {
  char pattern[] = LIBFL_IO_TMP_PATTERN;

  tmp->dir_path = strdup ( mkdtemp ( pattern ) );
  tmp->dir_fd = open ( tmp->dir_path, O_DIRECTORY, S_IRWXU );
}

static int tmp_cleanup_nftwfunc ( const char *file_name, const struct stat *sta,
                                  int file_flags, struct FTW *pftw ) {
  (void)sta;
  (void)pftw;

  if ( file_flags == FTW_D ) {
    if ( rmdir ( file_name ) < 0 ) {
      libfl_io_elog ( "%s removal failed: %s", file_name, strerror ( errno ) );
      g_libfl_errno = FL_ERMDIR;
      return -1;
    }
  } else if ( file_flags == FTW_F || file_flags == FTW_SL ) {
    if ( unlink ( file_name ) < 0 ) {
      libfl_io_elog ( "%s removal failed: %s", file_name, strerror ( errno ) );
      g_libfl_errno = FL_ERMDIR;
      return -1;
    }
  } else {
    libfl_io_elog (
        "unknown filesystem node type of file: %s\n"
        "aborting deletion.\n"
        "if it is important, open an issue regarding this.",
        file_name );
    g_libfl_errno = FL_ERMDIR;
    return -1;
  }

  return 0;
}

#define NFTW_MAX_DESCRIPTORS 64

void libfl_io_tmp_cleanup ( libfl_io_tmp_t *tmp ) {
  nftw ( tmp->dir_path, tmp_cleanup_nftwfunc, NFTW_MAX_DESCRIPTORS, FTW_DEPTH );
  free ( tmp->dir_path );
  close ( tmp->dir_fd );
}
