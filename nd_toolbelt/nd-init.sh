_ndtoolbelt_autocomplete_hook()
{
    local cur=${COMP_WORDS[COMP_CWORD]}
    COMPREPLY=( $(compgen -c nd-$cur | sed s/nd-//) )
}
complete -F _ndtoolbelt_autocomplete_hook nd
