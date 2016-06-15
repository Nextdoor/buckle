_ndtoolbelt_autocomplete_hook() {
    if [[ $COMP_CWORD = 1 || $COMP_CWORD = 2 && "${COMP_WORDS[1]}" == "help" ]]; then
        local current_word=${COMP_WORDS[$COMP_CWORD]}
        # Returns commands that start with nd-. Excludes aliases and functions.
        COMPREPLY=( $({ compgen -c nd-$current_word; compgen -abk -A function nd-$current_word; } | sort | uniq -u | sed s/nd-// ) )
    fi
}

complete -F _ndtoolbelt_autocomplete_hook nd
