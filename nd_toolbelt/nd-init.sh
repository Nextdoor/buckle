_ndtoolbelt_autocomplete_hook() {
    local cur=${COMP_WORDS[COMP_CWORD]}
    # Returns commands that start with nd-. Excludes aliases and functions.
    COMPREPLY=( $({ compgen -c nd-$cur; compgen -abk -A function nd-$cur; } | sort | uniq -u | sed s/nd-//) )
}

complete -F _ndtoolbelt_autocomplete_hook nd
