def delete_from_train_where_in_test(newtrain, oldtest):
    trainset = set(newtrain)
    testset = set(oldtest)
    a = trainset.difference(testset)
    return list(a)

def delete(new_train_path, old_test_path):
    with open(new_train_path) as f:
        train = [s.strip() for s in f.readlines()]
    with open(old_test_path) as f:
        test = [s.strip() for s in f.readlines()]
    new_new_train = delete_from_train_where_in_test(train, test)
    with open(new_train_path, 'w') as f:
        for x in new_new_train:
            f.write(x + "\n")

# l1 = ["abc", "def ght", "def"]
# l2 = ["ght", "def"]
# print(delete_from_train_where_in_test(l1, l2))
delete('train3.')