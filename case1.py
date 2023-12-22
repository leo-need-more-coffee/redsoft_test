h1, m1 = map(int, input().split(':'))
h2, m2 = map(int, input().split(':'))

t = h1*60 + m1
p = h2*60 + m2

if t < p:
    print(f"Опаздывает на {p-t} минут")
if t == p:
    print(f"Вовремя.")
if t > p:
    print(f"Спешит на {t-p} минут")
