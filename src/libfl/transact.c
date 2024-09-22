#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <ftw.h>
#include <libfl/context.h>
#include <libfl/io.h>
#include <libfl/misc.h>
#include <libfl/transact.h>
#include <libgen.h>
#include <linux/limits.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <sys/io.h>
#include <sys/sendfile.h>
#include <sys/stat.h>
#include <unistd.h>

/* @file transact.c
   @todo implement a copy from fs function
*/
/// @struct libfl_transact
/// @brief the transaction context
struct libfl_transact {
  /// the root path
  char *root_path;
  /// the root fd
  int root_fd;

  libfl_io_tmp_t tmp;
};

void libfl_transact_destroy ( libfl_transact_t *transact ) {
  libfl_io_tmp_cleanup ( &transact->tmp );
  free ( transact->root_path );
  close ( transact->root_fd );

  free ( transact );
}

libfl_transact_t *libfl_transact_init () {
  libfl_transact_t *transact = malloc ( sizeof ( libfl_transact_t ) );
  if ( transact == NULL ) {
    g_libfl_errno = FL_EALLOC;
    return NULL;
  }
  memset ( transact, 0, sizeof ( libfl_transact_t ) );

  libfl_io_tmp_init ( &transact->tmp );

  transact->root_path = strdup ( g_libfl_effective_root );
  transact->root_fd = open ( transact->root_path, O_DIRECTORY );

  if ( transact->root_fd < 0 ) {
    libfl_transact_destroy ( transact );
    g_libfl_errno = FL_EOPENDIR;
    return NULL;
  }

  return transact;
}

int libfl_transact_recursive_mkdir ( libfl_transact_t *transact, char *path,
                                     mode_t permissions ) {
  char *where = path;
  while ( *where ) {
    if ( *where == '/' ) {
      *where = '\0';
      if ( mkdirat ( transact->tmp.dir_fd, path, permissions ) < 0 &&
           errno != EEXIST ) {
        libfl_io_elog ( "%s directory creation failed: %s", path,
                        strerror ( errno ) );
        g_libfl_errno = FL_EMKDIR;
        return -1;
      }
      *where = '/';
    }
    where++;
  }
  return 0;
}

int libfl_transact_open ( libfl_transact_t *transact, char *path,
                          mode_t permissions ) {
  char *dirpath = strdup ( path );
  libfl_transact_recursive_mkdir (
      transact, dirname ( dirpath ),
      S_IRWXU | S_IRGRP | S_IXGRP | S_IROTH | S_IXOTH );
  free ( dirpath );

  return openat ( transact->tmp.dir_fd, path, O_CREAT | O_RDWR | O_TRUNC,
                  permissions );
}

int libfl_transact_symlink ( libfl_transact_t *transact, const char *from_path,
                             const char *to_path ) {
  if ( symlinkat ( from_path, transact->tmp.dir_fd, to_path ) < 0 ||
       errno != EEXIST ) {
    libfl_io_elog ( "%s -> %s symlinking failed: %s", from_path, to_path,
                    strerror ( errno ) );
    g_libfl_errno = FL_ESYMLINK;
    return -1;
  }
  return 0;
}

static int copy ( int atfd, const char *file1, const char *file2 ) {
  int file1_fd = openat ( atfd, file1, O_RDWR );
  int file2_fd = openat ( atfd, file2, O_RDWR | O_CREAT );

  if ( file1_fd == -1 || file2_fd == -1 ) {
    libfl_io_elog ( "%s -> %s copy failed, %s", file1, file2,
                    strerror ( errno ) );
    g_libfl_errno = FL_EOPENFILE;
    return -1;
  }

  struct stat sta;
  fstat ( file1_fd, &sta );

  if ( chmod ( file2, sta.st_mode ) < 0 ) {
    libfl_io_elog ( "%s -> %s copy failed, %s", file1, file2,
                    strerror ( errno ) );
    g_libfl_errno = FL_EOPENFILE;
    return -1;
  }

  if ( sendfile ( file1_fd, file2_fd, NULL, sta.st_size ) == -1 ) {
    libfl_io_elog ( "%s -> %s copy failed, %s", file1, file2,
                    strerror ( errno ) );
    g_libfl_errno = FL_ESENDFILE;
    return -1;
  }

  close ( file1_fd );
  close ( file2_fd );

  return 0;
}

static int copy_link ( int fromfd, const char *from, int destfd,
                       const char *dest ) {
  char symlink_target[ PATH_MAX ];
  if ( readlinkat ( fromfd, from, symlink_target,
                    sizeof ( symlink_target ) - 1 ) < 0 ) {
    g_libfl_errno = FL_ESYMLINK;
    return -1;
  }

  if ( symlinkat ( symlink_target, destfd, dest ) < 0 ) {
    g_libfl_errno = FL_ESYMLINK;
    return -1;
  }

  return 0;
}

int libfl_transact_copy ( libfl_transact_t *transact, const char *file_from,
                          const char *file_to ) {
  return copy ( transact->tmp.dir_fd, file_from, file_to );
}

static int commit_directory_iterator_file_handler (
    libfl_transact_t *transact, const char *current_directory,
    const char *f_name ) {
  char *current_path = smprintf ( "%s/%s/%s", transact->tmp.dir_path,
                                  current_directory, f_name );
  char *target_path =
      smprintf ( "%s/%s/%s", transact->root_path, current_directory, f_name );

  if ( copy ( transact->tmp.dir_fd, current_path, target_path ) < 0 ) {
    free ( current_path );
    free ( target_path );
    return -1;
  }

  free ( current_path );
  free ( target_path );
  return 0;
}

static int commit_directory_iterator ( libfl_transact_t *transact,
                                       const char *current_directory ) {
  DIR *dir;
  struct dirent *ent;

  char *path = smprintf ( "%s/%s", transact->tmp.dir_path, current_directory );
  if ( ( dir = opendir ( path ) ) == NULL ) {
    g_libfl_errno = FL_EOPENDIR;
    libfl_io_elog ( "%s opening directory failed: %s", current_directory,
                    strerror ( errno ) );
    return -1;
  }

  free ( path );

  while ( ( ent = readdir ( dir ) ) != NULL ) {
    if ( strcmp ( ent->d_name, "." ) == 0 ||
         strcmp ( ent->d_name, ".." ) == 0 ) {
      continue;
    }

    if ( ent->d_type == DT_DIR ) {
      char *new_current_directory =
          smprintf ( "%s/%s", current_directory, ent->d_name );
      if ( commit_directory_iterator ( transact, new_current_directory ) < 0 ) {
        free ( new_current_directory );
        return -1;
      }
      free ( new_current_directory );
    } else if ( ent->d_type == DT_REG ) {
      commit_directory_iterator_file_handler ( transact, current_directory,
                                               ent->d_name );
    } else if ( ent->d_type == DT_LNK ) {
      char *file = smprintf ( "%s/%s", current_directory, ent->d_name );
      if ( copy_link ( transact->tmp.dir_fd, file, transact->root_fd, file ) <
           0 ) {
        g_libfl_errno = FL_ESENDFILE;
        free ( file );
        return -1;
      }
      free ( file );
    } else {
      char *file = smprintf ( "%s/%s", current_directory, ent->d_name );
      libfl_io_log (
          "unknown filesystem node type of file: %s\n"
          "if it is important, open an issue regarding this.",
          file );
      free ( file );
    }
  }

  return 0;
}

int libfl_transact_commit ( libfl_transact_t *transact ) {
  return commit_directory_iterator ( transact, "" );
}
