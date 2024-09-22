#ifndef LIBFL_CONTEXT_H_
#define LIBFL_CONTEXT_H_

#include <libfl/types.h>
#include <sys/types.h>

/** @var g_libfl_effective_uid
 *  @brief the effective uid grabbed at libfl_init time
 */
extern uid_t g_libfl_effective_uid;
/** @var g_libfl_effective_gid
 *  @brief the effective gid grabbed at libfl_init time
 */
extern uid_t g_libfl_effective_gid;
/** @var g_libfl_effective_root
 *  @brief the effective root set at libfl_init time
 */
extern char *g_libfl_effective_root;
/** @var g_libfl_errno
 *  @brief the libfl errno
 */
extern libfl_errno_t g_libfl_errno;

/** @fn libfl_init
 *  @param effective_root the effective root, initialized externally
 *  @brief intializes the whole libfl context
 *  @return 0 on success, -1 on error
 */
int libfl_init ( const char *effective_root );

/** @fn libfl_destroy
 *  @brief destroys the whole libfl context
 */
void libfl_destroy ();
#endif
