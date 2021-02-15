my_dict = {
    'name': 'alvian',
    'star': '5',
    'comments': 'good app!'
    }

check = [{
    'name': 'alvian',
    'star': '5',
    'comments': 'good app!'
}]

def check_dict():
    if my_dict not in check:
        print("it's new")
    else:
        print('dict exist')

check_dict()

