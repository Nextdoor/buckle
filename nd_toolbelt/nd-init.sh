_ndtoolbelt_autocomplete_find_matches() {
    # Sets the variable at $1 to the possible matches for the next word of the command with the
    # prefix specified in $2 and the current partial word in $3.
    local target=$1
    local prefix=$2
    local cword=$3


	local exclude='^$'  # exclude nothing by default
	if [[ -z "$cword" ]]; then
		# When offering completions for a namespace, exclude those starting with '_'
		exclude="^${prefix}[_.].*$"
	fi

    declare -ga "${target}"="( $({
            compgen -c -X "${exclude}" "${prefix}${cword}" | sort -u;
            compgen -abk -A function -X "${exclude}" "${prefix}${cword}";
            } | sort | uniq -u | sed -e s/"${exclude}"// -e s/"${prefix}"// -e s/~.*$//) )"
}


_ndtoolbelt_autocomplete_hook() {
    local cword="${COMP_WORDS[$COMP_CWORD]}"

    # Gather the namespace arguments into an array. Ignores the current word and the first "help"
    local nspath=()
    local help_found=''
	for arg in "${COMP_WORDS[@]:1:$(($COMP_CWORD - 1))}"; do
		if [[ "$arg" != "help" ]] || [[ -n "$help_found" ]]; then
			nspath+=("$arg")
		elif [[ "$arg" = "help" ]]; then
			help_found=1
		fi
	done

	local nsprefix=''
    if [[ ${#nspath[@]} > 0 ]]; then
        # Joins the array with trailing tildes to gather the current namespace path
        printf -v nsprefix "%s~" "${nspath[@]}"
    fi
	nsprefix="nd-$nsprefix"

	_ndtoolbelt_autocomplete_find_matches COMPREPLY "$nsprefix" "$cword"

    # Add in help as an autocomplete option if current word has been started and matches 'help'
    if [[ -z "$help_found" ]] && [[ "help" = "$cword"* ]]; then
        # Check to see if we have completed a namespace prior to 'help'
        _ndtoolbelt_autocomplete_find_matches _ND_TOOLBELT_HELP_MATCHES "$nsprefix"
        if [[ -n $_ND_TOOLBELT_HELP_MATCHES ]]; then
            COMPREPLY+=("help")
        fi
    fi
}

# This idiom follows git bash autocompletion
# https://github.com/git/git/blob/master/contrib/completion/git-completion.bash#L2874
complete -o bashdefault -o default -F _ndtoolbelt_autocomplete_hook nd 2>/dev/null \
    || complete -o default -F _ndtoolbelt_autocomplete_hook nd
