from app.utils.parsing import parse_money_to_float

test_values = ['$1.8 m', '$3.4 m', '60', '1.1', '1.4', '$500k', '$100', '60%']
for val in test_values:
    result = parse_money_to_float(val)
    print(f'{val:<10} -> {result}')