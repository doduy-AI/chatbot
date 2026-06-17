import secrets
import time
def ramdum():
    otp = f"{secrets.randbelow(1000000):06d}"
    return otp

if __name__ == "__main__":
    start_time = time.time()
    print(ramdum())
    print( time.time() - start_time)

