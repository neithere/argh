#!/bin/sh
#
# Command completion for bash shell. Works with any Python script as long as
# it uses Argh as CLI dispatcher. Note that you need to specify the script
# name. It won't work with just some random file.
#
# Put this to your .bashrc:
#
#     source /path/to/argh_completion.bash
#     complete -F _argh_completion PROG
#
# ...where PROG should be your script name (e.g. "manage.py").
#
_argh_completion()
{
    COMPREPLY=( $( COMP_WORDS="${COMP_WORDS[*]}" \
                   COMP_CWORD=$COMP_CWORD \
                   ARGH_AUTO_COMPLETE=1 $1 ) )
}
