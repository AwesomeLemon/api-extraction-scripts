import re


def extract_cleaned_first_sentence(javadoc):
    javadoc = javadoc.decode("utf-8")
    sentence = first_sentence_from_javadoc(javadoc)
    sentence = clean_javadoc_sentence(sentence)
    if len(sentence) > 0 and sentence[0] == '@':
        return ''
    return sentence


def first_sentence_from_javadoc(javadoc):
    start_1_sentence = javadoc.find('*')
    if start_1_sentence == -1:
        start_1_sentence = 0
    else:
        start_1_sentence += 1 # don't need '*'
    end_1_sentence = javadoc.find('.', start_1_sentence)
    if end_1_sentence == -1:
        end_1_sentence = javadoc.find('\n', start_1_sentence)
        if end_1_sentence == -1:
            end_1_sentence = javadoc.find('*', start_1_sentence)
            if end_1_sentence == -1:
                end_1_sentence = start_1_sentence
    first_sentence = javadoc[start_1_sentence:end_1_sentence]
    return first_sentence


def clean_javadoc_sentence(javadoc):
    def remove_asterisks(javadoc):
        return re.sub('\r?\n( )*\*', '', javadoc)

    def remove_stuff_in_brackets(input, lbracket, rbracket):
        output = ''
        lstack = []
        try:
            for i, c in enumerate(input):
                if c == lbracket:
                    lstack.append(i)
                    continue
                if c == rbracket:
                    if len(lstack) > 0:
                        l_ind = lstack.pop()
                        output += output[l_ind:i]
                        continue
                if len(lstack) == 0:
                    output += c
        except IndexError as e:
            a = e
        return output

    javadoc = remove_asterisks(javadoc)
    javadoc = remove_stuff_in_brackets(javadoc, '(', ')')
    javadoc = remove_stuff_in_brackets(javadoc, '[', ']')
    javadoc = remove_stuff_in_brackets(javadoc, '{', '}')
    javadoc = remove_stuff_in_brackets(javadoc, '<', '>')
    javadoc = re.sub(r'\s+', ' ', javadoc)
    javadoc = javadoc.strip()
    return javadoc


if __name__ == "__main__":
    # brack_test = 'smth ((abc) def) other (ghi) another'
    # print(remove_stuff_in_brackets(brack_test, '(', ')'))
    test = '''
    
         * Set the animated values for this object to this set of ints
         * If there is only one value, it is assumed to be the end value of an animation,
         * and an initial value will be derived, if possible, by calling a getter function
         * on the object. Also, if any value is null, the value will be filled in when the animation
         * starts in the same way. This mechanism of automatically getting null values only works
         * if the PropertyValuesHolder object is used in conjunction
         * {@link ObjectAnimator}, and with a getter function
         * derived automatically from <code>propertyName</code>, since otherwise PropertyValuesHolder has
         * no way of determining what the value should be.
         *
         * @param values One or more values that the animation will animate between.
    
        '''
    test2 = '''
                *       De-activate content observer
                *
         '''
    test3 = '''
     * @param payload
     * @return
     '''
    test4 = ''' {@inheritDoc} '''
    test5 = ''' Called when the activity is first created.  Establishes the UI.  Reads state information saved by previous runs. '''
    print(first_sentence_from_javadoc(test5))
