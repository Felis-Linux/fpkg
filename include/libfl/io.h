#ifndef LIBFL_IO_H_
#define LIBFL_IO_H_

#include <stdio.h>

/** @def libfl_io_log
 *  @param fmt the format of the log
 *  @brief logs into STDOUT
 */
#define libfl_io_log( fmt, ... )                                          \
  do {                                                                    \
    printf ( "libfl::%s: " #fmt "\n", __PRETTY_FUNCTION__, __VA_ARGS__ ); \
  } while ( 0 )

/** @def libfl_io_elog
 *  @param fmt the frmat of the log
 *  @brief logs into STDERR
 */
#define libfl_io_elog( fmt, ... )                                         \
  do {                                                                    \
    (void)fprintf ( stderr, "libfl::%s: " #fmt "\n", __PRETTY_FUNCTION__, \
                    __VA_ARGS__ );                                        \
  } while ( 0 )

typedef struct libfl_io_tmp libfl_io_tmp_t;
/** @struct libfl_io_tmp
 *  @brief the temporary directory context
 */
struct libfl_io_tmp {
  char *dir_path;
  int dir_fd;
};

/** @fn libfl_io_tmp_init
 *  @param tmp
 *  @brief initializes libl_io_tmp_init, albeit doesnt call malloc
 */
void libfl_io_tmp_init ( libfl_io_tmp_t *tmp );

/** @fn libfl_io_tmp_cleanup
 *  @param tmp
 *  @brief cleans up a libfl_io_tmp_cleanup, albeit doesnt call free
 */
void libfl_io_tmp_cleanup ( libfl_io_tmp_t *tmp );

#endif
