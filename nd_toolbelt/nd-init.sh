_ndtoolbelt_autocomplete_find_matches() {
    # Returns commands that start with nd-<namespace>. Excludes aliases and functions
    # Parses and removes subnamespaces in the autocompletion results
    local output=( $({
            compgen -c "$1$2" | sort -u;
            compgen -abk -A function "$1$2";
            } | sort | uniq -u | sed -e s/"$NAMESPACE_PREFIX"// -e s/~.*$//) )
    echo "${output[@]}"
}


_ndtoolbelt_autocomplete_hook() {
    local CURRENT_WORD=${COMP_WORDS[$COMP_CWORD]}

    local NAMESPACES=()
    # Gather the namespace arguments into an array. Ignores the current word and the first "help"
    local help_found="false"
    for arg in "${COMP_WORDS[@]:1:$(($COMP_CWORD - 1))}"; do
        if [[ "$arg" != "help" ]] || [[ "$help_found" == "true" ]]; then
            NAMESPACES+=("$arg")
        elif [[ "$arg" == "help" ]]; then
            help_found="true"
        fi
    done

    if [ -z "$NAMESPACES" ]; then
        local NAMESPACE_PREFIX="nd-"
    else
        # Joins the NAMESPACES array with trailing tildas to gather the current namespace
        local NAMESPACE_PREFIX="nd-$(printf "%s~" "${NAMESPACES[@]}")"
    fi

    COMPREPLY=($(_ndtoolbelt_autocomplete_find_matches "$NAMESPACE_PREFIX" "$CURRENT_WORD"))

    # Add in help as an autocomplete option if current word has been started and matches 'help'
    if [[ "$help_found" == "false" ]] && [[ -n "$CURRENT_WORD" ]] && [[ "help" == *"$CURRENT_WORD"* ]]; then
        # Check to see if we have completed a namespace prior to 'help'
        if [[ -n $(_ndtoolbelt_autocomplete_find_matches "$NAMESPACE_PREFIX") ]]; then
            COMPREPLY+=("help")
        fi
    fi
}

complete -F _ndtoolbelt_autocomplete_hook nd
