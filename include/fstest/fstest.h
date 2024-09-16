#ifndef FSTEST_H_
#define FSTEST_H_

#define _GNU_SOURCE
#include <stdlib.h>

#ifndef fstest_strdup
#include <string.h>
#define fstest_strdup(s) strdup ( s )
#endif

char *fstest_init( void );

#ifdef FSTEST_FUNC_
char *fstest_init ( void ) {
  char tmp_template[] = "/tmp/flXXXXXX";
  char *tmp = fstest_strdup ( mkdtemp ( tmp_template ) ); 
  return tmp;
}
#endif

#endif
