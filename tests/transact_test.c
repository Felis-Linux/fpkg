#define _GNU_SOURCE
#include <assert.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#define FSTEST_FUNC_
#include <fstest/fstest.h>
#include <libfl/transact.h>

int main ( void ) {
  libfl_transact_t *transact;
  char *temporary_root;
  temporary_root = fstest_init ();

  transact = libfl_transact_init ( temporary_root );

  int foo_fd = libfl_transact_open ( transact, "foo", 755 );
  char foo_data[] = "MyData";

  write ( foo_fd, foo_data, sizeof ( foo_data ) );
  libfl_transact_commit ( transact );
  close ( foo_fd );

  int foodir = open ( temporary_root, O_DIRECTORY );
  foo_fd = openat ( foodir, "foo", O_RDONLY );
  char foo_data_2[ sizeof ( foo_data ) ];
  read ( foo_fd, foo_data_2, sizeof ( foo_data_2 ) );

  assert ( strcmp ( foo_data, foo_data_2 ) == 0 );
  close ( foodir );
  close ( foo_fd );

  free ( temporary_root );
  libfl_transact_destroy ( transact );
}
