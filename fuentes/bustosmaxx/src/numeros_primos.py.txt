from sympy import isprime

# Definir rango
lower = 500003
upper = 799983

# Lista para guardar los primeros 5 primos
primos = []

# Iterar sobre el rango
for n in range(lower + 1, upper):
    if isprime(n):
        primos.append(n)
        if len(primos) == 5:  # detener cuando tengamos 5
            break

print("Cinco números primos en el rango son:", primos)
