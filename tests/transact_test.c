#define _GNU_SOURCE
#include <assert.h>
#include <fcntl.h>
#include <libfl/context.h>
#include <libfl/transact.h>
#include <string.h>
#include <unistd.h>

int main ( void ) {
  libfl_init ( "./" );
  libfl_transact_t *transact = libfl_transact_init ();

  int foo_fd = libfl_transact_open ( transact, "foo", 755 );
  char foo_data[] = "MyData";

  write ( foo_fd, foo_data, sizeof ( foo_data ) );
  libfl_transact_commit ( transact );
  close ( foo_fd );

  foo_fd = open ( "foo", O_RDONLY );
  char foo_data_2[ sizeof ( foo_data ) ];
  read ( foo_fd, foo_data_2, sizeof ( foo_data_2 ) );

  assert ( strcmp ( foo_data, foo_data_2 ) == 0 );
  close ( foo_fd );

  libfl_transact_destroy ( transact );
  libfl_destroy ();
}
