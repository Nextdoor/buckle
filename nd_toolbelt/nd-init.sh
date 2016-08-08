_ndtoolbelt_autocomplete_find_matches() {
    # Sets the variable at $1 to the possible matches for the next word of the command with the
    # namespace path indicated in $2 and the current partial word in $3.
    local target=$1
    local path=("${!2}")  # Expand the array reference ("arr[@]") described in $2
    local cword=$3

    local prefix=''
    if [[ ${#path[@]} > 0 ]]; then
        # Joins the array with trailing tildes to gather the current namespace path
        printf -v prefix "%s~" "${path[@]}"
    fi
    prefix="nd-$prefix"

    local exclude=''  # exclude nothing by default
    if [[ -z "$cword" ]]; then
        # When offering completions for a namespace, exclude those starting with '_'
        exclude="${prefix}[_.].*"
    fi

    compgen_args=(-X "*.completion?(.*)" "${prefix}${cword}")
    declare -ga "${target}"="( $({
        shopt -s extglob;
        compgen -c "${compgen_args[@]}" | sort -u;
        compgen -abk -A function "${compgen_args[@]}";
        } | sort | uniq -u | sed -e s/"^${exclude}$"// -e s/"${prefix}"// -e s/~.*$//) )"
}

_ndtoolbelt_autocomplete_command_arg_completions() {
    # Sets the variable at $1 to the possible matches for the next word of the command with the
    # namespace path indicated in $2 and the current partial word in $3.
    local target=$1
    local path=("${!2}")  # Expand the array reference ("arr[@]") described in $2

    # Find and run any completion commands found on the path
    local arg_completions=()
    local nspath=''
    for segment in "${path[@]}"; do
        local command="nd-${nspath}${segment}"
        # Find any completion scripts
        local completion_commands=($(compgen -c "${command}.completion" | sort -u))
        for completion_command in "${completion_commands[@]}"; do
            if [[ $completion_command =~ .(sh|bash)$ ]]; then
                arg_completions+=($(source $completion_command))
            else
                arg_completions+=($(COMP_WORDS="${COMP_WORDS[@]}" COMP_CWORD=$COMP_CWORD \
                                  $completion_command))
            fi
        done
        nspath="${nspath}${segment}~"
    done

    declare -ga "${target}"="(${arg_completions[*]})"
}

_ndtoolbelt_autocomplete_hook() {
    local words_ cword_
    # Sets words_, a version of COMP_WORDS with the input characters as exclusions for word breaks
    # Also sets cword_, the index of the current word in words_
    __nd_reassemble_comp_words_by_ref '=:'

    local current_word="${words_[$cword_]}"

    # Gather the namespace arguments into an array. Ignores the current word and the first "help"
    local nspath=()
    local help_found=''
    for arg in "${words_[@]:1:$(($cword_ - 1))}"; do
        if [[ "$arg" = "help" && -z "$help_found" ]]; then
            help_found=1
        elif [[ ! ("$arg" = "-"* && -z "$nspath") ]]; then  # Ignore toolbelt options
            nspath+=("$arg")
        fi
    done

    _ndtoolbelt_autocomplete_find_matches COMPREPLY nspath[@] "$current_word"

    _ndtoolbelt_autocomplete_command_arg_completions _ND_TOOLBELT_COMMAND_ARG_COMPLETIONS nspath[@]
    COMPREPLY+=("${_ND_TOOLBELT_COMMAND_ARG_COMPLETIONS[@]}")

    # Add in help as an autocomplete option if current word has been started and matches 'help'
    if [[ -z "$help_found" ]] && [[ "help" = "$current_word"* ]]; then
        # Check to see if we have completed a namespace prior to 'help'
        _ndtoolbelt_autocomplete_find_matches _ND_TOOLBELT_HELP_MATCHES nspath[@]
        if [[ -n $_ND_TOOLBELT_HELP_MATCHES ]]; then
            COMPREPLY+=("help")
        fi
    fi
}

# This idiom follows git bash autocompletion
# https://github.com/git/git/blob/master/contrib/completion/git-completion.bash#L2874
complete -o bashdefault -o default -F _ndtoolbelt_autocomplete_hook nd 2>/dev/null \
    || complete -o default -F _ndtoolbelt_autocomplete_hook nd


# This function allows COMP_WORDS autocompletion with the characters passed ignored as word breaks
# Taken from https://github.com/git/git/blob/master/contrib/completion/git-completion.bash#L112
__nd_reassemble_comp_words_by_ref()
{
    local exclude i j first
    # Which word separators to exclude?
    exclude="${1//[^$COMP_WORDBREAKS]}"
    cword_=$COMP_CWORD
    if [ -z "$exclude" ]; then
        words_=("${COMP_WORDS[@]}")
        return
    fi
    # List of word completion separators has shrunk;
    # re-assemble words to complete.
    for ((i=0, j=0; i < ${#COMP_WORDS[@]}; i++, j++)); do
        # Append each nonempty word consisting of just
        # word separator characters to the current word.
        first=t
        while
            [ $i -gt 0 ] &&
            [ -n "${COMP_WORDS[$i]}" ] &&
            # word consists of excluded word separators
            [ "${COMP_WORDS[$i]//[^$exclude]}" = "${COMP_WORDS[$i]}" ]
        do
            # Attach to the previous token,
            # unless the previous token is the command name.
            if [ $j -ge 2 ] && [ -n "$first" ]; then
                ((j--))
            fi
            first=
            words_[$j]=${words_[j]}${COMP_WORDS[i]}
            if [ $i = $COMP_CWORD ]; then
                cword_=$j
            fi
            if (($i < ${#COMP_WORDS[@]} - 1)); then
                ((i++))
            else
                # Done.
                return
            fi
        done
        words_[$j]=${words_[j]}${COMP_WORDS[i]}
        if [ $i = $COMP_CWORD ]; then
            cword_=$j
        fi
    done
}
