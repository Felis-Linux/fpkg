#ifndef LIBFL_TRANSACT_H_
#define LIBFL_TRANSACT_H_

#include <sys/stat.h>

/// \file transact.h

/// \typedef libfl_transact_t
/// \ref libfl_transact
typedef struct libfl_transact libfl_transact_t;

/// \fn libfl_transact_init
/// \param root_path
/// \return the libfl_transact_t
/// \brief Intializes a sane libfl_transact_t, otherwise throws FL_EALLOC,
/// FL_EOPENDIR into g_libfl_errno
libfl_transact_t *libfl_transact_init ( const char *root_path );

/// \fn libfl_transact_recursive_mkdir
/// \param transact the transaction context
/// \param path the path inside the context to make
/// \param permissions the permissions to create the DIRECTORIES with
/// \return -1 if failed, 0 otherwise.
/// \brief this iterates over every '/' and mkdirat's in transact->dir_fd
/// \ref libfl_transact
int libfl_transact_recursive_mkdir ( libfl_transact_t *transact, char *path,
                                     __mode_t permissions );
/// \fn libfl_transact_open
/// \param transact the transact context
/// \param path the path inside the transact context
/// \param premissions the permissions to CREATE the file with
/// \brief returns a file descriptor with the given path
/// \return -1 if failed, a sane fd otherwise.
///
/// This mkdir's the dirname ( dirpath ) and then calls openat in
/// transact->dir_fd
int libfl_transact_open ( libfl_transact_t *transact, char *path,
                          __mode_t permissions );

/// \fn libfl_transact_symlink
/// \param transact the transact context
/// \param from_path the path to base the symlink on
/// \param to_path the target (created symlink) of the symlink
/// \brief This is a thin wrapper around symlinkat
/// \ref libfl_transact_t
/// \return -1 if failed, otherwise 0.
int libfl_transact_symlink ( libfl_transact_t *transact, const char *from_path,
                             const char *to_path );

/// \fn libfl_transact_copy
/// \param transact the transaction context
/// \param file_from the source of the copy
/// \param file_to the destination of the copy
/// \brief calls a static copy method
/// \return -1 if a fail occured, otherwise 0.
int libfl_transact_copy ( libfl_transact_t *transact, const char *file_from,
                          const char *file_to );

// \fn libfl_transact_commit
/// \param transact the transaction context
/// \brief calls commit_directory_iterator
/// \return -1 if failed, 0 otherwise.
/// commit_directory_iterator iterates over the transact *dir* and tries to copy
/// everything.
int libfl_transact_commit ( libfl_transact_t *transact );

/// \fn libfl_transact_destroy
/// \param transact the transaction context
/// \brief Destroys the transaction context and attempts to cleanup the
/// filesystem footprint.
void libfl_transact_destroy ( libfl_transact_t *transact );

#endif
