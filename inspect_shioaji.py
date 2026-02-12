import shioaji as sj
import inspect

api = sj.Shioaji(simulation=True)
print("API attributes:")
for name in dir(api):
    if not name.startswith("_"):
        print(name)

print("-" * 20)
print("api.Contracts attributes:")
try:
    for name in dir(api.Contracts):
        if not name.startswith("_"):
            print(name)
except:
    pass
