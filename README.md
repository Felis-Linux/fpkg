# Felis GNU+FFL+.../Linux Felis Package Manager
## no, i'm not serious about the naming right now.
### Goals
4th generation fpkg attempts... well, to be the 2nd fpkg, but in c, with some lua support,
and a more... mature? attempt.

the 2nd generation fpkg is in the legacy [fpkg.py](/legacy/fpkg.py), but it shan't be treated as the current fpkg

basically, we use the library<->app model

### commits

commit via a merge request (GitHub calls it a pull request)

### libfl/libffl

why libffl? and not libfl?
flex takes the libfl name already, so, libffl.

### library<->app

libffl, from now referred to as libfl, manages packaging, databases, immutability+imaging capabilities and a downloader context

fpkg{_*} links with libfl, libfl is common code.