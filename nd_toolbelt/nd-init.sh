_ndtoolbelt_autocomplete_hook() {
    local CURRENT_WORD=${COMP_WORDS[$COMP_CWORD]}

    local NAMESPACES=()
    # Gather the namespace arguments into an array. Ignores the current word and args named 'help'.
    for arg in "${COMP_WORDS[@]:1:$(($COMP_CWORD - 1))}"; do
        if [[ "$arg" != "help" ]]; then
            NAMESPACES[${#NAMESPACES[*]}]="$arg" # Append arg to end of NAMESPACE_ARRAY
        fi
    done

    if [ -z "$NAMESPACES" ]; then
        local NAMESPACE_PREFIX="nd-"
    else
        # Joins the NAMESPACES array with trailing tildas to gather the current namespace
        local NAMESPACE_PREFIX="nd-$(printf "%s~" "${NAMESPACES[@]}")"
    fi

    # Returns commands that start with nd-<namespace>. Excludes aliases and functions
    # Parses and removes subnamespaces in the autocompletion results
    COMPREPLY=( $({
            compgen -c "$NAMESPACE_PREFIX$CURRENT_WORD" | sort -u;
            compgen -abk -A function "$NAMESPACE_PREFIX$CURRENT_WORD";
            } | sort | uniq -u | sed -e s/"$NAMESPACE_PREFIX"// -e s/~.*$//) )
}

complete -F _ndtoolbelt_autocomplete_hook nd
