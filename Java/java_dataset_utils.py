import re
import sqlite3
import traceback
from Java.java_database import db_path

def extract_cleaned_first_sentence(javadoc):
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
        start_1_sentence += 1  # don't need '*'
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

    javadoc = remove_asterisks(javadoc)
    javadoc = remove_stuff_in_brackets(javadoc, '(', ')')
    javadoc = remove_stuff_in_brackets(javadoc, '[', ']')
    javadoc = remove_stuff_in_brackets(javadoc, '{', '}')
    javadoc = remove_stuff_in_brackets(javadoc, '<', '>')
    javadoc = re.sub(r'\s+', ' ', javadoc)
    javadoc = javadoc.strip()
    return javadoc


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
        traceback.print_exc()
    return output


def overwrite_bad_encoded_comments():
    database = sqlite3.connect(db_path)
    database.text_factory = bytes
    cursor = database.cursor()
    cursor.execute('''SELECT id, comment FROM Method''')
    methods = cursor.fetchall()
    for method in methods:
        try:
            method[1].decode('utf-8')
        except UnicodeDecodeError:
            cursor.execute('''UPDATE Method SET comment = 'OVERRIDE' WHERE id = ?''',
                           (method[0],))
            database.commit()
    database.commit()

def overwrite_bad_encoded_calls():
    database = sqlite3.connect(db_path)
    database.text_factory = bytes
    cursor = database.cursor()
    cursor.execute('''SELECT id, calls FROM Method''')
    methods = cursor.fetchall()
    for method in methods:
        try:
            method[1].decode('utf-8')
        except UnicodeDecodeError:
            cursor.execute('''UPDATE Method SET calls = 'OVERRIDE' WHERE id = ?''',
                           (method[0],))
            database.commit()
    database.commit()


if __name__ == "__main__":
    # overwrite_bad_encoded_comments()
    overwrite_bad_encoded_calls()
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
